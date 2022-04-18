import requests
from parsel import Selector


def line_inj_odds(team_name):
    """Scrapes for lineups, injuries and odds.

    :param team_name: Team name to search for
    :type team_name: str
    :returns Lineups, injuries and odds for both teams
    :rtype: list[list[lineups], list[injuries], list[odds]]
    """

    team_lineups = [[], []]
    team_injuries = [[], []]
    betting_data = ['N/A', 'N/A', 'N/A']

    response = Selector(text=requests.get("https://www.rotowire.com/basketball/nba-lineups.php").text)
    all_games = response.xpath('.//div[@class="lineup is-nba"]')

    # Find game box that contains correct game
    game_idx = None

    for i, game in enumerate(all_games):
        away = game.xpath('./div[2]/div[2]/a[1]/text()').get().strip()
        home = game.xpath('./div[2]/div[2]/a[2]/text()').get().strip()

        if home == team_name or away == team_name:
            game_idx = i

    if game_idx is None:    # Return out of function if game not found
        return team_lineups, team_injuries, betting_data

    game = all_games[game_idx]

    for side in [0, 1]:
        lineups = game.xpath(f'./div[2]/div[3]/ul[{side + 1}]')
        lineup_len = game.xpath(f'./div[2]/div[3]/ul[{side + 1}]/li')

        for player in range(2, 7):
            pos = lineups.xpath(f'./li[{player}]/div[1]/text()').get()
            name = lineups.xpath(f'./li[{player}]/a[1]/text()').get()
            des = lineups.xpath(f'./li[{player}]/span[1]/text()').get()

            if des:
                name = f'{name} - *{des}*'
            team_lineups[side].append((pos, name))

        for injury in range(8, len(lineup_len) + 1):
            name = lineups.xpath(f'./li[{injury}]/a[1]/text()').get()
            des = lineups.xpath(f'./li[{injury}]/span[1]/text()').get()
            team_injuries[side].append((name, des))

    ml = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[1]/span[1]/text()').get()
    spread = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[2]/span[1]/text()').get()
    ou = game.xpath(f'.//div[@class="lineup__odds is-row"]/div[3]/span[1]/text()').get()
    ou = ou.strip(' Pts')

    betting_data = [ml, spread, ou]

    return team_lineups, team_injuries, betting_data
