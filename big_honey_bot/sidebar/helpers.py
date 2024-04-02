import re
import logging
import asyncio
from datetime import date, timedelta

import requests
import asyncpraw
from parsel import Selector
from nba_api.stats.endpoints import leaguestandingsv3
from nba_api.stats.static import teams

from big_honey_bot.helpers import get_datetime, get_str_from_datetime
from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.threads.main import get_subreddit


logger = logging.getLogger(get_pname_fname_str(__file__))


YEAR = setup['season']
TEAM = setup['team']

UPDATE_SIDEBAR = get_env('UPDATE_SIDEBAR')
PLAYOFF_WATCH = get_env('PLAYOFF_WATCH')
IS_OFFSEASON = get_env('IS_OFFSEASON')


async def get_standings():
    # TODO: async version of nba_api?
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


async def update_tripdub():
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

    # ClinchedPostSeason; 1 1 if play-in or better clinched, 0 otherwise
    # PlayoffRank; int of current seed
    # ClinchedIndicator; "- ps" if playins secured?, empty string otherwise
    # PlayoffSeeding; ?
    # TODO: Check these when they become active
    tf_po_code = standings[tf_conf][tf_rank]['ClinchIndicator']

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

    if tf_po_code.lower() in ['p', 'c'] or playoff_magic_num < 0:
        p1_sub, p2_sub = generate_subs('Playoffs')
    elif play_in_magic_num < 0:
        p1_sub, p3_sub = generate_subs('Play-ins')
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
    date_now = get_datetime(add_tz=True).date()
    reign_days = (date_now - start_date + timedelta(days=1)).days

    return f"Reign Day #{reign_days}"


async def update_sidebar():
    """Updates sidebar for both new and old reddit."""

    if not get_env('UPDATE_SIDEBAR'):
        return

    logger.info(f"Updating sidebar @ {get_str_from_datetime(fmt='%H:%M')}")

    standings = asyncio.create_task(get_standings())
    subreddit = asyncio.create_task(get_subreddit())
    await standings
    await subreddit

    # Old Reddit
    ors = await subreddit.wiki.get_page('config/sidebar')
    old_reddit_sidebar = ors.content_md

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

    sidebar = await subreddit.wiki['config/sidebar']
    await sidebar.edit(old_reddit_sidebar)
    logger.info(f"Old-Reddit sidebar updated")

    # Get sidebar from new reddit
    widgets = await subreddit.widgets
    new_reddit_sidebar = None
    async for widget in widgets.sidebar():
        if isinstance(widget, asyncpraw.models.TextArea):
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
    await new_reddit_sidebar.mod.update(shortName='Season Info', text=new_text, styles=style)
    logger.info(f"New-Reddit sidebar updated")
