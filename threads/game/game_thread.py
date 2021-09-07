from datetime import datetime
import os
import re
import pytz
import requests
from parsel import Selector

from config import setup
from bots.thread_handler_bot import new_thread
from threads.static.templates import Game
from data.static.data import team_lookup
from threads.game.lineup_injury_odds import line_inj_odds


TEAM = setup['team']
LOCATION = setup['location']
TZ_STR = setup['timezone_short']


def home_away_fix(home_away):
    if home_away == 'home':
        return 'vs.'
    else:
        return '@'


def game_headline(event_data):
    """Generate a thread title based on event and team data."""

    # TODO: This URL could change in the future.
    id_response = requests.get("https://data.nba.net/prod/v2/2018/teams.json").json()

    team_focus_id = opp_team_id = tf_wins = tf_loss = opp_wins = opp_loss = 0

    # Get and set nba.com Team_ID's needed to lookup records
    for team in id_response['league']['standard']:
        if team['nickname'] == TEAM and team['isNBAFranchise']:
            team_focus_id = team['teamId']
        if team['nickname'] == event_data['Opponent'] and team['isNBAFranchise']:
            opp_team_id = team['teamId']

    rec_response = requests.get("https://data.nba.net/prod//v1/current/standings_conference.json").json()

    for conf in rec_response['league']['standard']['conference'].values():
        for team in conf:
            if team_focus_id == team['teamId']:
                tf_wins = team['win']
                tf_loss = team['loss']
            elif opp_team_id == team['teamId']:
                opp_wins = team['win']
                opp_loss = team['loss']

    return Game.headline(event_data['Type'], TEAM, tf_wins, tf_loss, home_away_fix(event_data['home_away']),
                         event_data['Opponent'], opp_wins, opp_loss, event_data['Date_Str'], event_data['Time'])


def playoff_headline(event_data, playoff_data):
    """Generate a thread title for playoff game threads."""

    team_wins, opp_wins = playoff_data[2]

    if event_data['Type'] == 'pre':
        headline = "GAME DAY THREAD: "
    else:
        headline = "GAME THREAD: "

    headline += f"ROUND {playoff_data[3]}, GAME {playoff_data[1]} - " \
                f"{TEAM} {home_away_fix(event_data['home_away'])} {event_data['Opponent']}"

    if team_wins > opp_wins:
        headline += f" | {TEAM} Lead {team_wins}-{opp_wins}"
    elif team_wins < opp_wins:
        headline += f" | {TEAM} Trail {team_wins}-{opp_wins}"
    else:
        headline += f" | Series Tied {team_wins}-{opp_wins}"

    headline += f" | {event_data['Date_Str']} - {event_data['Time']}"

    return headline


def game_body(utc_key, event_data):
    """Generate body of game thread depending on event data.

    Will scrape for probable lineups, injuries and game betting odds.
    """

    # Format a few times based on popular time zones in the subreddit
    time_fmt = '%#I:%M %p %Z'
    dt_obj = datetime.fromtimestamp(int(utc_key))
    est_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Eastern')), format(time_fmt))} - Kitchener"
    mst_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Mountain')), format(time_fmt))} - Denver"
    pst_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Pacific')), format(time_fmt))} - Seattle"
    cest_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('Europe/Belgrade')), format(time_fmt))} - Sombor"
    aedt_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('Australia/Sydney')), format(time_fmt))} - Sydney"

    # Set proper home/away team abbreviation for sub icons
    if event_data['Location'] == 'home':
        home_abv = team_lookup[TEAM][1]
        away_abv = team_lookup[event_data['Opponent']][1]
    else:
        away_abv = team_lookup[TEAM][1]
        home_abv = team_lookup[event_data['Opponent']][1]

    # subreddit links using team lookup dict
    top_sub = team_lookup[event_data['Opponent']][0]
    bot_sub = team_lookup[TEAM][0]

    # Top "General Information" table
    gen_info_table = Game.gen_info_table(
        [est_time, mst_time, pst_time, cest_time, aedt_time],
        event_data['TV'], event_data['Radio'],
        [event_data['NBA_Box'], event_data['NBA_Shot']],
        [event_data['ESPN_Box'], event_data['ESPN_Gamecast']],
        event_data['Arena'], event_data['City'],
        [top_sub, bot_sub])

    # Call to lineup script to return lineups, injuries, betting odds
    team_lineups, team_injuries, betting_odds = line_inj_odds(TEAM)

    lineup_header = Game.lineup_head_and_fmt(away_abv, home_abv)
    lineup_rows = Game.lineup_rows(team_lineups)

    injuries_header = Game.injuries_head_and_fmt(away_abv, home_abv)
    injuries_rows = Game.injuries_rows(team_injuries)

    betting_header = Game.betting_head_and_fmt()
    betting_rows = Game.betting_rows(betting_odds)

    # Scrape referees to get referees for the game
    ref_res = requests.get("https://official.nba.com/referee-assignments/").text
    ref_res = Selector(text=ref_res)
    ref_all_games = ref_res.xpath('//div[@class="nba-refs-content"]/table/tbody/tr')
    referees = "*Referees: "

    for i, game in enumerate(ref_all_games):
        curr_row = game.xpath('./td[1]/text()')

        if LOCATION in curr_row.get():
            regex = re.compile('[^a-zA-Z\s]')
            ref_list = []

            for n in range(2, 5):
                try:
                    ref_list.append(regex.sub('', game.xpath(f"./td[{n}]/a/text()").get()))
                except TypeError:
                    try:
                        ref_list.append(regex.sub('', game.xpath(f"./td[{n}]/text()").get()))
                    except TypeError:
                        ref_list.append("Unknown")

            referees += ", ".join(str(i).strip() for i in ref_list)

    referees += '*'

    return (f"{gen_info_table}\n\n&nbsp;\n\n"
            f"{lineup_header}{lineup_rows}\n\n&nbsp;\n\n"
            f"{injuries_header}{injuries_rows}\n\n&nbsp;\n\n"
            f"{betting_header}{betting_rows}\n\n&nbsp;\n\n"
            f"{referees}\n")


def pre_game_body(event_data):
    """Generates a very basic pre-game thread with room for additions."""

    tz_url = f"http://www.thetimezoneconverter.com/?t={event_data['Time']}&tz=Denver&"

    pg_body = Game.pre_game_body(event_data['Time'], TZ_STR, tz_url, event_data['Arena'],
                                 event_data['City'], event_data['TV'], event_data['Radio'])

    return pg_body


def game_thread_handler(event_data, playoff_data):
    """Callable function to generate and post a game thread."""

    print(f"Generating thread data for {event_data['Date_Str']} --- {event_data['Type']}")
    if playoff_data[0]:
        headline = playoff_headline(event_data, playoff_data)
    else:
        headline = game_headline(event_data)

    if event_data['Type'] == 'pre':
        body = pre_game_body(event_data)
    else:
        body = game_body(event_data['UTC'], event_data)

    thread_obj = new_thread(headline, body, event_data['Type'])
    print(f"Thread posted to r/{os.environ['TARGET_SUB']}")

    return headline, body, thread_obj
