import requests

from big_honey_bot.config.main import setup


TEAM = setup['team']
SEASON = setup['season']
NBA_URL = setup['nba_playoff_template'].format(SEASON)


def get_series_status():
    """
    Gets playoff series status given TEAM configured
    :returns: (current round (int), game number (int), series record [list])
    :rtype: tuple
    """

    try:
        response = requests.get(NBA_URL, headers=setup['nba_cdn_headers']).json()

        # This is index 0 whereas individual series are index 1
        current_round = response['bracket'].get('currentRound', 0) + 1
        series_record = [0,0]
        
        for series in response['bracket']['playoffBracketSeries']:
            if current_round == series['roundNumber']:
                if series['highSeedName'] == TEAM:
                    series_record = [series['highSeedSeriesWins'], series['lowSeedSeriesWins']]
                    break
                elif series['lowSeedName'] == TEAM:
                    series_record = [series['lowSeedSeriesWins'], series['highSeedSeriesWins']]
                    break

        game_number = sum(series_record) + 1
    except:
        raise Exception("Could not determine playoff series status")

    return current_round, game_number, series_record
