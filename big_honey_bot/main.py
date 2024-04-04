import logging
import asyncio
from datetime import timedelta

from big_honey_bot.helpers import hash_match, get_datetime, get_timestamp_from_datetime, dyn_event_types
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.sidebar.helpers import update_sidebar
from big_honey_bot.playoffs.helpers import get_series_status
from big_honey_bot.threads.main import edit_thread, generate_thread_stats
from big_honey_bot.threads.game.thread import game_thread_handler
from big_honey_bot.threads.off_day.thread import off_day_thread_handler
from big_honey_bot.threads.post_game.thread import post_game_thread_handler
from big_honey_bot.events.main import get_event, get_next_event, update_event, get_previous_event, find_events_by_meta


logger = logging.getLogger(get_pname_fname_str(__file__))


async def do_event(event, update_only=False):

    global active_event

    if not hash_match(event.summary, event.meta['title_hash']):
        logger.info(f"Custom title detected: {event.summary}")
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Custom body detected, updated @ {event.updated.strftime('%b %d, %H:%M')}")

    if event.meta['event_type'] in ['pre', 'game']:
        await game_thread_handler(event, playoff_data, update_only)
    elif event.meta['event_type'] == 'post':
        await post_game_thread_handler(event, playoff_data)
    elif event.meta['event_type'] == 'off':
        await off_day_thread_handler(event, update_only)
    else:
        logger.error(f"Event type while do_event has no instructions -- type: {event.meta['event_type']} -- {event.summary}")

    # Add comment to new thread of thread stats for previous thread
    if get_env('THREAD_STATS') and not update_only:
        if not event.meta.get('prev_reddit_id'):
            logger.warn(f"Could not generate thread stats as event has no prev_reddit_id set -- {event.summary}")
        elif active_event and (active_event.meta['reddit_id'] != event.meta['prev_reddit_id']):
            logger.warn(f"Did not generate thread stats as active_event.reddit_id != event.prev_reddit_id -- " \
                        f"{active_event.meta['reddit_id']} != {event.meta['prev_reddit_id']}")
        else:
            try:
                prev_event = await find_events_by_meta({'reddit_id': event.meta['prev_reddit_id']})
                await generate_thread_stats(prev_event.meta['reddit_id'], prev_event.meta['event_type'], event.meta['reddit_id'])
            except Exception as e:
                logger.error(f"Error caught while generating thread stats: {e}")

    # End active event after posting (when update_only=False)
    if active_event and not update_only:
        await end_active_event()

    # Set this event to active and update event
    await update_event_and_set_to_active(event)


async def update_event_and_set_to_active(event):
    
    global active_event
    
    event.meta['event_status'] = 'active'
    await update_event(event)
    logger.info(f"Event updated and set to active: {event.id} - {event.summary}")
    active_event = event


async def check_active_event_for_manual_changes():
    
    global active_event

    if not active_event:
        logger.debug("active_event=None during check for manual changes")
        return
    
    event = await get_event(active_event.id)

    # Catch when event type manually set to done
    if event.meta['event_status'] == 'done':
        logger.info(f"Event manually set to done, ending active event: {event.id} - {event.summary}")
        active_event = None

    # Update post if event body has been changed since last check
    if not hash_match(event.body, event.meta['body_hash']):
        logger.info(f"Update to active event's body found, updated @ {event.updated.strftime('%b %d, %H:%M')}")
        
        # Update thread on reddit and then update event to store new hash
        await edit_thread(event)
        await update_event(event)

        logger.info(f"Post & Event updated after body changes: {event.id} - {event.summary}")
        
        active_event = event


async def update_next_event():

    global next_event

    if active_event:
        if not next_event.meta.get('prev_reddit_id') or next_event.meta['prev_reddit_id'] == "":
            next_event.meta['prev_reddit_id'] = active_event.meta['reddit_id']
            await update_event(next_event)
            logger.info(f"Updating next_event's prev_reddit_id with reddit_id of active_event -- prev_reddit_id: {next_event.meta['prev_reddit_id']}")
        elif next_event.meta['prev_reddit_id'] != active_event.meta['reddit_id']:
            next_event.meta['prev_reddit_id'] = active_event.meta['reddit_id']
            await update_event(next_event)
            logger.warn(f"next_event's prev_reddit_id did not match active_event's reddit_id, updating: prev_reddit_id {next_event.meta['prev_reddit_id']} ")


async def update_active_event():

    global active_event
    
    await check_active_event_for_manual_changes()

    if not active_event:
        logger.debug("active_event=None during update of active event")
        return

    # End active events 12 hours after start time
    if get_datetime(add_tz=True, tz=active_event.timezone) > (active_event.start + timedelta(hours=12)):
        logger.info(f"active_event active longer than 12 hours, setting to done")
        await end_active_event()

    elif active_event.meta['event_type'] in dyn_event_types:
        logger.info(f"Sending active event to thread handlers for updating, last updated: {active_event.updated}")
        await do_event(active_event, update_only=True)


