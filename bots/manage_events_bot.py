# TODO: Handle json download/upload errors, if any

from datetime import datetime, timedelta
import json
import os
import time
import requests
import pytz
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from bots.new_gists import update_gist
from sidebar.update_sidebar import update_sidebar


DEBUG = True if os.environ['DEBUG'] == 'True' else False

if DEBUG:
    debug_schedule = 0

URL = f"https://api.myjson.com/bins/{os.environ['EVENT_BIN']}"
UPDATE_SIDEBAR = os.environ['UPDATE_SIDEBAR']

# Update sidebar at each restart
if UPDATE_SIDEBAR:
    print(f"Updating sidebar @ {datetime.now().strftime('%H:%M')}")
    update_sidebar()

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
            if int(datetime.now(tz=pytz.timezone(os.environ['TIMEZONE'])).strftime('%H')) == 4:
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

    # Send event to appropriate thread handler
    if schedule[next_event_utc]['Type'] == 'post':
        headline, body = post_game_thread_handler(schedule[next_event_utc])
        was_post = True
    else:
        headline, body = game_thread_handler(schedule[next_event_utc])

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

    # Update sidebar after ever post-game
    if UPDATE_SIDEBAR and was_post and not DEBUG:
        print("Sleeping 10 minutes to wait for standings to update")
        time.sleep(60 * 10)  # TODO: Check if 10 minutes is a long enough wait
        print("Updating sidebar")
        update_sidebar()
        last_sidebar_update = datetime.timestamp(datetime.now())
