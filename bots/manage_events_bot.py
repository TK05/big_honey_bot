# TODO: Handle json download/upload errors, if any

from datetime import datetime, timedelta
import json
import os
import time
import requests
import pytz
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from threads.post_game.thread_stats import generate_stats_comment
from bots.new_gists import update_gist
from sidebar.update_sidebar import update_sidebar


DEBUG = True if os.environ['DEBUG'] == 'True' else False

if DEBUG:
    debug_schedule = 0
    print(os.environ)

URL = f"https://api.myjson.com/bins/{os.environ['EVENT_BIN']}"
TIMEZONE = os.environ['TIMEZONE']
UPDATE_SIDEBAR = True if os.environ['UPDATE_SIDEBAR'] == 'True' else False
THREAD_STATS = True if os.environ['THREAD_STATS'] == 'True' else False
IN_PLAYOFFS = True if os.environ['IN_PLAYOFFS'] == 'True' else False
PLAYOFF_GAME_NUM = int(os.environ['PLAYOFF_GAME_NUM'])
PLAYOFF_ROUND = os.environ['PLAYOFF_ROUND']
playoff_round = ' '.join(PLAYOFF_ROUND.split('_'))
playoff_record = [0, 0]

# Update sidebar at each restart
if UPDATE_SIDEBAR and not DEBUG:
    print(f"Updating sidebar @ {datetime.now().strftime('%H:%M')}")
    update_sidebar()

game_thread = None
post_game_thread = None
bot_running = True

while bot_running:

    was_post = False    # Necessary to track sidebar updates after post game threads

    if DEBUG:
        if debug_schedule == 0:
            with open('../data/all_events.json', 'r') as f:
                schedule = json.load(f)
        else:
            schedule = debug_schedule
    else:
        # Download json from myjson bin
        try:
            schedule = requests.get(URL).json()
            print(f"Event JSON Downloaded @ {datetime.now()}")
        except ValueError:
            print("Error downloading json file.")
            time.sleep(30)
            continue

    # Events sorted by UTC
    all_events = sorted(schedule.keys())

    next_event_utc = 0

    # Find next not finished event
    for event in all_events:
        if schedule[event]['Type'] != 'done':
            # Set UTC for next event
            next_event_utc = event
            break

    # Check if all events finished
    if next_event_utc == 0:
        print("All events finished posting.... exiting".upper())
        bot_running = False
        break

    current_utc = datetime.timestamp(datetime.now())
    wait_time_sec = int(next_event_utc) - int(current_utc)

    # Wait until it's time to post
    while wait_time_sec > 0:
        wait_time_str = str(timedelta(seconds=wait_time_sec)).split(':')

        print(f"Next post in {wait_time_str[0]} hours, {wait_time_str[1]} minutes"
              f" on {schedule[next_event_utc]['Date_Str']} @ {schedule[next_event_utc]['Post_Date']} "
              f"{os.environ['TZ_STR']}")

        # Update sidebar every day ~ 4am
        if UPDATE_SIDEBAR:
            if int(datetime.now(tz=pytz.timezone(TIMEZONE)).strftime('%H')) == 4:
                print(f"Updating sidebar @ {datetime.now().strftime('%H:%M')}")
                update_sidebar()

        if DEBUG:
            time.sleep(10)
            wait_time_sec -= 10
        else:
            # Update every 60 minutes unless wait time < 60 minutes
            if wait_time_sec > 3600:
                time.sleep(3600)
                wait_time_sec -= 3600
            else:
                print(f"New Post in {wait_time_sec} seconds.")
                time.sleep(wait_time_sec)
                wait_time_sec -= wait_time_sec

    playoff_data = [IN_PLAYOFFS, PLAYOFF_GAME_NUM, playoff_record, playoff_round]

    # Send event to appropriate thread handler
    if schedule[next_event_utc]['Type'] == 'post':
        headline, body, win, post_game_thread = post_game_thread_handler(schedule[next_event_utc], playoff_data)
        was_post = True
    elif schedule[next_event_utc]['Type'] == 'game':
        headline, body, game_thread = game_thread_handler(schedule[next_event_utc], playoff_data)
    else:
        headline, body, game_thread = game_thread_handler(schedule[next_event_utc], playoff_data)
        game_thread = None

    if not DEBUG:
        gist_url = update_gist(headline, schedule[next_event_utc]['Type'], body)
        print(f"Gist available at: {gist_url}")

    # Update event's type
    schedule[next_event_utc]['Type'] = 'done'

    if DEBUG:
        del schedule[next_event_utc]
        debug_schedule = schedule
    else:
        valid_json = json.dumps(schedule)

        # Upload change to json
        header = {'Content-Type': 'application/json'}
        req = requests.put(URL, data=valid_json, headers=header)
        print(f"{req.status_code}: JSON update status code")

    # Reply to thread with stats comment
    if THREAD_STATS and was_post and game_thread and post_game_thread:
        generate_stats_comment(game_thread, post_game_thread)

    # Update sidebar after ever post-game
    if UPDATE_SIDEBAR and was_post and not DEBUG:
        print("Sleeping 10 minutes to wait for standings to update")
        time.sleep(60 * 10)  # TODO: Check if 10 minutes is a long enough wait
        print("Updating sidebar")
        update_sidebar()
        last_sidebar_update = datetime.timestamp(datetime.now())

    if IN_PLAYOFFS and was_post:
        PLAYOFF_GAME_NUM += 1
        if win:
            playoff_record[0] += 1
        else:
            playoff_record[1] += 1

        print(f"New PO GAME#: {PLAYOFF_GAME_NUM}, PO SERIES NOW: {playoff_record}")

    if DEBUG:
        print("Debug end-wait 30 seconds")
        time.sleep(30)
