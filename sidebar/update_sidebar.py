import os
import re
import requests
import praw
from parsel import Selector

from config import setup, options


TARGET_SUB = os.environ['TARGET_SUB']
USER_AGENT = setup['user_agent']
YEAR = setup['season']
TEAM = setup['team']
PLAYOFF_WATCH = options['playoff_watch']

USERNAME = os.environ['PRAW_USERNAME']
PASSWORD = os.environ['PRAW_PASSWORD']
CLIENT_ID = os.environ['PRAW_CLIENT_ID']
CLIENT_SECRET = os.environ['PRAW_CLIENT_SECRET']


reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)


def update_record():
    """Grabs team's record and standing from nba.com."""

    # TODO: This URL could be invalid in the future.
    id_response = requests.get(f"https://data.nba.net/prod/v2/{setup['season']}/teams.json").json()

    # Get Team_ID needed to lookup records
    for team in id_response['league']['standard']:
        if team['nickname'] == TEAM:
            team_focus_id = team['teamId']
            team_conf = team['confName']
            break

    rec_response = requests.get("https://data.nba.net/prod//v1/current/standings_conference.json").json()

    for conf in rec_response['league']['standard']['conference'].values():
        for seed, team in enumerate(conf):
            if team_focus_id == team['teamId']:
                tf_wins = team['win']
                tf_loss = team['loss']
                conf_data = conf
                team_seed = seed

    return conf_data, team_seed, f"Record: {tf_wins} - {tf_loss} | #{team_seed + 1} in the {team_conf}"


def update_tripdub():
    """Grabs Jokic's current triple-double count and dunk count."""

    # TODO: URL's could change in the future.
    header = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}
    dunk_res = requests.get('https://www.basketball-reference.com/players/j/jokicni01.html', headers=header).text

    dunk_obj = re.findall(r'(?<=fg2_dunk\" >)[\d]*', dunk_res)
    dunks = dunk_obj[-8] # TODO: Has to be changed every season

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


def update_playoff(conf_data, team_seed):
    """Calculates magic numbers for both playoffs and current seed."""

    tf_wins = int(conf_data[team_seed]['win'])
    ninth_losses = int(conf_data[8]['loss'])
    po_code_1 = conf_data[team_seed]['clinchedPlayoffsCode']    # 'P' for playoffs?
    po_code_2 = conf_data[team_seed]['clinchedPlayoffsCode']    # 'x' for playoffs?
    play_magic_num = 83 - tf_wins - ninth_losses

    if po_code_1 != '':
        playoffs_clinched = True
    else:
        playoffs_clinched = False

    if playoffs_clinched:
        play_sub = f'Playoffs **CLINCHED!**'
        for seed in range(7, team_seed, -1):
            seed_losses = int(conf_data[seed]['loss'])
            seed_magic_num = 83 - tf_wins - seed_losses
            seed_sub = f'#{seed} Seed Magic #: {seed_magic_num}^*'
            if seed_magic_num > 0:
                break
            else:
                seed_sub = f'#{team_seed + 1} Seed: CLINCHED!'
    else:
        play_sub = f'Playoff Magic #: {play_magic_num}^*'
        seed_sub = ''

    return play_sub, seed_sub


def update_sidebar():
    """Updates sidebar for both new and old reddit."""

    # Old Reddit
    old_reddit_sidebar = reddit.subreddit(TARGET_SUB).wiki['config/sidebar'].content_md

    record_regex = re.compile(r"((?<=\(/record\))[^\n]*)")
    tripdub_regex = re.compile(r"((?<=\(/tripdub\))[^\n]*)")
    play_regex = re.compile(r"((?<=\(/playoff1\))[^\n]*)")
    seed_regex = re.compile(r"((?<=\(/playoff2\))[^\n]*)")

    conf_data, team_seed, record_sub = update_record()
    old_reddit_sidebar = record_regex.sub(record_sub, old_reddit_sidebar)

    if PLAYOFF_WATCH:
        play_sub, seed_sub = update_playoff(conf_data, team_seed)
        old_reddit_sidebar = play_regex.sub(play_sub, old_reddit_sidebar)
        old_reddit_sidebar = seed_regex.sub(seed_sub, old_reddit_sidebar)

    old_reddit_sidebar = tripdub_regex.sub(update_tripdub(), old_reddit_sidebar)

    sidebar = reddit.subreddit(TARGET_SUB).wiki['config/sidebar']
    sidebar.edit(old_reddit_sidebar)
    print("Old-Reddit sidebar updated")

    # New Reddit
    widgets = reddit.subreddit(TARGET_SUB).widgets
    new_reddit_sidebar = None
    for widget in widgets.sidebar:
        if isinstance(widget, praw.models.TextArea):
            new_reddit_sidebar = widget
            break

    new_text = new_reddit_sidebar.text

    new_text = record_regex.sub(record_sub, new_text)

    if PLAYOFF_WATCH:
        play_sub, seed_sub = update_playoff(conf_data, team_seed)
        new_text = play_regex.sub(play_sub, new_text)
        new_text = seed_regex.sub(seed_sub, new_text)

    new_text = tripdub_regex.sub(update_tripdub(), new_text)

    style = {'backgroundColor': '#FFFFFF', 'headerColor': '#014980'}
    new_reddit_sidebar.mod.update(shortName='Season Info', text=new_text, styles=style)
    print("New-Reddit sidebar updated")
