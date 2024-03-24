import os
import time
import logging

import requests

from config import setup


SEASON = setup['season']

logger = logging.getLogger(f"{os.path.basename(__file__)}")


def status_check(nba_id, only_final):
    """Continually check the status of a game given a nba.com game ID.

    Continually requests a new version of the gamedetail json to determine the status
    of an ongoing game. Waits a determined amount of time depending on time remaining
    to avoid requests.

    Arguments: nba_id -> nba.com game ID
               only_final -> boolean, True meaning only game_status == 3 is an
               acceptable end condition.
    Return: Returns None for the purpose of pausing any subsequent functions until
    the game is complete.
    """

    game_ongoing = True
    final_version = False

    while game_ongoing:

        r = requests.get(f"http://data.nba.com/data/v2015/json/mobile_teams"
                         f"/nba/{SEASON}/scores/gamedetail/{nba_id}_gamedetail.json")
        game_data = r.json()

        game_status = game_data['g']['st']
        current_quarter = game_data['g']['p']

        # Attempt to handle NoneType game clocks gracefully
        if game_data['g']['cl']:
            min_left = int(game_data['g']['cl'].split(':')[0])
            sec_left = float(game_data['g']['cl'].split(':')[1])
        else:
            logger.info(f"{os.path.basename(__file__)}: Game clock is NoneType, sleeping 60 seconds...")
            time.sleep(60)
            continue

        logger.info(f"{os.path.basename(__file__)}: Status: {game_status}, Quarter: {current_quarter}, Time: {game_data['g']['cl']}")

        # Check for game start
        if game_status == 1:
            time.sleep(60*30)
            continue

        # Check if game in either 1st/2nd/3rd quarter
        if current_quarter <= 3:
            time.sleep(60*10)
            continue

        # Check if game in 4th quarter or OT
        elif current_quarter >= 4:
            if min_left > 5:
                time.sleep(60*5)
                continue
            elif min_left >= 1:
                time.sleep(30)
                continue
            elif min_left == 0:

                """Ideally, checking for game_status == 3 is ideal but sometimes stats.nba is slow
                to finalize a game and will stagnate at Q4 0:00 for minutes. Solution to initially post
                when game is over (and scores are different to not misinterpret overtime) and then update
                the thread when game_status == 3"""
                away_score = game_data['g']['vls']['s']
                home_score = game_data['g']['hls']['s']

                # Game is over and boxscore is finalized
                if game_status == 3:
                    logger.info(f"{os.path.basename(__file__)}: Game Over, finalized version")
                    final_version = True
                    game_ongoing = False
                # Game is over but boxscore not finalized
                elif abs(away_score - home_score) != 0 and sec_left == 0 and not only_final:
                    logger.info(f"{os.path.basename(__file__)}: Game Over, initial version")
                    final_version = False
                    game_ongoing = False
                else:
                    time.sleep(10)
                    continue
            else:
                logger.warning(f"{os.path.basename(__file__)}: Something unexpected happened during game_status_check...")  # TODO: Handle an error properly
                time.sleep(30)
                continue

    return final_version
