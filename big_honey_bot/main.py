import time
import logging
from datetime import timedelta

from big_honey_bot.helpers import hash_match, get_datetime, get_timestamp_from_datetime
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.sidebar.helpers import update_sidebar
from big_honey_bot.playoffs.helpers import get_series_status
from big_honey_bot.threads.main import edit_thread, get_thread
from big_honey_bot.threads.game.thread import game_thread_handler
from big_honey_bot.threads.off_day.thread import off_day_thread_handler
from big_honey_bot.threads.post_game.thread import post_game_thread_handler
from big_honey_bot.threads.post_game.thread_stats import generate_stats_comment
from big_honey_bot.events.main import get_event, get_next_event, update_event, get_previous_event


logger = logging.getLogger(get_pname_fname_str(__file__))


def do_event(event, po_data):

    if not hash_match(event.summary, event.meta['title_hash']):
        logger.info(f"Custom title detected: {event.summary}")
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Custom body detected, updated @ {event.updated.strftime('%b %d, %H:%M')}")

    if event.meta['event_type'] in ['pre', 'game']:
        game_thread_handler(event, po_data)
        update_event_and_set_to_active(event)

    elif event.meta['event_type'] == 'post':
        post_game_thread_handler(event, po_data)
        update_event_and_set_to_active(event)

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
        update_event_and_set_to_active(event)

    else:
        logger.info(f"Unhandled event_type: {event.meta['event_type']}")

    return event


def update_event_and_set_to_active(event):
    event.meta['event_status'] = 'active'
    update_event(event)
    logger.info(f"Event updated and set to active: {event.id} - {event.summary}")


def refresh_active_event(in_event):
    event = get_event(in_event.id)

    # Catch when event type manually set to done
    if event.meta['event_status'] == 'done':
        logger.info(f"Event manually set to done, ending active event: {event.id} - {event.summary}")
        return None

    # Update post if event body has been changed since last check
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Update to active event's body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        setattr(event, 'post', in_event.post)
        edit_thread(event)
        update_event(event)
        logger.info(f"Post & Event updated after body changes: {event.id} - {event.summary}")
        
        return event
    
    # Still active and no changes, return in_event
    else:
        return in_event


def end_active_event(event):
    event.meta['event_status'] = 'done'
    update_event(event)
    logger.info(f"Active event was set to done: {event.id} - {event.summary}")


def get_playoff_data():
    if get_env('IN_PLAYOFFS'):
        playoff_round, playoff_game_num, playoff_record = get_series_status()
        return [playoff_round, playoff_game_num, playoff_record]
    else:
        return None


def check_if_prev_event_still_active(po_data):

    prev_event = get_previous_event()

    if not prev_event:
        logger.info(f"Found no previous event")
        return None

    # If previous event type is post and status is not done, game watch may possibly need to be restarted
    if prev_event.meta['event_type'] == 'post' and prev_event.meta['event_status'] != 'done':
    
        # Check current time and resume game watch if event.start < 3 hours ago
        if get_datetime(add_tz=True, tz=prev_event.timezone) < (prev_event.start + timedelta(hours=3)):
            logger.info("Previous event was type='post' & status!='done'")
            active_event = do_event(prev_event, po_data)

            return active_event
        
        # If previous event is too old to game watch, then assume there was no previous event
        else:
            logger.info(f"Previous event was type='post' & status!='done' but skipping game check as start time is too old: {prev_event.start}")
            return None

    # If previous event still active, set post attribute and return event
    if prev_event.meta['event_status'] == 'active':
        prev_post = get_thread(prev_event.meta['reddit_id'])
        setattr(prev_event, 'post', prev_post)
        logger.info(f"Previous event still active - {prev_event.summary}")
        return prev_event
    
    # Else, previous event no longer active, unset active_event
    else:
        logger.info("Previous event is no longer active")
        return None

def run():

    # Update playoff data at each restart
    playoff_data = get_playoff_data()
    logger.debug(f"IN_PLAYOFFS: {playoff_data}")

    # Update sidebar at each restart
    update_sidebar()

    # Initialize startup variables
    active_event = None
    bot_running = True
    skip = False

    while bot_running:

        next_event = get_next_event()

        if not next_event or next_event.meta['event_status'] == 'done':
            logger.warning(f"No next event found.... exiting")
            bot_running = False
            break

        playoff_data = get_playoff_data()

        if active_event:

            # Catch when active_event & next_event are same (next_event not updated in time)
            try:
                if active_event.id == next_event.id:
                    logger.info(f"active_event==next_event; active_event: {active_event.id} -- next_event: {next_event.id}, sleeping 30")
                    time.sleep(30)
                    skip = True
            except AttributeError:
                pass

        # Check previous event to see if still active or needs doing
        else:
            active_event = check_if_prev_event_still_active(playoff_data)

        current_time = get_timestamp_from_datetime()
        seconds_till_event = get_timestamp_from_datetime(dt=next_event.start) - current_time

        # If skip, next_event was same as active_event, skip rest of loop and grab next_event again
        if skip:
            skip = False

        # Time to do next_event
        elif seconds_till_event <= 0 and next_event.meta['event_type']:

            # Update next_event.prev_reddit_id w/ reddit_id of current active_event & set active_event to done
            if active_event:
                setattr(next_event, 'prev_reddit_id', active_event.meta['reddit_id'])
                end_active_event(active_event)

            # Send event to appropriate thread handler and make next_event the active_event
            active_event = do_event(next_event, playoff_data)
            time.sleep(30)

        # Not time to do next_event but there is an active_event; check for updates to it
        elif active_event:

            # End active events 12 hours after start time
            if get_datetime(add_tz=True, tz=active_event.timezone) > (active_event.start + timedelta(hours=12)):
                logger.info(f"active_event active longer than 12 hours, setting to done")
                end_active_event(active_event)
            
            # Sleep, then refresh active_event for any changes
            logger.debug(f"next_event: {next_event.summary} -- active_event: {active_event.summary}")
            time.sleep(30)
            active_event = refresh_active_event(active_event)

        # Not time to do next_event and no active_event
        else:
            # Determine wait time
            try:   
                # next_event start time is near, sleep exact amount
                if seconds_till_event < 60:
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_event)}, sleeping {seconds_till_event}")
                    time.sleep(seconds_till_event)
                
                # next_event start time is far, sleep longer & update_sidebar after
                else:
                    wait_time = seconds_till_event if seconds_till_event < 3600 else 3600
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_event)}, sleeping {wait_time}")
                    time.sleep(wait_time)
                    
                    # Update sidebar (roughly) every hour while no active_event
                    update_sidebar()
            
            except ValueError:
                logger.error(f"seconds_till_event was negative, exiting")
                bot_running = False
                break
