# 3/2/2019 - v1.0
# TK
# TODO: Make sure this works when overtime happens

import os
import time
import requests


SEASON = os.environ['SEASON']


def status_check(nba_id):
    """Continually check the status of a game given a nba.com game ID.

    Continually requests a new version of the gamedetail json to determine the status
    of an ongoing game. Waits a determined amount of time depending on time remaining
    to avoid requests.

    Arguments: nba_id -> nba.com game ID
    Return: Returns None for the purpose of pausing any subsequent functions until
    the game is complete.
    """

    game_ongoing = True

    while game_ongoing:

        r = requests.get(f"http://data.nba.com/data/v2015/json/mobile_teams"
                         f"/nba/{SEASON}/scores/gamedetail/{nba_id}_gamedetail.json")
        r = r.json()

        game_status = r['g']['st']
        current_quarter = r['g']['p']

        # Attempt to handle NoneType game clocks gracefully
        if r['g']['cl']:
            time_left = int(r['g']['cl'].split(':')[0])
        else:
            print("Game clock is NoneType, sleeping 60 seconds...")
            time.sleep(60)
            continue

        print(f"Status: {game_status}, Quarter: {current_quarter}, Time: {time_left}")

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
            if time_left > 5:
                time.sleep(60*5)
                continue
            elif time_left >= 1:
                time.sleep(30)
                continue
            elif time_left == 0:

                # Check if game is over
                if game_status == 3:
                    print("Game Over")
                    game_ongoing = False
                else:
                    time.sleep(10)
                    continue
            else:
                print("Something unexpected happened during game_status_check...")  # TODO: Handle an error properly
                time.sleep(30)
                continue

    return True
