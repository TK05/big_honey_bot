import os
from datetime import datetime
import pprint
import json
import requests
from parsel import Selector
import pytz

from config import DEBUG, setup  # When DEBUG; save json & html


TIMEZONE = setup['timezone']
SCRAPE_YEAR = setup['season']


def espn_schedule_scrape():
    """ Load html from file or request html with requests.
        Traverse XML down to individual games.
        Scrape each game, append to a game dict with game's UTC timestamp as key.
        Output to json file.
        Grabbed from ESPN:
            utc, game date, espn gamecast/boxscore/recap urls, espn id
    """

    scrape_type = 'espn_s1'  # TODO: see if this is helps organizing event status

    response = request_schedule(setup['espn_url'], 'espn_schedule.html')

    response_selector = Selector(text=response)
    games_raw = response_selector.xpath('.//tbody[@class="Table__TBODY"]//tr')  # each item is an entire game's details
    espn_data = dict()

    for game in games_raw:
        """ Creates the following:
                UTC timestamp as game key (string) and initializes an empty dict.
                espn_data[utc_key]['Date']          = mo/day/yr hr:mn am/pm
                espn_data[utc_key]['ESPN_Gamecast'] = gamecast url
                espn_data[utc_key]['ESPN_Box']      = boxscore url
                espn_data[utc_key]['ESPN_Recap']    = recap url
                espn_data[utc_key]['ESPN_ID']       = espn ID for game
        """

        date_raw = game.xpath('./td[@class="Table__TD"][1]/span/text()').get()
        time_raw = game.xpath('./td[@class="Table__TD"][3]/span[1]/a/text()').get()

        if not time_raw or time_raw == 'TBD':    # ignore game if it has already been played or TBD
            continue

        utc_key, date = espn_convert_date_time(date_raw, time_raw)

        espn_data[utc_key] = dict()
        espn_data[utc_key]['Date'] = date
        espn_data[utc_key]['Type'] = scrape_type    # TODO: check if this matters

        # grabs and generates espn id and all necessary links
        game_id_url = game.xpath('./td[@class="Table__TD"][3]/span[1]/a/@href').get()
        espn_data[utc_key]['ESPN_Gamecast'] = game_id_url
        espn_data[utc_key]['ESPN_Box'] = game_id_url.replace("game", "boxscore", 1)
        espn_data[utc_key]['ESPN_Recap'] = game_id_url.replace("game", "recap", 1)
        game_id_raw = game_id_url.split('=')
        espn_data[utc_key]['ESPN_ID'] = game_id_raw[-1]

        try:
            os.mkdir('../json_output')
        except FileExistsError:
            pass

        with open(f'../json_output/schedule_scrape_output.json', 'w') as f:
            json.dump(espn_data, f, indent=4)

        if DEBUG:
            pprint.pprint(espn_data)


