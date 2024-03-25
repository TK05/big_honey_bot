import os
import time
import logging
from datetime import timedelta

from big_honey_bot.helpers import hash_match, get_datetime, get_timestamp_from_datetime
from big_honey_bot.config.helpers import get_env
from big_honey_bot.sidebar.helpers import update_sidebar
from big_honey_bot.playoffs.helpers import get_series_status
from big_honey_bot.threads.main import edit_thread, get_thread
from big_honey_bot.threads.game.thread import game_thread_handler
from big_honey_bot.threads.off_day.thread import off_day_thread_handler
from big_honey_bot.threads.post_game.thread import post_game_thread_handler
from big_honey_bot.threads.post_game.thread_stats import generate_stats_comment
from big_honey_bot.events.main import get_event, get_next_event, update_event, get_previous_event


logger = logging.getLogger(f"{os.path.basename(__file__)}")


def make_post(event, po_data):

    if not hash_match(event.summary, event.meta['title_hash']):
        logger.info(f"Custom title detected: {event.summary}")
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Custom body detected, updated @ {event.updated.strftime('%b %d, %H:%M')}")

    if event.meta['event_type'] in ['pre', 'game']:
        game_thread_handler(event, po_data)

        # Update event object
        event.meta['event_type'] = 'active'
        update_event(event)
        logger.info(f"Event updated after init post: {event.id} - {event.summary}")

    elif event.meta['event_type'] == 'post':
        post_game_thread_handler(event, po_data)

        # Generate thread stats after post game thread is posted
        if get_env('THREAD_STATS'):
            try:
                prev_game_event = get_previous_event(penultimate=True)
                prev_post = get_thread(prev_game_event.meta['reddit_id'])
                generate_stats_comment(game_thread=prev_post, post_game_thread=event.post)
            except Exception as e:
                logger.error(f"Error caught while generating thread stats: {e}")

    elif event.meta['event_type'] == 'off':
        off_day_thread_handler(event)

        # Update event object
        event.meta['event_type'] = 'active'
        update_event(event)
        logger.info(f"Event updated after init post: {event.id} - {event.summary}")

    else:
        logger.info(f"Unhandled event_type: {event.meta['event_type']}")

    return event


def check_active_post(post):
    event = get_event(post.id)

    # Catch when event type manually set to done
    if event.meta['event_type'] == 'done':
        logger.info(f"Event manually set to done, ending active post: {event.id} - {event.summary}")
        return None

    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Update to active post body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        setattr(event, 'post', post.post)
        edit_thread(event)
        update_event(event)
        logger.info(f"Event updated with body changes: {event.id} - {event.summary}")
        return event
    else:
        return post


def end_active_post(post):
    post.meta['event_type'] = 'done'
    update_event(post)
    logger.info(f"Event updated, active post set to done: {post.id} - {post.summary}")


def get_playoff_data():
    if get_env('IN_PLAYOFFS'):
        playoff_round, playoff_game_num, playoff_record = get_series_status()
        return [playoff_round, playoff_game_num, playoff_record]
    else:
        return None


def check_if_last_event_still_active(po_data):

    prev_event = get_previous_event()

    if not prev_event:
        logger.info(f"Found no previous post")
        return None

    # If previous event type is still post, game watch ongoing; restart game watch
    if prev_event.meta['event_type'] == 'post':
        logger.info(f"prev_event was type post")
        ap = make_post(prev_event, po_data)
        return ap

    # If previous event still active, set post attribute and return event
    if prev_event.meta['event_type'] == 'active':
        prev_post = get_thread(prev_event.meta['reddit_id'])
        setattr(prev_event, 'post', prev_post)
        logger.info(f"Previous event still active - {prev_event.summary}")
        return prev_event
    # Else, previous post no longer active so keep active_post None
    else:
        logger.info(f"Previous event is no longer active")
        return None

def run():

    # Update playoff data at each restart
    playoff_data = get_playoff_data()
    logger.info(f"IN_PLAYOFFS: {playoff_data}")

    # Update sidebar at each restart
    update_sidebar()

    # Initialize startup variables
    active_post = None
    bot_running = True
    skip = False
    upcoming_event_types = ['pre', 'game', 'post', 'off']

    while bot_running:

        next_event = get_next_event()

        if not next_event or next_event.meta['event_type'] == 'done':
            logger.warning(f"All events finished posting.... exiting")
            bot_running = False
            break

        # Update playoff series before posting
        playoff_data = get_playoff_data()

        if active_post:
            # Set prev_post_id on next_event
            setattr(next_event, 'prev_post_id', active_post.meta['reddit_id'])
            # Catch when active_post & next_event are same (next_event not updated in time)
            try:
                if active_post.id == next_event.id:
                    logger.info(f"ap==ne, ap:{active_post.id} - ne:{next_event.id}, sleeping 30")
                    time.sleep(30)
                    skip = True
            except AttributeError:
                pass

        # Ensure active_post is correct
        else:
            active_post = check_if_last_event_still_active(playoff_data)

        current_utc = get_timestamp_from_datetime()
        seconds_till_post = get_timestamp_from_datetime(dt=next_event.start) - current_utc

        # If skip, next_event was same as active_event, grab next_event again
        if skip:
            skip = False

        # Time to post next_event and correct event_type
        elif seconds_till_post <= 0 and next_event.meta['event_type'] in upcoming_event_types:

            # next_event will become the active_post, add prev post reference finish the existing active_post
            if active_post:
                end_active_post(active_post)

            # Send event to appropriate thread handler
            if next_event.meta['event_type'] in upcoming_event_types:
                active_post = make_post(next_event, playoff_data)
            else:
                logger.warning(f"next_event.meta['event_type'] is invalid")

            time.sleep(30)

        # There is an active post, check for updates to it
        elif active_post:
            # End active posts 12 hours after posting
            if get_datetime(add_tz=True, tz=active_post.timezone) > (active_post.start + timedelta(hours=12)):
                logger.info(f"active_post active longer than 12 hours, setting to done")
                end_active_post(active_post)
            else:
                logger.debug(f"ne: {next_event.summary[:30]}... ap: {active_post.summary[:30]}...")
                active_post = check_active_post(active_post)
                time.sleep(30)

        # Not time to post and no active_post
        else:
            # Update sidebar every hour while no active post
            update_sidebar()

            # Determine wait time
            try:
                if seconds_till_post < 60:
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_post)}, sleeping {seconds_till_post}")
                    time.sleep(seconds_till_post)
                else:
                    wait_time = seconds_till_post if seconds_till_post < 3600 else 3600
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_post)}, sleeping {wait_time}")
                    time.sleep(wait_time)
            except ValueError:
                logger.error(f"seconds_till_post was negative, exiting")
                bot_running = False
                break
