from datetime import datetime, timedelta
from distutils.util import strtobool
import os
import time
import pytz

from config import setup
from threads.game.game_thread import game_thread_handler
from bots.thread_handler_bot import edit_thread, get_thread
from threads.post_game.post_game import post_game_thread_handler
from threads.post_game.thread_stats import generate_stats_comment
from sidebar.update_sidebar import update_sidebar
from playoffs.playoff_data import get_series_status
from events.manager import get_event, get_next_event, update_event, get_previous_event
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
        game_thread_handler(event, playoff_data_arr)

        # Update event object
        event.meta['event_type'] = 'active'
        update_event(event)
        print(f"{os.path.basename(__file__)}: Event updated after init post: {event.id} - {event.summary}")

    elif event.meta['event_type'] == 'post':
        # TODO: Refactor this logic and in
        win = post_game_thread_handler(event, playoff_data_arr)

    else:
        print(f"{os.path.basename(__file__)}: Unhandled event_type: {event.meta['event_type']}")

    return event


def check_active_post(post):
    # TODO: Maybe think about rolling back changes to event title after post is made so event always matches post

    event = get_event(post.id)

    # Catch when event type manually set to done
    if event.meta['event_type'] == 'done':
        print(f"{os.path.basename(__file__)}: Event manually set to done, ending active post: {event.id} - {event.summary}")
        return None

    if not hash_match(event.body, event.meta['body_hash']):
        print(f"{os.path.basename(__file__)}: Update to active post body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        setattr(event, 'post', post.post)
        edit_thread(event)
        update_event(event)
        print(f"{os.path.basename(__file__)}: Event updated with body changes: {event.id} - {event.summary}")
        return event
    else:
        return post


def end_active_post(post):
    post.meta['event_type'] = 'done'
    update_event(post)
    print(f"{os.path.basename(__file__)}: Event updated, active post set to done: {post.id} - {post.summary}")

    return None


def update_playoff_data():
    pass


def check_if_last_event_still_active(po_data):

    prev_event = get_previous_event()

    if not prev_event:
        print(f"{os.path.basename(__file__)}: Found no previous post")
        return None

    # If previous event type is still post, game watch ongoing; restart game watch
    if prev_event.meta['event_type'] == 'post':
        print(f"{os.path.basename(__file__)}: prev_event was type post")
        ap = make_post(prev_event, po_data)
        return ap

    # If previous event still active, set post attribute and return event
    if prev_event.meta['event_type'] == 'active':
        prev_post = get_thread(prev_event.meta['reddit_id'])
        setattr(prev_event, 'post', prev_post)
        print(f"{os.path.basename(__file__)}: Previous event still active - {prev_event.summary}")
        return prev_event
    # Else, previous post no longer active so keep active_post None
    else:
        print(f"{os.path.basename(__file__)}: Previous event is no longer active")
        return None


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
skip = False

while bot_running:

    next_event = get_next_event()

    if not next_event or next_event.meta['event_type'] == 'done':
        print(f"{os.path.basename(__file__)}: All events finished posting.... exiting")
        bot_running = False
        break

    # If in playoffs, update playoff series before posting
    if IN_PLAYOFFS:
        playoff_data = [IN_PLAYOFFS, playoff_game_num, playoff_record, playoff_round]
    else:
        playoff_data = [IN_PLAYOFFS]

    if active_post:
        # Set prev_post_id on next_event
        setattr(next_event, 'prev_post_id', active_post.meta['reddit_id'])
        # Catch when active_post & next_event are same (next_event not updated in time)
        try:
            if active_post.id == next_event.id:
                print(f"{os.path.basename(__file__)}: ap==ne, ap:{active_post.id} - ne:{next_event.id}, sleeping 30")
                time.sleep(30)
                skip = True
        except AttributeError:
            pass

    # Ensure active_post is correct
    else:
        active_post = check_if_last_event_still_active(playoff_data)

    current_utc = datetime.timestamp(datetime.now())
    seconds_till_post = int(datetime.timestamp(next_event.start)) - int(current_utc)

    # If skip, next_event was same as active_event, grab next_event again
    if skip:
        skip = False

    # Time to post next_event and correct event_type
    elif seconds_till_post <= 0 and next_event.meta['event_type'] in ["pre", "game", "post"]:

        # next_event will become the active_post, add prev post reference finish the existing active_post
        if active_post:
            active_post = end_active_post(active_post)

        # Send event to appropriate thread handler
        if next_event.meta['event_type'] in ['pre', 'game', 'post']:
            active_post = make_post(next_event, playoff_data)
        else:
            print(f"{os.path.basename(__file__)}: next_event.meta['event_type'] is invalid")

        time.sleep(30)

    # There is an active post, check for updates to it
    elif active_post:
        # End active posts 6 hours after posting
        if datetime.now(tz=pytz.timezone(active_post.timezone)) > (active_post.start + timedelta(hours=6)):
            end_active_post(active_post)
        else:
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
