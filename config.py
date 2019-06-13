DEBUG = False

setup = {
    'season': 2018,  # Start year. EX: 18-19 season = 2018
    'team': 'Nuggets',
    'timezone': 'US/Mountain',
    'timezone_string': 'MT',
    'user_agent': 'BigHoneyBot_by_TK05',
    'flairs': {     # Subreddit specific link_flair IDs
        'pre': '51a03fc6-3e0c-11e9-8856-0e97475b835e',
        'game': 'b94d2b1e-7af0-11e8-9106-0ecef3c85830',
        'post': '3f0b88d4-3e0c-11e9-afb3-0e6687893da2'
    }
}

options = {
    'update_sidebar': True,
    'thread_stats': True,
    'in_playoffs': False,
    'playoff_watch': False
}

gists = {
    'pre': {
        'filename': 'pre_game.md',
        'id': '29116608ab19125f97f40fea9c6582a9'
    },
    'game': {
        'filename': 'game_thread.md',
        'id': 'd0fbf3fce1e517c5b567e87d5b7b2542'
    },
    'post': {
        'filename': 'post_game.md',
        'id': '1a32b36af1a2c6ed3eb16f08ffa51580'
    },
    'schedule': {
        'filename': 'schedule.json',
        'id': 'ca4c2fa43d1da9986d2c66556774f44b'
    }
}
