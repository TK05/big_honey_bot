# Static lookup dicts in here to not clutter other scripts.


class Data(object):

    @staticmethod
    def team_lookup():
        team_lookup = {
            "Mavericks": ["mavericks", 'DAL'],
            "Nuggets": ["denvernuggets", 'DEN'],
            "Warriors": ["warriors", 'GSW'],
            "Rockets": ["rockets", 'HOU'],
            "Clippers": ["laclippers", 'LAC'],
            "Lakers": ["lakers", 'LAL'],
            "Grizzlies": ["memphisgrizzlies", 'MEM'],
            "Timberwolves": ["timberwolves", 'MIN'],
            "Pelicans": ["nolapelicans", 'NOP'],
            "Thunder": ["thunder", 'OKC'],
            "Suns": ["suns", 'PHX'],
            "Trail Blazers": ["ripcity", 'POR'],
            "Kings": ["kings", 'SAC'],
            "Spurs": ["nbaspurs", 'SAS'],
            "Jazz": ["utahjazz", 'UTA'],
            "Hawks": ["atlantahawks", 'ATL'],
            "Celtics": ["bostonceltics", 'BOS'],
            "Nets": ["gonets", 'BKN'],
            "Hornets": ["charlottehornets", 'CHA'],
            "Bulls": ["chicagobulls", 'CHI'],
            "Cavaliers": ["clevelandcavs", 'CLE'],
            "Pistons": ["detroitpistons", 'DET'],
            "Pacers": ["pacers", 'IND'],
            "Heat": ["heat", 'MIA'],
            "Bucks": ["mkebucks", 'MIL'],
            "Knicks": ["nyknicks", 'NYK'],
            "Magic": ["orlandomagic", 'ORL'],
            "Sixers": ["sixers", 'PHI'],
            "Raptors": ["torontoraptors", 'TOR'],
            "Wizards": ["washingtonwizards", 'WAS']
        }

        return team_lookup
