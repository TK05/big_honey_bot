# assumes starting with base game dict
key_paths = {
    "game": "game",
    "away_team": "awayTeam",                                  
    "away_tricode": "awayTeam.teamTricode",
    "away_stats": "awayTeam.statistics",
    "away_players": "awayTeam.players",
    "away_periods": "awayTeam.periods",
    "home_team": "homeTeam",                                  
    "home_tricode": "homeTeam.teamTricode",
    "home_stats": "homeTeam.statistics",
    "home_players": "homeTeam.players",
    "home_periods": "homeTeam.periods",
    "officials": "officials",
    "period": "period",
}


def get_value(d, path):
    keys = path.split(".")
    for k in keys:
        d = d[k]
    return d
