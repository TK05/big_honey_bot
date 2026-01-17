import re
import requests
from parsel import Selector

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_env
from big_honey_bot.threads.static.headlines import gt_placeholders as gtp


def replace_nbs(text):
    # Attempt replacing non breaking spaces (NBS) with an emptry string to hopefully help with
    # google cal to reddit thread formatting oddities
    text = text.replace('\xa0', '')
    return text


def get_flair_uuid_from_event_type(event_type):
    flair_map = {
        "pre": get_env('FLAIR_PRE'),
        "game": get_env('FLAIR_GAME'),
        "post": get_env('FLAIR_POST'),
        "off": get_env('FLAIR_OFF')
    }

    return flair_map.get(event_type)


def lineup_injury_odds(team_name):
    """Scrapes for lineups, injuries and odds.

    :param team_name: Team name to search for
    :type team_name: str
    :returns Lineups, injuries and odds for both teams
    :rtype: list[list[lineups], list[injuries], list[odds]]
    """

    lineup_status = ["Projected", "Projected"]
    team_lineups = [[], []]
    team_injuries = [[], []]
    betting_data = ['N/A', 'N/A', 'N/A']

    response = requests.get("https://www.rotowire.com/basketball/nba-lineups.php", headers=setup['rotowire_headers'])
    response.raise_for_status()

    selector = Selector(text=response.text)
    all_games = selector.xpath('.//div[@class="lineup is-nba"]')

    # Find game box that contains correct game
    game_idx = None

    for i, game in enumerate(all_games):
        away_team = game.xpath('.//a[contains(@class, "lineup__mteam is-visit")]/text()').get().strip()
        home_team = game.xpath('.//a[contains(@class, "lineup__mteam is-home")]/text()').get().strip()

        if home_team == team_name or away_team == team_name:
            game_idx = i

    if game_idx is None:    # Return out of function if game not found
        return lineup_status, team_lineups, team_injuries, betting_data

    game = all_games[game_idx]

    for i, side in enumerate(["is-visit", "is-home"]):
        lineup_list = game.xpath(f'.//ul[contains(@class, "lineup__list {side}")]')
        players = lineup_list.xpath('.//li[contains(@class, "lineup__player")]')

        # First 5 are starters
        for player in players[:5]:
            pos = player.xpath('.//div[@class="lineup__pos"]/text()').get()
            name = player.xpath('.//a[1]/text()').get()
            des = player.xpath('.//span[@class="lineup__inj"]/text()').get()

            if des:
                name = f"{name} - *{des}*"

            team_lineups[i].append((pos, name))

        # Remaining are those with injuries listed
        for injury in players[5:]:
            name = injury.xpath('.//a[1]/text()').get()
            des = injury.xpath('.//span[@class="lineup__inj"]/text()').get()

            # Do not append when des='OFS' (out for season)
            if name and des and des != 'OFS':
                team_injuries[i].append((name, des))

        status = lineup_list.xpath('.//li[contains(@class, "lineup__status")]/text()').getall()[-1]
        # This will be unstripped string, ie: "Possible Lineup\r\n", we just need first word cleaned
        lineup_status[i] = status.split(' ')[0].strip()

    # TODO: consider storing & showing opening line and then updating current line to closing
    ml = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[1]/span[4]/text()').get()
    spread = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[2]/span[4]/text()').get()
    ou = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[3]/span[4]/text()').get()
    ou = ou.strip(' Pts')

    betting_data = [ml, spread, ou]

    return lineup_status, team_lineups, team_injuries, betting_data


def create_templatized_headline(event_type, home_away, opponent, in_playoffs):
    
    f_map = {
        "pre": "GDT",
        "game": "GAME THREAD",
        "post": "POST GAME THREAD",
        "home": "vs.",
        "away": "@"
    }

    ret_str = f"{f_map[event_type]}: "
    
    if event_type == "post":
        ret_str += f"{setup['team']} {f_map[home_away]} {opponent}"
    else:
        if in_playoffs:
            ret_str += f"{gtp['playoff_series']} - {gtp['playoff_teams']} | {gtp['date_and_time']}"
        else:
            ret_str += f"{setup['team']} {gtp['our_record']} {f_map[home_away]} {opponent} {gtp['opp_record']} | {gtp['date_and_time']}"

    return ret_str


def parse_game_clock(gc_str):
    # format as of 10/23/2025: 	"PT10M20.00S"
    matches = re.findall(r'(\d+)M(\d+)\.(\d+)S', gc_str)[0]
    minutes = int(matches[0])
    seconds = int(matches[1])
    sub_sec = int(matches[2])
    
    return [minutes, seconds, sub_sec]
