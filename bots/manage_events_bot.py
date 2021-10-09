# TODO: Handle changes to event (hash differences)
from datetime import datetime, timedelta
import json
import os
import time
import pytz

from config import setup
from threads.game.game_thread import game_thread_handler
from threads.post_game.post_game import post_game_thread_handler
from threads.post_game.thread_stats import generate_stats_comment
from sidebar.update_sidebar import update_sidebar
from playoffs.playoff_data import get_series_status
from events.manager import get_next_event


UPDATE_SIDEBAR = os.environ['UPDATE_SIDEBAR'] or False
THREAD_STATS = os.environ['THREAD_STATS'] or False
IN_PLAYOFFS = os.environ['IN_PLAYOFFS'] or False

TIMEZONE = pytz.timezone(setup['timezone'])

# Update playoff data at each restart
if IN_PLAYOFFS:
    playoff_round, playoff_game_num, playoff_record = get_series_status()

# Update sidebar at each restart
if UPDATE_SIDEBAR:
    print(f"Updating sidebar @ {datetime.now().strftime('%H:%M')}")
    update_sidebar()

game_thread = None
post_game_thread = None
bot_running = True

while bot_running:

    was_post = False    # Necessary to track sidebar updates after post game threads
    next_event = get_next_event()

    if not next_event:
        print("All events finished posting.... exiting".upper())
        bot_running = False
        break

    current_utc = datetime.timestamp(datetime.now())
    wait_time_sec = int(next_event.meta['post_utc']) - int(current_utc)

    # Wait until it's time to post
    while wait_time_sec > 0:
        wait_time_str = str(timedelta(seconds=wait_time_sec)).split(':')

        print(f"Next post in {wait_time_str[0]} hours, {wait_time_str[1]} minutes"
              f" on {datetime.fromtimestamp(next_event.meta['post_utc']).astimezone(TIMEZONE).strftime('%A %B %d @ %H:%M %p %Z')}")

        # Update sidebar every day ~ 4am
        if UPDATE_SIDEBAR:
            if int(datetime.now(tz=TIMEZONE).strftime('%H')) == 4:
                print(f"Updating sidebar @ {datetime.now().strftime('%H:%M')}")
                update_sidebar()

        # Print update every 60 minutes unless wait time < 60 minutes
        if wait_time_sec > 3600:
            time.sleep(3600)
            wait_time_sec -= 3600
        else:
            print(f"New Post in {wait_time_sec} seconds.")
            time.sleep(wait_time_sec)
            wait_time_sec -= wait_time_sec

    if IN_PLAYOFFS:
        playoff_data = [IN_PLAYOFFS, playoff_game_num, playoff_record, playoff_round]
    else:
        playoff_data = [IN_PLAYOFFS]

    # Send event to appropriate thread handler
    if next_event.meta['event_type'] == 'post':
        # TODO: Handle passing this back to post game events on calendar
        headline, body, win, post_game_thread = post_game_thread_handler(next_event.meta['post_utc'], playoff_data)
        was_post = True
    elif next_event.meta['event_type'] == 'game':
        headline, body, game_thread = game_thread_handler(next_event.meta['post_utc'], playoff_data)
    else:
        headline, body, game_thread = game_thread_handler(next_event.meta['post_utc'], playoff_data)
        game_thread = None

    # TODO: Update calendar here
    # gist_url = update_gist(headline, schedule[next_event_utc]['Type'], body)
    # print(f"Gist available at: {gist_url}")

    # TODO: event_type = 'done' for done, 'active' for ongoing
    # # Update event's type
    # schedule[next_event_utc]['Type'] = 'done'

    # TODO: Update calendar
    # valid_json = json.dumps(schedule)
    #
    # # Upload change to schedule json
    # gist_url = update_gist(f"Updated: {datetime.now().strftime('%c')}", 'schedule', valid_json)
    # print(f"Schedule Gist Updated: {gist_url}")

    # Reply to thread with stats comment
    if THREAD_STATS and was_post and game_thread and post_game_thread:
        generate_stats_comment(game_thread, post_game_thread)

    # Update sidebar after post-game post
    if UPDATE_SIDEBAR and was_post:
        print("Sleeping 10 minutes to wait for standings to update")
        time.sleep(60 * 10)
        print("Updating sidebar")
        update_sidebar()
        last_sidebar_update = datetime.timestamp(datetime.now())

    if IN_PLAYOFFS and was_post:
        playoff_game_num += 1
        if win:
            playoff_record[0] += 1
        else:
            playoff_record[1] += 1

        print(f"New PO GAME#: {playoff_game_num}, PO SERIES NOW: {playoff_record}")
