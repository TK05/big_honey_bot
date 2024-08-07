from pathlib import Path


OUTPUT_PATH = Path.cwd().joinpath("out")

if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()

ENV_RELOAD_INTERVAL_SEC = 60
LOG_FILENAME = "big_honey_bot.log"

setup = {
    'season': 2024,  # Start year. EX: 18-19 season = 2018
    'team': 'Nuggets',
    'location': 'Denver',
    'timezone': 'US/Mountain',
    'timezone_short': 'MT',
    'pre_game_post_hour': "8",  # hour (24) to post pre game thread
    # ESPN uses 3 different pages for full season schedule; 1=preseason, 2=regular season, 3=postseason
    'espn_url_template': 'http://www.espn.com/nba/team/schedule/_/name/den/seasontype/{}',
    'espn_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'If-Modified-Since': 'Sat, 30 Sep 2023 21:05:15 GMT',
    },
    'nba_url': 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json',  # nba.com json schedule
    'nba_game_detail_template': 'http://data.nba.com/data/v2015/json/mobile_teams/nba/{}/scores/gamedetail/{}_gamedetail.json',
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
    }
}
