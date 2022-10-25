from datetime import datetime
import os
import re
import requests
from parsel import Selector
from nba_api.stats.endpoints import leaguestandingsv3
from nba_api.stats.static import teams

from config import setup
from bots.thread_handler_bot import new_thread
from threads.static.templates import Game
from data.static.data import team_lookup
from threads.game.lineup_injury_odds import line_inj_odds
from tools.toolkit import description_tags


TEAM = setup['team']
LOCATION = setup['location']


def generate_title(event):
    """Generates thread title based on event and team data. Generates and formats team records, date and time
    to replace placeholder tags from event title.

    :param event: Event to generate thread title for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    def format_date_and_time(game_start):
        try:
            date = datetime.strptime(game_start, "%m/%d/%y %I:%M %p").strftime('%b %-d, %Y')
            time = datetime.strptime(game_start, "%m/%d/%y %I:%M %p").strftime('%-I:%M %p')
        except ValueError:
            date = datetime.strptime(game_start, "%m/%d/%y %I:%M %p").strftime('%b %#d, %Y')
            time = datetime.strptime(game_start, "%m/%d/%y %I:%M %p").strftime('%#I:%M %p')

        return date, time

    team_focus_id = teams.find_teams_by_nickname(TEAM)[0]['id']
    opp_team_id = teams.find_teams_by_nickname(event.meta['opponent'])[0]['id']

    standings = leaguestandingsv3.LeagueStandingsV3().get_dict()

    # find index for 'Record' header
    for i, h in enumerate(standings['resultSets'][0]['headers']):
        if h == 'Record':
            rec_idx = i
        elif h == 'TeamID':
            id_idx = i

    # iterate over results for record of both teams
    for team in standings['resultSets'][0]['rowSet']:
        if team[id_idx] == team_focus_id:
            tf_rec = team[rec_idx]
        elif team[id_idx] == opp_team_id:
            opp_rec = team[rec_idx]

    date_str, time_str = format_date_and_time(event.meta['game_start'])

    event.summary = event.summary.replace(description_tags['our_record'], f'({tf_rec})')
    event.summary = event.summary.replace(description_tags['opp_record'], f'({opp_rec})')
    event.summary = event.summary.replace(description_tags['date_and_time'], f'{date_str} - {time_str}')


def playoff_headline(event_data, playoff_data):
    """Generate a thread title for playoff game threads."""

    def home_away_fix(home_away):
        if home_away == 'home':
            return 'vs.'
        else:
            return '@'

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


def generate_game_body(event):
    """Generates game thread body based on event, lineup, injury, odds and referee data. Replaces placeholder tags with
    this generated data.

    :param event: Event to generate thread body for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    # Set proper home/away team abbreviation for sub icons
    if event.meta['home_away'] == 'home':
        home_abv = team_lookup[TEAM][1]
        away_abv = team_lookup[event.meta['opponent']][1]
    else:
        away_abv = team_lookup[TEAM][1]
        home_abv = team_lookup[event.meta['opponent']][1]

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

    if referees == "*Referees: *":
        referees = ''

    event.body = event.body.replace(description_tags['starters'], f"{lineup_header}{lineup_rows}")
    event.body = event.body.replace(description_tags['injuries'], f"{injuries_header}{injuries_rows}")
    event.body = event.body.replace(description_tags['odds'], f"{betting_header}{betting_rows}")
    event.body = event.body.replace(description_tags['referees'], f"{referees}\n")


def game_thread_handler(event, playoff_data):
    """Generates thread title and body for event. Posts generated thread.

    :param event: Event to generate thread for
    :type event: gcsa.event.Event
    :param playoff_data: TODO
    :type playoff_data: TODO
    :returns: None
    :rtype: NoneType
    """

    if playoff_data[0]:
        # TODO: Update for playoffs
        playoff_headline(event, playoff_data)
    else:
        generate_title(event)

    if event.meta['event_type'] in ['pre', 'game']:
        generate_game_body(event)

    print(f"{os.path.basename(__file__)}: Created headline: {event.summary}")
    new_thread(event)
