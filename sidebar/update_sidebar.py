import os
import re
from distutils.util import strtobool
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import requests
import praw
from parsel import Selector
from nba_api.stats.endpoints import leaguestandingsv3
from nba_api.stats.static import teams

from config import setup


USER_AGENT = setup['user_agent']
YEAR = setup['season']
TEAM = setup['team']
TIMEZONE = setup['timezone']

UPDATE_SIDEBAR = bool(strtobool(os.getenv('UPDATE_SIDEBAR', "False")))
PLAYOFF_WATCH = bool(strtobool(os.getenv('PLAYOFF_WATCH', "False")))
IS_OFFSEASON = bool(strtobool(os.getenv('IS_OFFSEASON', "False")))

TARGET_SUB = os.environ['TARGET_SUB']
USERNAME = os.environ['PRAW_USERNAME']
PASSWORD = os.environ['PRAW_PASSWORD']
CLIENT_ID = os.environ['PRAW_CLIENT_ID']
CLIENT_SECRET = os.environ['PRAW_CLIENT_SECRET']


reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)


def get_standings():
    raw_standings = leaguestandingsv3.LeagueStandingsV3(headers=setup['nba_api_headers']).get_dict()
    headers = raw_standings['resultSets'][0]['headers']
    standings = {'West': {}, 'East': {}}

    for i, h in enumerate(headers):
        if h == 'Conference':
            conf_idx = i
        elif h == 'PlayoffRank':
            rank_idx = i

    for stats in raw_standings['resultSets'][0]['rowSet']:
        conf = stats[conf_idx]
        rank = stats[rank_idx]
        standings[conf][rank] = {}

        for i, stat in enumerate(stats):
            standings[conf][rank][headers[i]] = stat

    return standings


def get_team_conf_and_rank(standings, tf_id=None):

    if not tf_id:
        tf_id = teams.find_teams_by_nickname(TEAM)[0]['id']

    for conf in standings.keys():
        for rank, team in standings[conf].items():
            if team['TeamID'] == tf_id:
                tf_rank = rank
                tf_conf = conf
                break

    return tf_conf, tf_rank


def update_record(standings):

    tf_conf, tf_rank = get_team_conf_and_rank(standings)
    tf_rec = standings[tf_conf][tf_rank]['Record']

    return f"Record: {tf_rec} | #{tf_rank} in the {tf_conf}"


def update_tripdub():
    """Grabs Jokic's current triple-double count and dunk count."""

    # TODO: URL's could change in the future.
    header = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}
    dunk_res = requests.get('https://www.basketball-reference.com/players/j/jokicni01.html', headers=header).text

    dunk_obj = re.findall(r'(?<=fg2_dunk\" >)[\d]*', dunk_res)
    dunks = dunk_obj[-7]    # TODO: Has to be changed every season

    td_res = requests.get(f"https://www.basketball-reference.com/play-index/pgl_finder.cgi?request=1&"
                          f"match=career&year_min={setup['season'] + 1}&year_max={setup['season'] + 1}&is_playoffs=N&"
                          f"age_min=0&age_max=99&season_start=1&season_end=-1&pos_is_g=Y&pos_is_gf=Y&pos_is_f=Y&"
                          f"pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&player_id=jokicni01&"
                          f"is_trp_dbl=Y&order_by=pts",
                          headers=header)

    td_res = Selector(text=td_res.text)
    trip_dub = td_res.xpath('//td[@data-stat="counter"]/a/text()').get()

    if trip_dub == 'None':
        trip_dub = 0

    return f"Nikola Jokić TD-to-Dunk Ratio: {trip_dub}:{dunks}"


# TODO: Validate for 2022-23
def update_playoff(standings):
    """Calculates magic numbers for playoffs, play-ins and current seed."""

    tf_conf, tf_rank = get_team_conf_and_rank(standings)
    tf_wins = standings[tf_conf][tf_rank]['WINS']
    tf_po_code = standings[tf_conf][tf_rank]['ClinchIndicator'] # TODO: Check these when they become active

    # Get data for 7th and 11th seed in same conference
    seventh_losses = standings[tf_conf][7]['LOSSES']
    eleventh_losses = standings[tf_conf][11]['LOSSES']

    play_in_magic_num = 83 - tf_wins - eleventh_losses
    playoff_magic_num = 83 - tf_wins - seventh_losses

    def generate_subs(p_type):
        p_sub = f'{p_type} **CLINCHED!**'
        s_sub = ''

        for seed in range(5 if p_type == 'Playoffs' else 10, tf_rank, -1):
            seed_losses = standings[tf_conf][seed]['LOSSES']
            seed_magic_num = 83 - tf_wins - seed_losses
            s_sub = f'#{seed - 1} Seed Magic #: {seed_magic_num}'
            if seed_magic_num > 0:
                break
            else:
                s_sub = f'#{tf_rank} Seed: CLINCHED!'

        return p_sub, s_sub

    p2_sub = ''
    p3_sub = ''

    if tf_po_code in ['P', 'C'] or playoff_magic_num < 0:
        p1_sub, p2_sub = generate_subs('Playoffs')
    elif play_in_magic_num < 0:
        p1_sub, p3_sub = generate_subs('Play-ins', tf_rank)
        p2_sub = f'Playoff Magic #: {playoff_magic_num}'
    else:
        p1_sub = f'Play-in Magic #: {play_in_magic_num}'

    return p1_sub, p2_sub, p3_sub


