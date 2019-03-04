# 3/3/2019 - v1.0
# TK

from datetime import datetime
import json
import os
import time
import requests
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from bots.new_gists import update_gist

DEBUG = True if os.environ['DEBUG'] == 'True' else False

if DEBUG:
    debug_schedule = 0

URL = f"https://api.myjson.com/bins/{os.environ['BIN']}"

bot_running = True

while bot_running:

    if DEBUG:
        if debug_schedule == 0:
            with open('../data/all_events.json', 'r') as f:
                schedule = json.load(f)
        else:
            schedule = debug_schedule
    else:
        # Download json
        try:
            schedule = requests.get(URL).json()
            print("JSON Downloaded")
        except ValueError:
            print("Error downloading json file.")
            time.sleep(10)
            continue

    print(len(schedule))

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
        print("All events finished posting.... exiting")
        bot_running = False
        break

    # Update current time as utc
    current_utc = datetime.timestamp(datetime.now())

    # Check if the event has passed
    if int(current_utc) > int(next_event_utc):
        # Send event to appropriate thread handler
        if schedule[next_event_utc]['Type'] == 'post':
            headline, body = post_game_thread_handler(schedule[next_event_utc])
        else:
            headline, body = game_thread_handler(schedule[next_event_utc])

        gist_url = update_gist(headline, schedule[next_event_utc]['Type'], body)
        print(gist_url)

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
            print(f"{req.status_code}: JSON Updated")

        # Move onto next event
        time.sleep(10)
        continue

    # Calculate how long to wait
    time_to_event = int(next_event_utc) - int(current_utc)
    wait_time = time_to_event + 5

    print(f"Waiting {wait_time} seconds.")
    time.sleep(wait_time)
