import time
import logging
import threading
from datetime import timedelta

from big_honey_bot.helpers import hash_match, get_datetime, get_timestamp_from_datetime, dyn_event_types
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


def do_event(event, update_only=False):

    global active_event

    if not hash_match(event.summary, event.meta['title_hash']):
        logger.info(f"Custom title detected: {event.summary}")
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Custom body detected, updated @ {event.updated.strftime('%b %d, %H:%M')}")

    if event.meta['event_type'] in ['pre', 'game']:
        game_thread_handler(event, playoff_data, update_only)
        update_event_and_set_to_active(event)

    elif event.meta['event_type'] == 'post':
        # Set post game events to active prior to running game check
        update_event_and_set_to_active(event)
        post_game_thread_handler(event, playoff_data)

        # Then update event again after finish with data
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

    active_event = event


def update_event_and_set_to_active(event):
    event.meta['event_status'] = 'active'
    update_event(event)
    logger.info(f"Event updated and set to active: {event.id} - {event.summary}")


def check_active_event_for_manual_changes():
    
    global active_event

    if not active_event:
        return
    
    event = get_event(active_event.id)

    # Catch when event type manually set to done
    if event.meta['event_status'] == 'done':
        logger.info(f"Event manually set to done, ending active event: {event.id} - {event.summary}")
        active_event = None

    # Update post if event body has been changed since last check
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Update to active event's body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        setattr(event, 'post', active_event.post)
        edit_thread(event)
        update_event(event)
        logger.info(f"Post & Event updated after body changes: {event.id} - {event.summary}")
        
        active_event = event


def update_active_event():

    global active_event
    
    active_event = check_active_event_for_manual_changes()

    if not active_event:
        return

    # End active events 12 hours after start time
    if get_datetime(add_tz=True, tz=active_event.timezone) > (active_event.start + timedelta(hours=12)):
        logger.info(f"active_event active longer than 12 hours, setting to done")
        end_active_event(active_event)

    elif active_event.meta['event_type'] in dyn_event_types:
        logger.info(f"Sending active event to thread handlers for updating, last updated: {active_event.updated}")
        do_event(active_event, update_only=True)


def end_active_event():
    
    global active_event
    
    active_event.meta['event_status'] = 'done'
    update_event(active_event)
    logger.info(f"Active event was set to done: {active_event.id} - {active_event.summary}")

    active_event = None


def update_playoff_data():

    global playoff_data
    
    # Set playoff_data for global use
    if get_env('IN_PLAYOFFS'):
        playoff_round, playoff_game_num, playoff_record = get_series_status()
        playoff_data = [playoff_round, playoff_game_num, playoff_record]
    else:
        playoff_data = None


def check_if_prev_event_still_active():

    global active_event

    prev_event = get_previous_event()

    if not prev_event:
        logger.info(f"Found no previous event")
        active_event = None
    
    try:
        pe_type = prev_event.meta['event_type']
        pe_status = prev_event.meta['event_status']
    except KeyError:
        logger.error(f"Previous event's meta was missing some required meta keys, ignoring previous event...")
        active_event = None

    # If previous event type is post and status is not done, game watch may possibly need to be restarted
    if pe_type == 'post' and pe_status != 'done':
    
        # Check current time and resume game watch if event.start < 3 hours ago
        if get_datetime(add_tz=True, tz=prev_event.timezone) < (prev_event.start + timedelta(hours=3)):
            logger.info("Previous event was type='post' & status!='done'")
            do_event(prev_event)
        
        # If previous event is too old to game watch, then assume there was no previous event
        else:
            logger.info(f"Previous event was type='post' & status!='done' but skipping game check as start time is too old: {prev_event.start}")
            active_event = None

    # If previous event still active, set post attribute and return event
    if pe_status == 'active':
        prev_post = get_thread(prev_event.meta['reddit_id'])
        setattr(prev_event, 'post', prev_post)
        logger.info(f"Previous event still active - {prev_event.summary}")
        active_event = prev_event
    
    # Else, previous event no longer active, unset active_event
    else:
        logger.info("Previous event is no longer active")
        active_event = None

def run():

    # Initialize globals
    global playoff_data
    global active_event
    global bot_running

    playoff_data = None
    active_event = None
    bot_running = True


    def _maint_tasks():
        # Maint tasks are things to do every hour likey get playoff updates, update sidebar and 
        # update active threads that have dynamic data.
        
        logger.info("Maintanence tasks thread started...")

        # Do these once at startup
        update_sidebar()
        update_playoff_data()
        check_if_prev_event_still_active()
        update_active_event()
        
        while bot_running:
            # After doing once at startup, sleep
            sleep_time = (60*30) if get_env('DEBUG') == False else (60*2)
            time.sleep(sleep_time)

            # Then do tasks
            logger.info("Maintanence tasks running...")

            update_sidebar()
            update_playoff_data()
            check_if_prev_event_still_active()
            update_active_event()


    # Initialize locals
    skip = False

    # Create separate thread for maint_tasks & start thread
    maint_tasks_thread = threading.Thread(target=_maint_tasks, daemon=True)
    maint_tasks_thread.start()   

    # Init debug logging
    logger.debug(f"IN_PLAYOFFS: {playoff_data}")

    while bot_running:

        next_event = get_next_event()

        if not next_event or next_event.meta['event_status'] == 'done':
            logger.warning(f"No next event found.... exiting")
            bot_running = False
            break

        if active_event:

            # Catch when active_event & next_event are same (next_event not updated in time)
            try:
                if active_event.id == next_event.id:
                    logger.info(f"active_event==next_event; active_event: {active_event.id} -- next_event: {next_event.id}, sleeping 30")
                    time.sleep(30)
                    skip = True
            except AttributeError:
                pass

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
                end_active_event()

            # Send event to appropriate thread handler and make next_event the active_event
            do_event(next_event)
            time.sleep(30)

        # Not time to do next_event but there is an active_event; check for updates to it
        elif active_event:
            
            # Sleep, then refresh active_event for any changes
            logger.debug(f"next_event: {next_event.summary} -- active_event: {active_event.summary}")
            time.sleep(30)
            check_active_event_for_manual_changes()

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
            
            except ValueError:
                logger.error(f"seconds_till_event was negative, exiting")
                bot_running = False
                break