def update_munder(standings):

    tf_conf, tf_rank = get_team_conf_and_rank(standings)
    tf_gp = standings[tf_conf][tf_rank]['WINS'] + standings[tf_conf][tf_rank]['LOSSES']
    opp_score_100 = standings[tf_conf][tf_rank]['OppScore100PTS']
    games_over_100 = sum([int(i) for i in opp_score_100.split('-')])

    return f"Munders: {tf_gp - games_over_100}"


def update_reign():
    start_date = date(2023, 6, 13)
    date_now = datetime.now(tz=ZoneInfo(TIMEZONE)).date()
    reign_days = (date_now - start_date + timedelta(days=1)).days

    return f"Reign Day #{reign_days}"


def update_sidebar():
    """Updates sidebar for both new and old reddit."""

    if not UPDATE_SIDEBAR:
        return

    print(f"{os.path.basename(__file__)}: Updating sidebar @ {datetime.now().strftime('%H:%M')}")

    standings = get_standings()

    # Old Reddit
    old_reddit_sidebar = reddit.subreddit(TARGET_SUB).wiki['config/sidebar'].content_md

    record_regex = re.compile(r"((?<=\(/record\))[^\n]*)")
    reign_regex = re.compile(r"((?<=\(/reign\))[^\n]*)")
    tripdub_regex = re.compile(r"((?<=\(/tripdub\))[^\n]*)")
    munder_regex = re.compile(r"((?<=\(/munder\))[^\n]*)")
    p1_regex = re.compile(r"((?<=\(/playoff1\))[^\n]*)")
    p2_regex = re.compile(r"((?<=\(/playoff2\))[^\n]*)")
    p3_regex = re.compile(r"((?<=\(/playoff3\))[^\n]*)")

    if not IS_OFFSEASON:
        record_sub = update_record(standings)
        old_reddit_sidebar = record_regex.sub(record_sub, old_reddit_sidebar)

    old_reddit_sidebar = reign_regex.sub(update_reign(), old_reddit_sidebar)
    # old_reddit_sidebar = tripdub_regex.sub(update_tripdub(), old_reddit_sidebar)
    # old_reddit_sidebar = munder_regex.sub(update_munder(standings), old_reddit_sidebar)

    if PLAYOFF_WATCH:
        p1_sub, p2_sub, p3_sub = update_playoff(standings)
        old_reddit_sidebar = p1_regex.sub(p1_sub, old_reddit_sidebar)
        old_reddit_sidebar = p2_regex.sub(p2_sub, old_reddit_sidebar)
        old_reddit_sidebar = p3_regex.sub(p3_sub, old_reddit_sidebar)

    sidebar = reddit.subreddit(TARGET_SUB).wiki['config/sidebar']
    sidebar.edit(old_reddit_sidebar)
    print(f"{os.path.basename(__file__)}: Old-Reddit sidebar updated")

    # New Reddit
    widgets = reddit.subreddit(TARGET_SUB).widgets
    new_reddit_sidebar = None
    for widget in widgets.sidebar:
        if isinstance(widget, praw.models.TextArea):
            new_reddit_sidebar = widget
            break

    new_text = new_reddit_sidebar.text

    if not IS_OFFSEASON:
        new_text = record_regex.sub(record_sub, new_text)

    new_text = reign_regex.sub(update_reign(), new_text)
    # new_text = tripdub_regex.sub(update_tripdub(), new_text)
    # new_text = munder_regex.sub(update_munder(standings), new_text)

    if PLAYOFF_WATCH:
        p1_sub, p2_sub, p3_sub = update_playoff(standings)
        new_text = p1_regex.sub(p1_sub, new_text)
        new_text = p2_regex.sub(p2_sub, new_text)
        new_text = p3_regex.sub(p3_sub, new_text)

    style = {'backgroundColor': '#FFFFFF', 'headerColor': '#014980'}
    new_reddit_sidebar.mod.update(shortName='Season Info', text=new_text, styles=style)
    print(f"{os.path.basename(__file__)}: New-Reddit sidebar updated")
