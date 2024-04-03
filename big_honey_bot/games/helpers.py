import logging

import requests
from parsel import Selector

from big_honey_bot.helpers import (
    change_timezone,
    get_timestamp_from_datetime,
    get_str_from_datetime,
    get_datetime_from_str,
    get_datetime
)
from big_honey_bot.config.main import setup, OUTPUT_PATH
from big_honey_bot.config.helpers import get_env, get_pname_fname_str


logger = logging.getLogger(get_pname_fname_str(__file__))


def request_schedule(url, headers, file_name):

    # import from file_name if it exists, otherwise scrape page using requests
    if get_env('DEBUG'):
        try:
            OUTPUT_PATH.mkdir()
        except FileExistsError:
            pass

        try:
            with open(OUTPUT_PATH.joinpath(file_name), 'r') as file:
                response = file.read().replace('\n', '')
        except FileNotFoundError:
            response = requests.get(url).text

        f = open(OUTPUT_PATH.joinpath(file_name), 'w', encoding='utf-8')
        f.write(response)

    else:
        response = requests.get(url, headers=headers).text

    return response


def espn_convert_date_time(date_in, time_in):
    """ convert raw time and date
        outputs utc timestamp for key and a local time string for easier reading
    """

    espn_timezone = 'US/Eastern' # ESPN uses Eastern timezone
    scrape_year = setup['season']

    # TODO: fix this table so it's not needed
    # ESPN doesn't include year, so lookup table to return month (as int) and correct year
    mo_yr_table = {'Oct': (10, scrape_year),
                   'Nov': (11, scrape_year),
                   'Dec': (12, scrape_year),
                   'Jan': (1, (scrape_year + 1)),
                   'Feb': (2, (scrape_year + 1)),
                   'Mar': (3, (scrape_year + 1)),
                   'Apr': (4, (scrape_year + 1)),
                   'May': (5, (scrape_year + 1)),
                   'Jun': (6, (scrape_year + 1)),
                   'Jul': (7, (scrape_year + 1)),
                   'Aug': (8, (scrape_year + 1)),
                   'Sep': (9, (scrape_year + 1))}

    date_in = date_in.split()  # ex:['Wed,', 'Jan', '30]
    month, year = mo_yr_table[date_in[1]]
    day = int((date_in[-1]))

    # transform hour into gmt (24 hour)
    time_in = time_in.split(":")
    if 'PM' in time_in[-1] and time_in[0] == '12':
        hour = 12
        minute = (int(time_in[-1].strip(' PM')))
    elif 'PM' in time_in[-1]:
        hour = int(time_in[0]) + 12
        minute = (int(time_in[-1].strip(' PM')))
    else:
        hour = int(time_in[0])
        minute = (int(time_in[-1].strip(' AM')))

    site_dt = get_datetime(dt=[year, month, day, hour, minute], add_tz=True, tz=espn_timezone)  # create datetime obj from what's scraped
    loc_dt = change_timezone(dt=site_dt, tz=setup['timezone']) # convert to setup timezone
    loc_str = get_str_from_datetime(dt=loc_dt, fmt='%D %I:%M %p')

    return get_timestamp_from_datetime(dt=site_dt), loc_str


def get_espn_schedule_dict():
    """ Load html from file or request html with requests.
        Traverse XML down to individual games.
        Scrape each game, append to a game dict with game's UTC timestamp as key.
        Return as dict.
        Grabbed from ESPN:
            utc, game date, espn id
    """

    response = request_schedule(setup['espn_url'], setup['espn_headers'], 'espn_schedule.html')

    response_selector = Selector(text=response)
    games_raw = response_selector.xpath('.//tbody[@class="Table__TBODY"]//tr')  # each item is an entire game's details
    espn_data = dict()

    for game in games_raw:
        """ Creates the following:
                UTC timestamp as game key (string) and initializes an empty dict.
                espn_data[utc_key]['game_start']    = mo/day/yr hr:mn am/pm
                espn_data[utc_key]['espn_id']       = espn ID for game
        """

        date_raw = game.xpath('./td[@class="Table__TD"][1]/span/text()').get()
        time_raw = game.xpath('./td[@class="Table__TD"][3]/span[1]/a/text()').get()

        if not time_raw or time_raw == 'TBD':    # ignore game if it has already been played or TBD
            continue

        utc_key, date = espn_convert_date_time(date_raw, time_raw)
        
        # store utc_key as string since they're converted to strings in JSON already
        utc_key = str(utc_key)
        espn_data[utc_key] = dict()
        espn_data[utc_key]['game_start'] = date

        game_id_url = game.xpath('./td[@class="Table__TD"][3]/span[1]/a/@href').get()
        game_id_raw = game_id_url.split('/')
        game_id = game_id_raw[-2]

        # Ensure game_is an integer to catch potential future URI schema changes
        try:
            int(game_id)
        except ValueError:
            raise ValueError(f"ESPN game_id unexpectedly not an int: {game_id}")
        
        espn_data[utc_key]['espn_id'] = game_id

    return espn_data


