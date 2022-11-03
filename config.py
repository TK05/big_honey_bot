from dotenv import load_dotenv


load_dotenv()

DEBUG = False

setup = {
    'season': 2022,  # Start year. EX: 18-19 season = 2018
    'team': 'Nuggets',
    'location': 'Denver',
    'timezone': 'US/Mountain',
    'timezone_short': 'MT',
    'pre_game_post_time': "08:00",  # time used for pre game post time
    # 'espn_url': 'http://www.espn.com/nba/team/schedule/_/name/den/seasontype/1',  # Preseason
    'espn_url': 'http://www.espn.com/nba/team/schedule/_/name/den/seasontype/2',  # Regular Season
    # 'espn_url': 'http://www.espn.com/nba/team/schedule/_/name/den/seasontype/3',  # Postseason
    'nba_url': 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json',  # nba.com json schedule
    'user_agent': 'BigHoneyBot_by_TK05',
    'nba_api_headers': {
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://stats.nba.com/'
    },
    'flairs': {     # Subreddit specific link_flair IDs
        'pre': '51a03fc6-3e0c-11e9-8856-0e97475b835e',
        'game': 'b94d2b1e-7af0-11e8-9106-0ecef3c85830',
        'post': '3f0b88d4-3e0c-11e9-afb3-0e6687893da2',
        'off': '8bf4420e-4a77-11e9-a63c-0e1a3ad07cf6'
    }
    # 'flairs': {   # Test flairs
    #     'pre': '701ba516-3e0d-11e9-80e7-0e07faed2e96',
    #     'game': '7fa2da68-3e0d-11e9-9571-0e5fef20b374',
    #     'post': '7962e238-3e0d-11e9-92dc-0edef102ea7a',
    #     'off': 'e5a3688e-bde7-11ec-86e2-86c0ad65b04f'
    # }
}
