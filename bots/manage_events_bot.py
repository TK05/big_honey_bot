# 3/3/2019 - v1.0
# TK

from datetime import datetime
import time
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from bots.new_gists import update_gist
from data.all_events import all_events

schedule = all_events

# Events sorted by UTC
event_keys = sorted(schedule.keys())
event_num = 0

while True:

    # Update current time as utc
    current_utc = datetime.timestamp(datetime.now())

    # UTC for next event
    next_event = event_keys[event_num]

    # Check if the event has passed
    if int(current_utc) < int(next_event):

        # Send event to appropriate thread handler
        if schedule[next_event]['Type'] == 'post':
            headline, body = post_game_thread_handler(schedule[next_event])
        else:
            headline, body = game_thread_handler(schedule[next_event])

        gist_url = update_gist(headline, schedule[next_event]['Type'], body)
        print(gist_url)

        # Move onto next event
        event_num += 1
        time.sleep(20)
        continue

    # Calculate how long to wait
    time_to_event = int(schedule[next_event]['UTC']) - int(current_utc)
    wait_time = time_to_event + 1

    time.sleep(wait_time)
