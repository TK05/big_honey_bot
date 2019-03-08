# 3/3/2019 - v1.0
# TK

# TODO: Handle json download/upload errors, if any

from datetime import datetime, timedelta
import json
import os
import time
import requests
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from bots.new_gists import update_gist
from sidebar.update_sidebar import update_sidebar


DEBUG = True if os.environ['DEBUG'] == 'True' else False

if DEBUG:
    debug_schedule = 0

URL = f"https://api.myjson.com/bins/{os.environ['EVENT_BIN']}"

# Update sidebar upon initial loading
if os.environ['UPDATE_SIDEBAR']:
    print("Updating sidebar")
    update_sidebar()
    last_sidebar_update = datetime.timestamp(datetime.now())

bot_running = True

while bot_running:

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

    # Update current time as utc
    current_utc = datetime.timestamp(datetime.now())

    # Update sidebar every 24 hours
    if os.environ['UPDATE_SIDEBAR']:
        if (last_sidebar_update + (24*60*60)) < current_utc:
            print("Updating sidebar")
            update_sidebar()
            last_sidebar_update = current_utc

    # Calculate how long to wait
    wait_time_sec = int(next_event_utc) - int(current_utc)

    # Wait until it's time to post
    while wait_time_sec > 0:
        wait_time_str = str(timedelta(seconds=wait_time_sec)).split(':')

        print(f"Next post in {wait_time_str[0]} hours, {wait_time_str[1]} minutes, {wait_time_str[2]} seconds"
              f" on {schedule[next_event_utc]['Date_Str']} @ {schedule[next_event_utc]['Post_Date']} "
              f"{os.environ['TZ_STR']}")

        if DEBUG:
            time.sleep(10)
            wait_time_sec -= 10
        else:
            # Update every 30 minutes unless wait time < 30 minutes
            if wait_time_sec > 1800:
                time.sleep(1800)
                wait_time_sec -= 1800
            else:
                print(f"New Post in {wait_time_sec} seconds.")
                time.sleep(wait_time_sec)
                wait_time_sec -= wait_time_sec

    # Send event to appropriate thread handler
    if schedule[next_event_utc]['Type'] == 'post':
        headline, body = post_game_thread_handler(schedule[next_event_utc])
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
        # Convert to valid json
        valid_json = json.dumps(schedule)

        # Upload change to json
        header = {'Content-Type': 'application/json'}
        req = requests.put(URL, data=valid_json, headers=header)
        print(f"{req.status_code}: JSON update status code")
