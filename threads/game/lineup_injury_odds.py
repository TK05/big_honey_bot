# 3/2/2019 - v1.0
# TK

import requests

LINEUP_INJ_URL = "https://www.lineups.com/nba/lineups"


def line_inj_odds(teams):
    """Scrapes for lineups, injuries and odds.

    Arguments: teams -> list of two teams (will search based on away team but order not important)
    Return: team_lineups -> nested list of lineups with name, position and stats, [away, home]
            team_injuries -> nested list of injuries with name and status, [away, home]
            betting_data -> nested list of moneyline, spread, over/under, implied totals data [away, home]
    """

    team_lineups = [[], []]
    team_injuries = [[], []]
    betting_data = [[], []]

    game_data = requests.get("https://api.lineups.com/nba/fetch/lineups/gateway").json()
    game_data = game_data['data']

    # Find correct key for current game
    game_idx = None

    for i, game in enumerate(game_data):
        if teams[0].lower() in game['home_route'] or teams[0].lower() in game['away_route']:
            game_idx = i

    if not game_idx:    # Return out of function if game not found
        return team_lineups, team_injuries, betting_data

    # Find all injuries for both home and away teams
    injury_idx = ['away_injuries', 'home_injuries']

    for i, team in enumerate(injury_idx):
        for player in game_data[game_idx][team]:
            team_injuries[i].append((player['name'], player['designation']))

    # Find all players for both home and away teams
    player_idx = ['away_players', 'home_players']

    for i, team in enumerate(player_idx):
        for player in game_data[game_idx][team]:
            team_lineups[i].append((player['first_dot_last'], player['position'], player['assists'],
                                    player['rebounds'], player['points']))

    # Find all betting odds for home and away teams
    bets_idx = ['away_bets', 'home_bets']

    for i, team in enumerate(bets_idx):
        # Add '+' to moneyline and spread
        moneyline = game_data[game_idx][team]['moneyline']
        moneyline = f"+{moneyline}" if '-' not in str(moneyline) else moneyline
        spread = game_data[game_idx][team]['spread']
        spread = f"+{spread}" if '-' not in str(spread) else spread

        betting_data[i] = [
            moneyline, f"{spread} ({game_data[game_idx][team]['spread_moneyline']})",
            game_data[game_idx][team]['total'],
            f"{game_data[game_idx][team]['over_under']} ({game_data[game_idx][team]['over_under_moneyline']})"]

    # Makes more sense to flip the implied totals imo
    betting_data[0][-2], betting_data[1][-2] = betting_data[1][-2], betting_data[0][-2]

    return team_lineups, team_injuries, betting_data
