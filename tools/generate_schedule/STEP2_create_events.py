import copy

from big_honey_bot.helpers import (
    get_dict_from_json_file,
    write_dict_to_json_file,
    get_datetime_from_timestamp,
    get_timestamp_from_datetime,
    get_str_from_datetime,
    get_str_from_timestamp,
    description_tags,
    platform_hr_min_fmt
)
from big_honey_bot.config.main import setup
from big_honey_bot.threads.static.lookups import team_lookup
from big_honey_bot.threads.static.templates import Game
from tools.models import GameEvent


IN_PLAYOFFS = True
PRE_FILE_NAME = 'schedule_scrape_output.json'
POST_FILE_NAME = 'all_events.json'


def add_desc_placeholders(in_desc):
    return  f"{in_desc}\n\n&nbsp;\n\n" \
            f"{description_tags['lineup_injury_odds']}\n\n&nbsp;\n\n" \
            f"{description_tags['referees']}\n"


def create_pre_game_event(schedule):
    
    new_schedule = {}

    for game_ts, event_data in schedule.items():

        event_dt = get_datetime_from_timestamp(ts=game_ts, add_tz=True).replace(hour=int(setup['pre_game_post_hour']), minute=int(0))
        event_ts = str(get_timestamp_from_datetime(dt=event_dt))
        start_time = get_datetime_from_timestamp(ts=event_ts, to_tz=True, tz=setup['timezone'])

        game_time = get_str_from_timestamp(ts=game_ts, fmt=platform_hr_min_fmt, to_tz=True)
        description = Game.pre_game_body(
            time=game_time,
            tz=setup['timezone_short'],
            url=f"https://dateful.com/time-zone-converter?t={game_time}&tz={setup['location']}&",
            arena=event_data['arena'],
            city=event_data['city'],
            tv=event_data['tv'],
            radio=event_data['radio'],
            previews=f"[Game Notes](https://www.nba.com/gamenotes/{setup['team'].lower()}.pdf), [nba.com]({nba_link('preview', event_data['nba_id'])})"
        )
        description = add_desc_placeholders(description)

        new_event = GameEvent(
            event_data=event_data,
            event_type='pre',
            start=start_time,
            game_ts=game_ts,
            description=description,
            in_playoffs=IN_PLAYOFFS
        )

        new_schedule.update({event_ts: new_event.as_dict_for_google_cal()})

    return new_schedule


def create_game_event(schedule):
    
    new_schedule = {}

    for game_ts, event_data in schedule.items():
        
        event_ts = str(int(game_ts) - 60*60)     # Offset time 1 hour prior to game start time
        start_time = get_datetime_from_timestamp(ts=event_ts, to_tz=True, tz=setup['timezone'])


        # Format a few times based on popular time zones in the subreddit
        time_fmt = f'{platform_hr_min_fmt} %p %Z'
        game_dt = get_datetime_from_timestamp(ts=game_ts, to_tz=True)
        time_table = {
            "Kitchener": 'US/Eastern',
            "Denver": 'US/Mountain',
            "Seattle": 'US/Pacific',
            "Sombor": 'Europe/Belgrade',
            "Sydney": 'Australia/Sydney'
        }

        times = []
        for loc, tz in time_table.items():
            times.append(f"{get_str_from_datetime(dt=game_dt, fmt=time_fmt, to_tz=True, tz=tz)} - {loc}")

        # subreddit links using team lookup dict
        top_sub = team_lookup[event_data['opponent']][0]
        bot_sub = team_lookup[setup['team']][0]

        # Top "General Information" table
        description = Game.gen_info_table(
            times=times,
            tv=event_data['tv'],
            radio=event_data['radio'],
            nba_links=[nba_link('box', event_data['nba_id']), nba_link('shot', event_data['nba_id'])],
            espn_links=[espn_link('boxscore', event_data['espn_id']), espn_link('game', event_data['espn_id'])],
            arena=event_data['arena'],
            city=event_data['city'],
            subreddits=[top_sub, bot_sub])
        description = add_desc_placeholders(description)

        new_event = GameEvent(
            event_data=event_data,
            event_type='game',
            start=start_time,
            game_ts=game_ts,
            description=description,
            in_playoffs=IN_PLAYOFFS
        )

        new_schedule.update({event_ts: new_event.as_dict_for_google_cal()})

    return new_schedule


def post_game_edit(schedule):
    
    new_schedule = {}

    for game_ts, event_data in schedule.items():

        start_time = get_datetime_from_timestamp(ts=game_ts, to_tz=True, tz=setup['timezone'])
        description = "TBD"
        
        new_event = GameEvent(
            event_data=event_data,
            event_type='post',
            start=start_time,
            game_ts=game_ts,
            description=description,
            in_playoffs=IN_PLAYOFFS
        )

        # Custom post game titles; see threads.post_game.post_game.format_post for details
        meta = {
            "win": "",
            "lose": ""
        }

        new_event.add_meta(**meta)

        new_schedule.update({game_ts: new_event.as_dict_for_google_cal()})

    return new_schedule


def espn_link(link_type, espn_id):
    """types: game, boxscore, recap"""

    return f"https://www.espn.com/nba/{link_type}/_/gameId/{espn_id}"


def nba_link(link_type, nba_id):
    """types: none is boxscore, shotchart"""

    link = f"https://www.nba.com/game/{nba_id}"
    if link_type == 'shot':
        link += '/game-charts#game-charts'
    elif link_type == 'box':
        link += '/box-score#box-score'

    return link


if __name__ == '__main__':

    raw_schedule = get_dict_from_json_file(PRE_FILE_NAME)

    schedule_pre_game = create_pre_game_event(copy.deepcopy(raw_schedule))
    schedule_game = create_game_event(copy.deepcopy(raw_schedule))
    schedule_post_game = post_game_edit(copy.deepcopy(raw_schedule))

    ordered_schedule = {}
    ordered_schedule.update(schedule_pre_game)
    ordered_schedule.update(schedule_game)
    ordered_schedule.update(schedule_post_game)

    write_dict_to_json_file(POST_FILE_NAME, dict(sorted(ordered_schedule.items())))
