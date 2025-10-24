import time
import logging
import re

import requests

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_pname_fname_str


SEASON = setup['season']
GD_TEMPLATE = setup['nba_game_detail_template']

logger = logging.getLogger(get_pname_fname_str(__file__))

def _parse_game_clock(gc_str):
    # format as of 10/23/2025: 	"PT10M20.00S"
    matches = re.findall(r'(\d+)M(\d+)\.(\d+)S', gc_str)[0]
    minutes = int(matches[0])
    seconds = int(matches[1])
    sub_sec = int(matches[2])
    
    return minutes, seconds, sub_sec


def status_check(nba_id, only_final):
    """Continually check the status of a game given a nba.com game ID.

    Continually requests a new version of the gamedetail json to determine the status
    of an ongoing game. Waits a determined amount of time depending on time remaining
    to avoid requests.

    Arguments: nba_id -> nba.com game ID
               only_final -> boolean, True meaning only game_status == 3 is an
               acceptable end condition.
    Return: final_version -> boolean, true if game_status=3, else false
            game_data -> dict, JSON of game data
    """

    game_ongoing = True
    final_version = False
    final_checked_once = False

    while game_ongoing:

        game_data = requests.get(GD_TEMPLATE.format(nba_id)).json()

        game_status = game_data['game']['gameStatus']
        game_status_text = game_data['game']['gameStatusText']
        current_quarter = game_data['game']['period']
        away_score = game_data['game']['awayTeam']['score']
        home_score = game_data['game']['homeTeam']['score']
        min_left, sec_left, sub_sec_left = _parse_game_clock(game_data['game']['gameClock'])

        logger.info(f"Status: {game_status}, Quarter: {current_quarter}, Time: {game_status_text}, Score: {away_score}-{home_score}")

        # Sleep while game hasn't started or when game is in quarters (1..3)
        if game_status == 1 or current_quarter <= 3:
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

        # Set game over conditions
        over_by_status = True if game_status == 3 else False
        over_by_status_text = True if game_status_text == 'Final' else False
        over_by_time = True if current_quarter >= 4 and min_left == 0 and sec_left == 0 else False
        margin = abs(away_score - home_score)
        
        # Never return game status if score is tied
        if not margin:
            time.sleep(10)
            continue
        
        # Game is possibly over, start checking game over conditions
        elif over_by_status or (over_by_time and margin):
            # We catch the first instance of a game being over with final_checked_once and then sleep.
            # Checking for game_status==3 is ideal but sometimes stats.nba is slow to finalize a game
            # and will stagnate at Q4 0:00 for minutes. This is possibly because game_status==3 is reserved
            # for when the boxscore is somewhat finalized. In that case, we want to set game_ongoing=False
            # if the game is over by both time and margin to allow an initial post game thread to be created.
            # We can then check again with only_final=True which requires game_status==3 to make a final
            # update to the post game thread with the updated "finalized" box score data.

            # First instance that the game is "over"; sleep 10 and check again
            if not final_checked_once and not only_final:
                final_checked_once = True
                # Sleep longer if close margin
                if margin >= 4:
                    time.sleep(60)
                else:
                    time.sleep(10)
                continue

            # Game is over and boxscore is finalized
            elif over_by_status:
                logger.info(f"Game Over, finalized version")
                final_version = True
                game_ongoing = False
            
            # Game is over but boxscore not finalized
            elif over_by_time and not only_final:
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

    return final_version, game_data

if __name__ == "__main__":
    import sys

    # Existing logger setup
    logger = logging.getLogger(get_pname_fname_str(__file__))

    # Set logger level
    logger.setLevel(logging.DEBUG)  # or INFO depending on how much you want

    # Create handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)  # capture DEBUG and up

    # Create a formatter you like
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add handler to the logger
    logger.addHandler(handler)
    status_check("0022500006", False)
