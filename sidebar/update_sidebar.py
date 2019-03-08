import os
import re
import requests
import praw
from nba_api.stats.endpoints import playerdashboardbyyearoveryear


TARGET_SUB = os.environ['TARGET_SUB']
USER_AGENT = os.environ['USER_AGENT']
YEAR = os.environ['SEASON']
TEAM = os.environ['TEAM']
PLAYOFF_WATCH = os.environ['PLAYOFF_WATCH']

username = os.environ['praw_username']
password = os.environ['praw_password']
client_id = os.environ['praw_client_id']
client_secret = os.environ['praw_client_secret']


reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=USER_AGENT)


def update_record():
    print("grab record")
    id_response = requests.get("https://data.nba.net/prod/v2/2018/teams.json").json()

    # Get and set nba.com Team_ID's needed to lookup records
    for team in id_response['league']['standard']:
        if team['nickname'] == TEAM:
            team_focus_id = team['teamId']
            break

    rec_response = requests.get("https://data.nba.net/prod//v1/current/standings_conference.json").json()
    print("record grabbed")
    for conf in rec_response['league']['standard']['conference'].values():
        for seed, team in enumerate(conf):
            if team_focus_id == team['teamId']:
                tf_wins = team['win']
                tf_loss = team['loss']
                conf_data = conf
                team_seed = seed

    return conf_data, team_seed, f"Record: {tf_wins} - {tf_loss}"


def update_tripdub():
    print("grab bballref")
    header = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}
    dunk_res = requests.get('https://www.basketball-reference.com/players/j/jokicni01.html', headers=header).text
    print("bballref grabbed")
    dunk_obj = re.findall(r'(?<=fg2_dunk\" >)[\d]*', dunk_res)
    dunks = dunk_obj[-3]

    season = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id='203999')
    season_dict = season.get_normalized_dict()
    trip_dub = season_dict['ByYearPlayerDashboard'][0]['TD3']

    return f"Nikola Jokić TD-to-Dunk Ratio: {trip_dub}:{dunks}"


def update_playoff(conf_data, team_seed):
    tf_wins = int(conf_data[team_seed]['win'])
    ninth_losses = int(conf_data[8]['loss'])
    play_magic_num = 83 - tf_wins - ninth_losses

    next_seed_losses = int(conf_data[int(team_seed) + 1]['loss'])
    seed_magic_num = 83 - tf_wins - next_seed_losses

    play_sub = f'Playoff Magic #: {play_magic_num}^*'
    seed_sub = f'#{int(team_seed) + 1} Seed Magic #: {seed_magic_num}^*'

    return play_sub, seed_sub


def update_sidebar():
    sidebar_md = reddit.subreddit(TARGET_SUB).wiki['config/sidebar'].content_md
    print('sidebar grabbed')

    record_regex = re.compile(r"((?<=\(/record\))[^\n]*)")
    tripdub_regex = re.compile(r"((?<=\(/tripdub\))[^\n]*)")
    play_regex = re.compile(r"((?<=\(/playoff1\))[^\n]*)")
    seed_regex = re.compile(r"((?<=\(/playoff2\))[^\n]*)")

    conf_data, team_seed, record_sub = update_record()
    print('update record ran')
    sidebar_md = record_regex.sub(record_sub, sidebar_md)
    print('record regex done')

    if PLAYOFF_WATCH:
        play_sub, seed_sub = update_playoff(conf_data, team_seed)
        sidebar_md = play_regex.sub(play_sub, sidebar_md)
        sidebar_md = seed_regex.sub(seed_sub, sidebar_md)
        print('playoff regex done')

    sidebar_md = tripdub_regex.sub(update_tripdub(), sidebar_md)
    print('tripdub regex done')

    sidebar = reddit.subreddit(TARGET_SUB).wiki['config/sidebar']
    sidebar.edit(sidebar_md)
    print("Old-Reddit sidebar updated")

    widgets = reddit.subreddit(os.environ['TARGET_SUB']).widgets
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
