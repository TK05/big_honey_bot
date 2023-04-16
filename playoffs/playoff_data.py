import requests

from config import setup


TEAM = setup['team']
SEASON = setup['season']

nba_api_playoff_url = f'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/{SEASON}/scores/00_playoff_bracket.json'


def get_series_status():
    """
    Gets playoff series status given TEAM configured
    :returns: (current round (int), game number (int), series record [list])
    :rtype: tuple
    """

    response = requests.get(nba_api_playoff_url).json()

    for each_round in response['pb']['r']:
        current_round = each_round['id']
        for conference in each_round['co']:
            for series in conference['ser']:
                if TEAM == series['tn1']:
                    playoff_record = [series['t1w'], series['t2w']]
                elif TEAM == series['tn2']:
                    playoff_record = [series['t2w'], series['t1w']]
                else:
                    continue

                try:
                    if 4 in playoff_record:
                        continue
                    game_number = sum(playoff_record) + 1
                    return current_round, game_number, playoff_record
                except NameError:
                    continue

    raise Exception("COULD NOT DETERMINE PLAYOFF SERIES STATUS")