def nba_com_schedule_scrap():
    """ Load html from file or request html with requests.
        Traverse XML down to individual games.
        Scrape each game, append to a game dict with game's UTC timestamp as key.
        Output to json file.
        Grabbed from nba.com:
            utc, nba id, nba boxscore/shotchart urls...
            location (home/away), arena, city, opponent (as team name), tv, radio
    """

    scrape_type = 'nba_s2'  # TODO: see if this is helps organizing event status

    response = request_schedule(setup['nba_url'], 'nba_schedule.html')

    response_selector = Selector(text=response)
    games_raw = response_selector.xpath('.//li[@data-gamestatus="1"]')  # len(games_raw) would show remaining games

    nbacom_data = dict()
    url_hub = "https://stats.nba.com/game/"

    for game in games_raw:
        """ Creates the following:
                UTC timestamp as game key (string) and initializes an empty dict.
                nbacom_data[utc_key]['NBA_ID']      = nba.com ID for game
                nbacom_data[utc_key]['NBA_Box']     = boxscore url
                nbacom_data[utc_key]['NBA_Shot']    = shotchart url
                nbacom_data[utc_key]['Location']    = home or away
                nbacom_data[utc_key]['Arena']       = arena name
                nbacom_data[utc_key]['City']        = city location of game
                nbacom_data[utc_key]['Opponent']    = opponent's team name
                nbacom_data[utc_key]['TV']          = tv networks
                nbacom_data[utc_key]['Radio']       = radio networks
        """

        # Playoff Fix: If time is TBD, continue
        if game.xpath('./div[2]/div[3]/div[1]/span/text()').get() == 'TBD':
            continue

        # 2019 Fix: NBA.com changed game event utc to 2 hours before
        utc_key = str(int(game.xpath('./@data-eventtime').get()) + 7200)

        nbacom_data[utc_key] = dict()

        nbacom_data[utc_key]['Type'] = scrape_type
        nbacom_data[utc_key]["NBA_ID"] = game.xpath('./@id').get()
        nbacom_data[utc_key]["NBA_Box"] = f"{url_hub}{nbacom_data[utc_key]['NBA_ID']}"
        nbacom_data[utc_key]["NBA_Shot"] = f"{nbacom_data[utc_key]['NBA_Box']}/shotchart"
        nbacom_data[utc_key]["Location"] = (game.xpath('./div[1]/span/text()').get())[0:4]
        nbacom_data[utc_key]["Arena"] = game.xpath('./@data-arena').get()
        nbacom_data[utc_key]["City"] = game.xpath('./div[2]/div[2]/div/span[2]/span/text()').get()
        nbacom_data[utc_key]["Opponent"] = (game.xpath('./div[2]/div[1]/div[1]/img/@alt').get()).title()

        # fix for sixers
        if nbacom_data[utc_key]["Opponent"] == '76Ers':
            nbacom_data[utc_key]["Opponent"] = '76ers'

        # broadcast details, fix for when there's local and national tv
        tv = ""
        if game.xpath('./div[3]/div[1]/div[1]/div[1]/span[1]/span[2]/text()').get():
            tv_nat = game.xpath('./div[3]/div[1]/div[1]/div[1]/span[1]/span[2]/text()').get()
            tv = f"{tv_nat}, "
        tv += game.xpath('./div[3]/div[1]/div[1]/div[1]/span[1]/span[1]/text()').get()
        nbacom_data[utc_key]["TV"] = tv
        # TODO: Check if radio is added to nba.com eventually
        nbacom_data[utc_key]["Radio"] = game.xpath('./div[3]/div[1]/div[1]/div[1]/span[2]/span[1]/text()').get()
        # nbacom_data[utc_key]["Radio"] = "KKSE-FM 92.5"

    if not os.path.exists('../json_output/schedule_scrape_output.json'):
        json_file = {}
    else:
        with open('../json_output/schedule_scrape_output.json', 'r') as f:
            json_file = json.load(f)

    # update json file using utc_key as key
    for utc_key, game_dict in nbacom_data.items():
        for data_key, data in game_dict.items():
            try:
                json_file[utc_key][data_key] = data
            except KeyError:
                # 2020 catch for scrimmage games not on both sites
                pass

    with open('../json_output/schedule_scrape_output.json', 'w') as f:
        json.dump(json_file, f, indent=4)

    if DEBUG:
        pprint.pprint(nbacom_data)


def espn_convert_date_time(date_in, time_in):
    """ convert raw time and date
        outputs utc timestamp (as int) for key and a local time string for easier reading
    """
    espn_timezone = pytz.timezone('US/Eastern')  # ESPN uses Eastern timezone
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

    site_dt = datetime(year, month, day, hour, minute)  # datetime of scraped time
    site_dt = espn_timezone.localize(site_dt)   # properly converted to correct timezone
    loc_str = datetime.strftime(site_dt.astimezone(tz=pytz.timezone(TIMEZONE)), format('%D %I:%M %p'))

    return int(site_dt.timestamp()), loc_str


def request_schedule(url, file_name):

    # import from file_name if it exists, otherwise scrape page using requests
    if DEBUG:
        try:
            os.mkdir('../tmp')
        except FileExistsError:
            pass

        try:
            with open(f'../tmp/{file_name}', 'r') as file:
                response = file.read().replace('\n', '')
        except FileNotFoundError:
            response = requests.get(url).text

        f = open(f'../tmp/{file_name}', 'w', encoding='utf-8')
        f.write(response)

    else:
        response = requests.get(url).text

    return response


# espn should always be ran before nba.com
if __name__ == '__main__':
    espn_schedule_scrape()
    nba_com_schedule_scrap()
