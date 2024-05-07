import logging
import time
import threading
from datetime import timedelta

from big_honey_bot.helpers import hash_match, get_datetime, get_timestamp_from_datetime, dyn_event_types
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.sidebar.helpers import update_sidebar
from big_honey_bot.playoffs.helpers import get_series_status
from big_honey_bot.threads.main import edit_thread, generate_thread_stats as gts
from big_honey_bot.threads.game.thread import game_thread_handler
from big_honey_bot.threads.off_day.thread import off_day_thread_handler
from big_honey_bot.threads.post_game.thread import post_game_thread_handler
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
    elif event.meta['event_type'] == 'post':
        post_game_thread_handler(event, playoff_data)
    elif event.meta['event_type'] == 'off':
        off_day_thread_handler(event, update_only)
    else:
        logger.error(f"Event type while do_event has no instructions -- type: {event.meta['event_type']} -- {event.summary}")

    # Create thread stats of prev event on new event
    if not update_only:
        generate_thread_stats(event)

    # End active event after posting (when update_only=False)
    if active_event and not update_only:
        end_active_event()

    # Set this event to active and update event
    update_event_and_set_to_active(event)


def generate_thread_stats(curr_event):
    
    # Add comment to new thread of thread stats for previous thread
    if get_env('THREAD_STATS'):
        prev_thread_id = None
        prev_thread_type = None

        # Only generate thread stats if currente event has prev_reddit_id set
        if not curr_event.meta.get('prev_reddit_id'):
            logger.warn(f"Could not generate thread stats as event has no prev_reddit_id set -- {curr_event.summary}")
        
        # If still active event; gen thread stats from that thread
        elif active_event:
            if active_event.meta['reddit_id'] == curr_event.meta['prev_reddit_id']:
                prev_thread_id = active_event.meta['reddit_id']
                prev_thread_type = active_event.meta['event_type']
            else:
                logger.warn(f"Did not generate thread stats as active_event.reddit_id != event.prev_reddit_id -- " \
                        f"{active_event.meta['reddit_id']} != {curr_event.meta['prev_reddit_id']}")
        
        # If no active event; get penultimate previous event and check that
        else:
            prev_event = get_previous_event(penultimate=True)
            if prev_event.meta['reddit_id'] == curr_event.meta['prev_reddit_id']:
                prev_thread_id = prev_event.meta['reddit_id']
                prev_thread_type = prev_event.meta['event_type']
            else:
                logger.warn(f"Did not generate thread stats as prev_event.reddit_id != event.prev_reddit_id -- " \
                        f"{prev_event.meta['reddit_id']} != {curr_event.meta['prev_reddit_id']}")
        
        # If previous thread found, generate thread stats
        if prev_thread_id and prev_thread_type:
            try:
                gts(prev_thread_id, prev_thread_type, curr_event.meta['reddit_id'])
            except Exception as e:
                logger.error(f"Error caught while generating thread stats: {e}")


def update_event_and_set_to_active(event):
    
    global active_event
    
    event.meta['event_status'] = 'active'
    update_event(event)
    logger.info(f"Event updated and set to active: {event.id} - {event.summary}")
    active_event = event


def check_active_event_for_manual_changes():
    
    global active_event

    if not active_event:
        logger.debug("active_event=None during check for manual changes")
        return
    
    event = get_event(active_event.id)

    # Catch when event type manually set to done
    if event.meta['event_status'] == 'done':
        logger.info(f"Event manually set to done, ending active event: {event.id} - {event.summary}")
        active_event = None

    # Update post if event body has been changed since last check
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Update to active event's body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        
        # Update thread on reddit and then update event to store new hash
        edit_thread(event)
        update_event(event)

        logger.info(f"Post & Event updated after body changes: {event.id} - {event.summary}")
        
        active_event = event


def update_next_event():

    global next_event

    if active_event:
        if not next_event.meta.get('prev_reddit_id') or next_event.meta['prev_reddit_id'] == "":
            next_event.meta['prev_reddit_id'] = active_event.meta['reddit_id']
            update_event(next_event)
            logger.info(f"Updating next_event's prev_reddit_id with reddit_id of active_event -- prev_reddit_id: {next_event.meta['prev_reddit_id']}")
        elif next_event.meta['prev_reddit_id'] != active_event.meta['reddit_id']:
            next_event.meta['prev_reddit_id'] = active_event.meta['reddit_id']
            update_event(next_event)
            logger.warn(f"next_event's prev_reddit_id did not match active_event's reddit_id, updating: prev_reddit_id {next_event.meta['prev_reddit_id']} ")


