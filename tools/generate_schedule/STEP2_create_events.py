import copy

from big_honey_bot.helpers import (
    create_hash,
    get_dict_from_json_file,
    write_dict_to_json_file,
    get_datetime_from_timestamp,
    get_timestamp_from_datetime,
    get_str_from_datetime,
    description_tags,
    platform_hr_min_fmt
)
from big_honey_bot.config.main import setup
from big_honey_bot.threads.static.lookups import team_lookup
from big_honey_bot.threads.static.templates import Game
from big_honey_bot.threads.static.headlines import gt_placeholders


IN_PLAYOFFS = False
PRE_FILE_NAME = 'schedule_scrape_output.json'
POST_FILE_NAME = 'all_events.json'


def create_headline(event_type_str, event_data):
    home_away = "vs." if event_data['home_away'] == 'home' else '@'
    if event_type_str == 'POST GAME THREAD':
        return f"POST GAME THREAD: {setup['team']} {home_away} {event_data['opponent']}"
    else:
        if IN_PLAYOFFS:
            return f"{event_type_str}: {gt_placeholders['playoff_series']} - {gt_placeholders['playoff_teams']} | {gt_placeholders['date_and_time']}"
        else:
            return f"{event_type_str}: {setup['team']} {gt_placeholders['our_record']} {home_away} {event_data['opponent']} {gt_placeholders['opp_record']} | {gt_placeholders['date_and_time']}"