async def end_active_event():
    
    global active_event

    if not active_event:
        return
    
    active_event.meta['event_status'] = 'done'
    await update_event(active_event)
    logger.info(f"Active event was set to done: {active_event.id} - {active_event.summary}")

    active_event = None


async def update_playoff_data():

    global playoff_data
    
    # Set playoff_data for global use
    if get_env('IN_PLAYOFFS'):
        playoff_round, playoff_game_num, playoff_record = await get_series_status()
        playoff_data = [playoff_round, playoff_game_num, playoff_record]
    else:
        playoff_data = None


async def check_if_prev_event_still_active():

    global active_event

    prev_event = await get_previous_event()

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
            await end_active_event()
    
        # Check current time and resume game watch if event.start < 3 hours ago
        elif get_datetime(add_tz=True, tz=prev_event.timezone) < (prev_event.start + timedelta(hours=3)):
            logger.info(f"Previous event was type={pe_type} & status={pe_status}, sending back to do_event")
            await do_event(prev_event)
        
        # If previous event is too old to game watch, then set to done
        else:
            logger.info(f"Previous event was type={pe_type} & status={pe_status} but skipping game check as start time is too old: {prev_event.start}")
            active_event = prev_event
            await end_active_event()

    # If previous event still active, set active_event
    if pe_status == 'active':
        logger.info(f"Previous event still active - {prev_event.summary}")
        active_event = prev_event
    
    # Else, previous event no longer active, unset active_event
    else:
        logger.info("Previous event is no longer active")
        active_event = None


async def do_maint_tasks(init_maint_task):
    # Maint tasks are things to do every maint_interval
    # IE: get playoff updates, update sidebar and  update active threads that have dynamic data.
    while True:
        logger.info("Maintanence tasks running...")

        # Async tasks
        t1 = asyncio.create_task(update_sidebar())
        t2 = asyncio.create_task(update_playoff_data())
        await t1
        await t2

        # Need to be done in order
        await check_if_prev_event_still_active()
        await update_active_event()

        # Continually check active_event.reddit_id==next_event.prev_reddit_id
        if active_event and next_event:
            await update_next_event()
        
        # Maint debug logging
        logger.debug(f"Maint data -- playoff_data: {playoff_data}")
        logger.debug(f"Maint data -- active_event: {active_event}")

        # Set maint_task_event to enable rest of tasks to run now
        init_maint_task.set()

        # Sleep at end
        await asyncio.sleep(int(get_env('MAINT_INTERVAL')))


async def bhb_main_loop(init_maint_task):

    # Wait for maint_task
    await init_maint_task.wait()

    global next_event
    
    skip = False
    logger.info("Starting main event loop...")

    while True:

        next_event = await get_next_event()

        if not next_event or next_event.meta['event_status'] == 'done':
            logger.warning(f"No next event found.... exiting")
            break

        if active_event:

            # Catch when active_event & next_event are same (next_event not updated in time)
            try:
                if active_event.id == next_event.id:
                    logger.info(f"active_event==next_event; active_event: {active_event.id} -- next_event: {next_event.id}, sleeping 30")
                    skip = True
                    await asyncio.sleep(30)
                else:
                    # Set prev_reddit_id on next_event w/ reddit_id of active_event
                    await update_next_event()

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
            await do_event(next_event)
            await asyncio.sleep(30)

        # Not time to do next_event but there is an active_event; check for updates to it
        elif active_event:
            
            # Sleep, then refresh active_event for any changes
            logger.debug(f"next_event: {next_event.summary} -- active_event: {active_event.summary}")
            await asyncio.sleep(30)
            await check_active_event_for_manual_changes()

        # Not time to do next_event and no active_event
        else:
            # Determine wait time
            try:   
                # next_event start time is near, sleep exact amount
                if seconds_till_event < 60:
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_event)}, sleeping {seconds_till_event}")
                    await asyncio.sleep(seconds_till_event)
                
                # next_event start time is far, sleep longer & update_sidebar after
                else:
                    wait_time = seconds_till_event if seconds_till_event < 3600 else 3600
                    logger.info(f"{next_event.summary} in {timedelta(seconds=seconds_till_event)}, sleeping {wait_time}")
                    await asyncio.sleep(wait_time)
            
            except ValueError:
                logger.error(f"seconds_till_event was negative, exiting")
                break


async def run_bhb():

    # Initialize globals
    global playoff_data
    global next_event
    global active_event

    playoff_data = None
    next_event = None
    active_event = None

    # Create event so we do an initial maint_tasks before starting
    init_maint_task = asyncio.Event()

    # Schedule maintenance tasks to run every MAINT_INTERVAL
    asyncio.create_task(do_maint_tasks(init_maint_task))

    # Run BHB continuously
    await bhb_main_loop(init_maint_task)