def get_nba_com_schedule_dict():
    """ Grab NBA.com's scheduled JSON
        Walk through JSON of games, append to a game dict with game's UTC timestamp as key.
        Return as dict.
        Grabbed from nba.com:
            utc, nba id, home/away, arena, city, opponent (as team name), tv, radio
    """

    nbacom_data = dict()

    all_games = requests.get(setup['nba_url']).json()

    for date in all_games['leagueSchedule']['gameDates']:
        for game in date['games']:

            # early exit for finished games
            if game['gameStatus'] != 1:
                continue

            home_team = game['homeTeam']['teamName']
            away_team = game['awayTeam']['teamName']

            # early exit for non team match
            if setup['team'] not in [home_team, away_team]:
                continue

            utc_dt = get_datetime_from_str(dt_str=game['gameDateTimeUTC'], fmt='%Y-%m-%dT%H:%M:%SZ', add_tz=True, tz='UTC')
            # store utc_key as string since they're converted to strings in JSON already
            utc_key = str(get_timestamp_from_datetime(dt=utc_dt))
            nbacom_data[utc_key] = dict()
            nbacom_data[utc_key]['nba_id'] = game['gameId']
            nbacom_data[utc_key]['home_away'] = 'home' if setup['team'] == home_team else 'away'
            nbacom_data[utc_key]['arena'] = game['arenaName']
            nbacom_data[utc_key]['city'] = game['arenaCity']
            nbacom_data[utc_key]['opponent'] = home_team if not setup['team'] == home_team else away_team

            # format TV broadcasters
            nat_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['nationalTvBroadcasters']]
            home_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['homeTvBroadcasters']]
            away_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['awayTvBroadcasters']]
            tv_ordered = [nat_tv, home_tv, away_tv] if setup['team'] == home_team else [nat_tv, away_tv, home_tv]
            nbacom_data[utc_key]['tv'] = ", ".join([i for s in tv_ordered for i in s])

            # format radio broadcasters
            nat_rad = [i['broadcasterDisplay'] for i in game['broadcasters']['nationalRadioBroadcasters']]
            home_rad = [i['broadcasterDisplay'] for i in game['broadcasters']['homeRadioBroadcasters']]
            away_rad = [i['broadcasterDisplay'] for i in game['broadcasters']['awayRadioBroadcasters']]
            rad_ordered = [nat_rad, home_rad] if setup['team'] == home_team else [nat_rad, away_rad]
            nbacom_data[utc_key]['radio'] = ", ".join([i for s in rad_ordered for i in s])

    return nbacom_data


def get_next_game():
    espn_data = get_espn_schedule_dict()
    nba_com_data = get_nba_com_schedule_dict()

    next_espn_ts = None
    next_nba_com_ts = None
    now_ts = get_timestamp_from_datetime()

    for game_ts in espn_data.keys():
        if int(game_ts) > now_ts:
            next_espn_ts = game_ts
            break
    
    for game_ts in nba_com_data.keys():
        if int(game_ts) > now_ts:
            next_nba_com_ts = game_ts
            break
    
    if next_espn_ts == next_nba_com_ts:
        next_game_dict = {**espn_data[next_espn_ts], **nba_com_data[next_nba_com_ts]}
        next_game_dict['start_ts'] = next_espn_ts
        
        return next_game_dict
    
    elif (not next_espn_ts or not next_nba_com_ts) or (next_espn_ts != next_nba_com_ts):
        logger.error(f"No next game or source discrepency - ESPN: {next_espn_ts}, NBA: {next_nba_com_ts}")

        raise ValueError(f"Next game not found or discrepency between sources.")
    
    else:
        logger.error(f"Unknown error when getting next game: {next_espn_ts}, NBA: {next_nba_com_ts}")
        
        raise ValueError(f"Unknown error when getting next game.")
    

if __name__ == "__main__":
    get_espn_schedule_dict()
