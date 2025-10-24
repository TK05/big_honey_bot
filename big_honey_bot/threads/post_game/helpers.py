key_paths = {
    "game": "game",
    "away_team": "game.awayTeam",                                  
    "away_tricode": "game.awayTeam.teamTricode",
    "away_stats": "game.awayTeam.statistics",
    "away_players": "game.awayTeam.players",
    "away_periods": "game.awayTeam.periods",
    "home_team": "game.homeTeam",                                  
    "home_tricode": "game.homeTeam.teamTricode",
    "home_stats": "game.homeTeam.statistics",
    "home_players": "game.homeTeam.players",
    "home_periods": "game.homeTeam.periods",
    "officials": "game.officials",
    "game_periods": "game.periods",
}


def get_value(d, path):
    keys = path.split(".")
    for k in keys:
        d = d[k]
    return d
