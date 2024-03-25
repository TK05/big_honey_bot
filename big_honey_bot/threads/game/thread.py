import os
import re
import logging

import requests
from parsel import Selector
from nba_api.stats.endpoints import leaguestandingsv3
from nba_api.stats.static import teams

from big_honey_bot.helpers import get_datetime_from_str, description_tags
from big_honey_bot.config.main import setup
from big_honey_bot.threads.main import new_thread
from big_honey_bot.threads.static.headlines import gt_placeholders
from big_honey_bot.threads.static.templates import Game
from big_honey_bot.threads.static.lookups import team_lookup
from big_honey_bot.threads.helpers import lineup_injury_odds


TEAM = setup['team']
LOCATION = setup['location']

logger = logging.getLogger(f"{os.path.basename(__file__)}")


def format_date_and_time(game_start):

    dt = get_datetime_from_str(dt_str=game_start, fmt="%m/%d/%y %I:%M %p")

    try:
        date = dt.strftime('%b %-d, %Y')
        time = dt.strftime('%-I:%M %p')
    except ValueError:
        date = dt.strftime('%b %#d, %Y')
        time = dt.strftime('%#I:%M %p')

    return date, time


def generate_title(event):
    """Generates thread title based on event and team data. Generates and formats team records, date and time
    to replace placeholder tags from event title.

    :param event: Event to generate thread title for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    team_focus_id = teams.find_teams_by_nickname(TEAM)[0]['id']
    opp_team_id = teams.find_teams_by_nickname(event.meta['opponent'])[0]['id']

    standings = leaguestandingsv3.LeagueStandingsV3(headers=setup['nba_api_headers']).get_dict()

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

    event.summary = event.summary.replace(gt_placeholders['our_record'], f'({tf_rec})')
    event.summary = event.summary.replace(gt_placeholders['opp_record'], f'({opp_rec})')
    event.summary = event.summary.replace(gt_placeholders['date_and_time'], f'{date_str} - {time_str}')


def playoff_headline(event, playoff_data):
    """Generates a playoff thread title based on event and team data. Generates and formats team records, date and time
    to replace placeholder tags from event title.

    :param event: Event to generate thread title for
    :type event: gcsa.event.Event
    :param playoff_data: List of playoff data
    :type event: tuple
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    def home_away_fix(home_away):
        if home_away == 'home':
            return 'vs.'
        else:
            return '@'

    team_wins, opp_wins = playoff_data[2]
    series_str = f"R{playoff_data[0]}G{playoff_data[1]}"
    teams_str = f"{TEAM} {home_away_fix(event.meta['home_away'])} {event.meta['opponent']}"

    if playoff_data[1] != 1:
        if team_wins > opp_wins:
            teams_str += f" | {TEAM} Lead {team_wins}-{opp_wins}"
        elif team_wins < opp_wins:
            teams_str += f" | {TEAM} Trail {team_wins}-{opp_wins}"
        else:
            teams_str += f" | Series Tied {team_wins}-{opp_wins}"

    date_str, time_str = format_date_and_time(event.meta['game_start'])

    event.summary = event.summary.replace(gt_placeholders['playoff_series'], series_str)
    event.summary = event.summary.replace(gt_placeholders['playoff_teams'], teams_str)
    event.summary = event.summary.replace(gt_placeholders['date_and_time'], f'{date_str} - {time_str}')


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
    team_lineups, team_injuries, betting_odds = lineup_injury_odds(TEAM)

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
    :param playoff_data: List of playoff data if in playoffs;
    :type playoff_data: list or NoneType
    :returns: None
    :rtype: NoneType
    """

    if playoff_data:
        playoff_headline(event, playoff_data)
    else:
        generate_title(event)

    if event.meta['event_type'] in ['pre', 'game']:
        generate_game_body(event)

    logger.info(f"Created headline: {event.summary}")
    new_thread(event)
