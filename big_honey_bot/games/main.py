import logging

from big_honey_bot.helpers import timestamps_are_same_day
from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_pname_fname_str
from big_honey_bot.games.helpers import get_next_game
from big_honey_bot.events.main import get_next_event, find_events_by_meta


logger = logging.getLogger(get_pname_fname_str(__file__))


async def validate_next_game():

    # early exit if not next_event.event_type == pre
    if next_event.meta['event_type'] != 'pre':
        return

    try:
        next_game_dict = get_next_game()
    except ValueError:
        # skip validation if we fail getting the next game
        return

    next_event = await get_next_event()
    next_game_ts = int(next_game_dict['start_ts'])
    next_event_ts = int(next_event.meta['game_utc'])

    # if found next game matches next event, do nothing
    if next_game_ts == next_event_ts:
        return

    # if found next game and next event are on a different day, adjust
    #   this is possible because of the early exit != 'pre' so we should only get
    #   here when the next event is a game but the next game found doesn't match
    elif not timestamps_are_same_day(next_event_ts, next_event_ts, setup['timezone']):
        # need to possibly search for this game on a diff date and update that
        # may also need to create events between today and next game if days are unexpectedly empty
        pass

    # found next game and next game are on same day, but different times. adjust
    #   upcoming pre/game/post events to reflect correct game time
    else:
        events_to_update = await find_events_by_meta(nba_id=next_game_dict)

        for event in events_to_update:
            # change event start & end times
            # change event.meta game_utc, game_start
            # maybe just replace meta w/ info from new game
            pass
    