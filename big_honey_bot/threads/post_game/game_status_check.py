import time
import logging

import requests

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_pname_fname_str


SEASON = setup['season']

logger = logging.getLogger(get_pname_fname_str(__file__))


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
    final_checked_once = False

    while game_ongoing:

        r = requests.get(f"http://data.nba.com/data/v2015/json/mobile_teams"
                         f"/nba/{SEASON}/scores/gamedetail/{nba_id}_gamedetail.json")
        game_data = r.json()

        game_status = game_data['g']['st']
        current_quarter = game_data['g']['p']
        away_score = game_data['g']['vls']['s']
        home_score = game_data['g']['hls']['s']

        # Sleep further when game clock is not initialized
        if game_data['g']['cl']:
            min_left = int(game_data['g']['cl'].split(':')[0])
            sec_left = float(game_data['g']['cl'].split(':')[1])
        else:
            logger.info(f"Game clock is not yet initialized, sleeping 15 minutes...")
            time.sleep(60*15)
            continue

        # Set game over conditions
        over_by_status = True if game_status == 3 else False
        over_by_time = True if current_quarter >= 4 and min_left == 0 and sec_left == 0 else False
        # Ensure game isn't tied (could go to overtime)
        over_by_score = True if abs(away_score - home_score) != 0 else False
        over_by_time_and_score = over_by_time and over_by_score

        logger.info(f"Status: {game_status}, Quarter: {current_quarter}, Time: {game_data['g']['cl']}, Score: {away_score}-{home_score}")

        # Sleep while game hasn't started
        if game_status == 1:
            time.sleep(60*15)
            continue

        # Sleep when game is in quarters (1..3)
        if current_quarter <= 3:
            time.sleep(60*15)
            continue

        # Shorter sleeps when Q4 or OT but still time left
        elif current_quarter >= 4:
            if min_left > 5:
                time.sleep(60*5)
                continue
            elif min_left >= 1:
                time.sleep(30)
                continue
            elif min_left == 0 and sec_left != 0:
                time.sleep(10)
                continue
        
        # Game is possibly over, start checking game over conditions
        if over_by_status or over_by_time_and_score:
                
            # We catch the first instance of a game being over with final_checked_once and then sleep.
            # Checking for game_status==3 is ideal but sometimes stats.nba is slow to finalize a game
            # and will stagnate at Q4 0:00 for minutes. This is possibly because game_status==3 is reserved
            # for when the boxscore is somewhat finalized. In that case, we want to set game_ongoing=False
            # if the game is over by both time and margin to allow an initial post game thread to be created.
            # We can then check again with only_final=True which requires game_status==3 to make a final
            # update to the post game thread with the updated "finalized" box score data.

            # First instance that the game is "over"; sleep 10 and check again
            if not final_checked_once:
                final_checked_once = True
                time.sleep(10)
                continue

            # Game is over and boxscore is finalized
            elif over_by_status:
                logger.info(f"Game Over, finalized version")
                final_version = True
                game_ongoing = False
            
            # Game is over but boxscore not finalized
            elif over_by_time_and_score and not only_final:
                logger.info(f"Game Over, initial version")
                final_version = False
                game_ongoing = False

            # Game is over but not over_by_status and only_final==True (waiting for final update)
            else:
                time.sleep(10)
                continue
        
        else:
            # TODO: Handle errors
            logger.warning(f"Something unexpected happened during game_status_check...")  
            time.sleep(30)
            continue

    return final_version
