DEBUG = False

setup = {
    'season': 2021,  # Start year. EX: 18-19 season = 2018
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
    'flairs': {     # Subreddit specific link_flair IDs
        'pre': '51a03fc6-3e0c-11e9-8856-0e97475b835e',
        'game': 'b94d2b1e-7af0-11e8-9106-0ecef3c85830',
        'post': '3f0b88d4-3e0c-11e9-afb3-0e6687893da2'
    }
    # 'flairs': {   # Test flairs
    #     'pre': '701ba516-3e0d-11e9-80e7-0e07faed2e96',
    #     'game': '7fa2da68-3e0d-11e9-9571-0e5fef20b374',
    #     'post': '7962e238-3e0d-11e9-92dc-0edef102ea7a'
    # }
}
