from datetime import datetime, timedelta
from distutils.util import strtobool
import os
import time
import pytz

from config import setup
from threads.game.game_thread import game_thread_handler
from bots.thread_handler_bot import edit_thread
from threads.post_game.post_game import post_game_thread_handler
from threads.post_game.thread_stats import generate_stats_comment
from sidebar.update_sidebar import update_sidebar
from playoffs.playoff_data import get_series_status
from events.manager import get_event, get_next_event, update_event
from tools.toolkit import hash_match


UPDATE_SIDEBAR = bool(strtobool(os.getenv('UPDATE_SIDEBAR', "False")))
THREAD_STATS = bool(strtobool(os.getenv('THREAD_STATS', "False")))
IN_PLAYOFFS = bool(strtobool(os.getenv('IN_PLAYOFFS', "False")))

TIMEZONE = pytz.timezone(setup['timezone'])


def make_post(event, playoff_data_arr):

    if not hash_match(event.summary, event.meta['title_hash']):
        print(f"{os.path.basename(__file__)}: Custom title detected: {event.summary}")
    if not hash_match(event.body, event.meta['body_hash']):
        print(f"{os.path.basename(__file__)}: Custom body detected, updated @ {event.updated.strftime('%b %d, %H:%M')}")

    if event.meta['event_type'] in ['pre', 'game']:
        post = game_thread_handler(event, playoff_data_arr)

        # Update event object
        setattr(event, 'post', post)
        event.meta['event_type'] = 'active'
        event.meta['reddit_id'] = post.id
        update_event(event)

    elif event.meta['event_type'] == 'post':
        # TODO: Refactor this logic and in
        win = post_game_thread_handler(event, playoff_data_arr)

    else:
        print(f"{os.path.basename(__file__)}: Unhandled event_type: {event.meta['event_type']}")

    return event


def check_active_post(post):

    event = get_event(post.id)

    if not hash_match(event.body, event.meta['body_hash']):
        print(f"{os.path.basename(__file__)}: Update to active post body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        edit_thread(post.post, event.body)
        update_event(event)
        print(f"{os.path.basename(__file__)}: Event updated: {event.summary}")
        updated_event = get_event(post.id)
        setattr(updated_event, 'post', post.post)
    else:
        updated_event = post

    # TODO: Maybe think about rolling back changes to event title after post is made so event always matches post

    return updated_event


def end_active_post(post):
    post.meta['event_type'] = 'done'
    update_event(post)
    return None


def update_playoff_data():
    pass


# TODO: if in playoffs, update calendar event w/ series status from here
# Update playoff data at each restart
if IN_PLAYOFFS:
    playoff_round, playoff_game_num, playoff_record = get_series_status()
else:
    playoff_round = playoff_game_num = playoff_record = None

# Update sidebar at each restart
update_sidebar()

# Initialize startup variables
game_thread = None
post_game_thread = None
active_post = None
bot_running = True

while bot_running:

    next_event = get_next_event()

    if not next_event or next_event.meta['event_type'] == 'done':
        print(f"{os.path.basename(__file__)}: All events finished posting.... exiting".upper())
        bot_running = False
        break

    current_utc = datetime.timestamp(datetime.now())
    seconds_till_post = int(datetime.timestamp(next_event.start)) - int(current_utc)

    # Time to post next_event and correct event_type
    if seconds_till_post <= 0 and next_event.meta['event_type'] in ["pre", "game", "post"]:

        # Catch when active_post & next_event are same (next_event not updated in time)
        try:
            if active_post.id == next_event.id:
                print(f"{os.path.basename(__file__)}: ap==ne, ap:{active_post.id} - ne:{next_event.id}, sleeping 30")
                time.sleep(30)
                break
        except AttributeError:
            pass

        # next_event will become the active_post, add prev post reference finish the existing active_post
        if active_post:
            next_event.meta['prev_post_id'] = active_post.post.id
            active_post = end_active_post(active_post)

        # If in playoffs, update playoff series before posting
        if IN_PLAYOFFS:
            playoff_data = [IN_PLAYOFFS, playoff_game_num, playoff_record, playoff_round]
        else:
            playoff_data = [IN_PLAYOFFS]

        # Send event to appropriate thread handler
        if next_event.meta['event_type'] in ['pre', 'game']:
            active_post = make_post(next_event, playoff_data)
        elif next_event.meta['event_type'] == 'post':
            make_post(next_event, playoff_data)
            # event_type already set to active, set to done
            active_post = end_active_post(next_event)
        else:
            print(f"{os.path.basename(__file__)}: next_event.meta['event_type'] is invalid")

        time.sleep(30)

    # There is an active post, check for updates to it
    elif active_post:
        active_post = check_active_post(active_post)
        time.sleep(30)

    # Not time to post and no active_post
    else:
        # Update sidebar every hour while no active post
        update_sidebar()

        # Determine wait time
        try:
            if seconds_till_post < 60:
                print(f"{os.path.basename(__file__)}: {next_event.summary} in {timedelta(seconds=seconds_till_post)}, sleeping {seconds_till_post}")
                time.sleep(seconds_till_post)
            else:
                wait_time = seconds_till_post if seconds_till_post < 3600 else 3600
                print(f"{os.path.basename(__file__)}: {next_event.summary} in {timedelta(seconds=seconds_till_post)}, sleeping {wait_time}")
                time.sleep(wait_time)
        except ValueError:
            print(f"{os.path.basename(__file__)}: seconds_till_post was negative, exiting")
            bot_running = False
            break