def create_pre_game_event(schedule):
    new_schedule = {}

    for old_utc, event_data in schedule.items():

        post_time = setup['pre_game_post_time'].split(':')
        game_day = get_datetime_from_timestamp(ts=old_utc, add_tz=True)
        game_day = game_day.replace(hour=int(post_time[0]), minute=int(post_time[1]))   # Offsets time based on config's pre_game_post_time
        new_utc = str(get_timestamp_from_datetime(dt=game_day))

        new_schedule[new_utc] = {}
        new_schedule[new_utc]['meta'] = {}
        new_schedule[new_utc]['meta'] = event_data
        new_schedule[new_utc]['meta']['game_utc'] = int(old_utc)
        new_schedule[new_utc]['meta']['event_type'] = 'pre'

        post_date = get_datetime_from_timestamp(ts=new_utc)
        loc_time_str = get_str_from_datetime(dt=post_date, fmt=f'{platform_hr_min_fmt} %p', add_tz=True)
        new_schedule[new_utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[new_utc]['start'] = {}
        new_schedule[new_utc]['start']['dateTime'] = get_datetime_from_timestamp(ts=new_utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['start']['timeZone'] = setup['timezone']
        new_schedule[new_utc]['end'] = {}
        new_schedule[new_utc]['end']['dateTime'] = get_datetime_from_timestamp(ts=new_utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['end']['timeZone'] = setup['timezone']
        new_schedule[new_utc]['summary'] = create_headline('GDT', event_data)

        game_time = " ".join(event_data['game_start'].split(" ")[1:])
        new_schedule[new_utc]['description'] = Game.pre_game_body(
            time=game_time,
            tz=setup['timezone_short'],
            url=f"https://dateful.com/time-zone-converter?t={game_time}&tz={setup['location']}&",
            arena=event_data['arena'],
            city=event_data['city'],
            tv=event_data['tv'],
            radio=event_data['radio'],
            previews=f"[Game Notes](https://www.nba.com/gamenotes/{setup['team'].lower()}.pdf), [nba.com]({nba_link('preview', event_data['nba_id'])})"
        )
        new_schedule[new_utc]['description'] = f"{new_schedule[new_utc]['description']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['starters']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['injuries']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['odds']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['referees']}\n"

        new_schedule[new_utc]['location'] = f"{event_data['arena']} - {event_data['city']}"

        new_schedule[new_utc]['meta']['title_hash'] = create_hash(new_schedule[new_utc]['summary'])
        new_schedule[new_utc]['meta']['body_hash'] = create_hash(new_schedule[new_utc]['description'])

    return new_schedule


def create_game_event(schedule):
    new_schedule = {}

    for old_utc, event_data in schedule.items():

        new_utc = str(int(old_utc) - 60*60)     # Offset time 1 hour prior to game start time
        post_date = get_datetime_from_timestamp(ts=new_utc)
        loc_time_str = get_str_from_datetime(dt=post_date, fmt=f'{platform_hr_min_fmt} %p', add_tz=True)

        new_schedule[new_utc] = {}
        new_schedule[new_utc]['meta'] = event_data
        new_schedule[new_utc]['meta']['game_utc'] = int(old_utc)
        new_schedule[new_utc]['meta']['event_type'] = 'game'
        new_schedule[new_utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[new_utc]['start'] = {}
        new_schedule[new_utc]['start']['dateTime'] = get_datetime_from_timestamp(ts=new_utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['start']['timeZone'] = setup['timezone']
        new_schedule[new_utc]['end'] = {}
        new_schedule[new_utc]['end']['dateTime'] = get_datetime_from_timestamp(ts=new_utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['end']['timeZone'] = setup['timezone']
        new_schedule[new_utc]['location'] = f"{event_data['arena']} - {event_data['city']}"
        new_schedule[new_utc]['summary'] = create_headline('GAME THREAD', event_data)

        # Format a few times based on popular time zones in the subreddit
        time_fmt = f'{platform_hr_min_fmt} %p %Z'
        dt_obj = get_datetime_from_timestamp(ts=old_utc) 
        time_table = {
            "Kitchener": 'US/Eastern',
            "Denver": 'US/Mountain',
            "Seattle": 'US/Pacific',
            "Sombor": 'Europe/Belgrade',
            "Sydney": 'Australia/Sydney'
        }

        times = []
        for loc, tz in time_table.items():
            times.append(f"{get_str_from_datetime(dt=dt_obj, fmt=time_fmt, add_tz=True, tz=tz)} - {loc}")

        # subreddit links using team lookup dict
        top_sub = team_lookup[event_data['opponent']][0]
        bot_sub = team_lookup[setup['team']][0]

        # Top "General Information" table
        new_schedule[new_utc]['description'] = Game.gen_info_table(
            times=times,
            tv=event_data['tv'],
            radio=event_data['radio'],
            nba_links=[nba_link('box', event_data['nba_id']), nba_link('shot', event_data['nba_id'])],
            espn_links=[espn_link('boxscore', event_data['espn_id']), espn_link('game', event_data['espn_id'])],
            arena=event_data['arena'],
            city=event_data['city'],
            subreddits=[top_sub, bot_sub])
        new_schedule[new_utc]['description'] = f"{new_schedule[new_utc]['description']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['starters']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['injuries']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['odds']}\n\n&nbsp;\n\n" \
                                               f"{description_tags['referees']}\n"
        new_schedule[new_utc]['meta']['title_hash'] = create_hash(new_schedule[new_utc]['summary'])
        new_schedule[new_utc]['meta']['body_hash'] = create_hash(new_schedule[new_utc]['description'])

    return new_schedule


def post_game_edit(schedule):
    new_schedule = {}

    for utc, event_data in schedule.items():
        new_schedule[utc] = {}
        new_schedule[utc]['meta'] = event_data
        new_schedule[utc]['meta']['game_utc'] = int(utc)
        new_schedule[utc]['meta']['event_type'] = 'post'

        game_time = get_datetime_from_timestamp(ts=utc)
        loc_time_str = get_str_from_datetime(dt=game_time, fmt=f'{platform_hr_min_fmt} %p', add_tz=True)
        new_schedule[utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[utc]['start'] = {}
        new_schedule[utc]['start']['dateTime'] = get_datetime_from_timestamp(ts=utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[utc]['start']['timeZone'] = setup['timezone']
        new_schedule[utc]['end'] = {}
        new_schedule[utc]['end']['dateTime'] = get_datetime_from_timestamp(ts=utc, add_tz=True, tz=setup['timezone']).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[utc]['end']['timeZone'] = setup['timezone']
        new_schedule[utc]['location'] = f"{event_data['arena']} - {event_data['city']}"
        new_schedule[utc]['summary'] = create_headline('POST GAME THREAD', event_data)
        new_schedule[utc]['description'] = "TBD"

        # Custom post game titles; see threads.post_game.post_game.format_post for details
        new_schedule[utc]['meta']['win'] = ""
        new_schedule[utc]['meta']['lose'] = ""

        new_schedule[utc]['meta']['title_hash'] = create_hash(new_schedule[utc]['summary'])
        new_schedule[utc]['meta']['body_hash'] = create_hash(new_schedule[utc]['description'])

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