def update_active_event():

    global active_event
    
    check_active_event_for_manual_changes()

    if not active_event:
        logger.debug("active_event=None during update of active event")
        return

    # End active events 12 hours after start time
    if get_datetime(add_tz=True, tz=active_event.timezone) > (active_event.start + timedelta(hours=12)):
        logger.info(f"active_event active longer than 12 hours, setting to done")
        end_active_event()

    elif active_event.meta['event_type'] in dyn_event_types:
        logger.info(f"Sending active event to thread handlers for updating, last updated: {active_event.updated}")
        do_event(active_event, update_only=True)


def end_active_event():
    
    global active_event

    if not active_event:
        return
    
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
        return
    
    try:
        pe_type = prev_event.meta['event_type']
        pe_status = prev_event.meta['event_status']
    except KeyError:
        logger.warning(f"Previous event's meta was missing some required meta keys, ignoring previous event...")
        active_event = None

    # TODO: think/rethink/actually-think if we really need to send this to game check and possible post
    # If previous event type is post and status is upcoming, game watch may possibly need to be restarted
    if pe_type == 'post' and pe_status == 'upcoming':

        # First check if prev_event is same as next_event which will be handled by run
        if next_event and (prev_event.id == next_event.id):
            logger.info(f"Previous event was type={pe_type} & status={pe_status} but has same ID as next event, skipping game check")
            active_event = prev_event
            end_active_event()
    
        # Check current time and resume game watch if event.start < 3 hours ago
        elif get_datetime(add_tz=True, tz=prev_event.timezone) < (prev_event.start + timedelta(hours=3)):
            logger.info(f"Previous event was type={pe_type} & status={pe_status}, checking penultimate event")
            pen_event = get_previous_event(penultimate=True)
            if pen_event.meta['event_type'] == 'active':
                active_event = pen_event
                logger.info(f"Setting penultimate event to active: {pen_event.summary}")
            logger.info(f"Sending previous event with event_type={pe_type} to do_event")
            do_event(prev_event)
        
        # If previous event is too old to game watch, then set to done
        else:
            logger.info(f"Previous event was type={pe_type} & status={pe_status} but skipping game check as start time is too old: {prev_event.start}")
            active_event = prev_event
            end_active_event()

    # If previous event still active, set active_event
    if pe_status == 'active':
        logger.info(f"Previous event still active - {prev_event.summary}")
        active_event = prev_event
    
    # Else, previous event no longer active, unset active_event
    else:
        logger.info("Previous event is no longer active")
        active_event = None


def do_maint_tasks():
    # Maint tasks are things to do every maint_interval
    # IE: get playoff updates, update sidebar and  update active threads that have dynamic data.
    while True:
        logger.info("Maintanence tasks running...")

        # Do these things each cycle
        update_sidebar()
        update_playoff_data()
        check_if_prev_event_still_active()
        update_active_event()

        # Continually check active_event.reddit_id==next_event.prev_reddit_id
        if active_event and next_event:
            update_next_event()
        
        # Maint debug logging
        logger.debug(f"Maint data -- playoff_data: {playoff_data}")
        logger.debug(f"Maint data -- active_event: {active_event}")

        # Sleep at end
        time.sleep(int(get_env('MAINT_INTERVAL_MIN')) * 60)


def bhb_main_loop():

    global next_event
    
    skip = False
    logger.info("Starting main event loop...")

    while True:

        next_event = get_next_event()

        if not next_event or next_event.meta['event_status'] == 'done':
            logger.warning(f"No next event found.... exiting")
            break

        if active_event:

            # Catch when active_event & next_event are same (next_event not updated in time)
            try:
                if active_event.id == next_event.id:
                    logger.info(f"active_event==next_event; active_event: {active_event.id} -- next_event: {next_event.id}, sleeping 30")
                    skip = True
                    time.sleep(30)
                else:
                    # Set prev_reddit_id on next_event w/ reddit_id of active_event
                    update_next_event()

            except AttributeError:
                pass

        current_time = get_timestamp_from_datetime()
        seconds_till_event = get_timestamp_from_datetime(dt=next_event.start) - current_time

        # If skip, next_event was same as active_event, skip rest of loop and grab next_event again
        if skip:
            skip = False

        # Time to do next_event
        elif seconds_till_event <= 0 and next_event.meta['event_type']:
            
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
                break


def run_bhb():

    # Initialize globals
    global playoff_data
    global next_event
    global active_event

    playoff_data = None
    next_event = None
    active_event = None

    # Create maint thread, and start
    maint_thread = threading.Thread(target=do_maint_tasks)
    maint_thread.start()

    # Create main run BHB thread, and start
    run_bhb_thread = threading.Thread(target=bhb_main_loop)
    run_bhb_thread.start()
