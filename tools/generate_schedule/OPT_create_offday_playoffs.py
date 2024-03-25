from datetime import date, timedelta

from big_honey_bot.helpers import (
    create_hash,
    write_dict_to_json_file,
    get_dict_from_json_file,
    get_datetime,
    get_str_from_datetime,
    get_datetime_from_str,
    description_tags,
    platform_hr_min_fmt,
    platform_day_fmt
)
from big_honey_bot.events.main import get_all_events_with_meta
from big_honey_bot.config.main import setup
from tools.generate_schedule.STEP3_create_calendar import update_calendar


IN_SEASON_OFFDAYS = True
IN_PLAYOFFS = False
FILE_NAME_IN = 'all_events.json'
FILE_NAME_OUT = 'off_day_events.json'


def create_schedule(start, end, playoffs=True, count_down=False):
    now = get_datetime(add_tz=True)
    pgpt = setup['pre_game_post_time'].split(':')
    new_schedule = {}
    for d in range((end - now.date()).days):
        post_date = now + timedelta(days=d+1)
        post_time_dict = {
            "year": post_date.year,
            "month": post_date.month,
            "day": post_date.day,
            "hour": int(pgpt[0]),
            "minute": int(pgpt[1])
        }
        post_time = get_datetime(dt=post_time_dict, add_tz=True)
        post_stamp = int(post_time.timestamp())

        new_schedule[post_stamp] = {}
        new_schedule[post_stamp]['meta'] = {}
        new_schedule[post_stamp]['meta']['event_type'] = 'off'
        loc_time_str = get_str_from_datetime(dt=post_time, fmt=f'{platform_hr_min_fmt} %p')
        new_schedule[post_stamp]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[post_stamp]['start'] = {}
        new_schedule[post_stamp]['start']['dateTime'] = post_time.strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['start']['timeZone'] = setup['timezone']
        new_schedule[post_stamp]['end'] = {}
        new_schedule[post_stamp]['end']['dateTime'] = (post_time + timedelta(seconds=61)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['end']['timeZone'] = setup['timezone']
        new_schedule[post_stamp]['location'] = 'Parts Unknown'

        if count_down:
            delta_days = (end - post_date.date()).days
        else:
            delta_days = (post_date.date() - start).days + 1

        if post_date.weekday() == 4:
            if playoffs:
                headline = f"Playoffs Day {delta_days} - Free Talk Friday | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
            elif count_down:
                headline = f"{delta_days} Days Until Tip-Off - Free Talk Friday | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
            else:
                headline = f"Nuggets Reign - Day {delta_days} | Free Talk Friday | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
        else:
            if playoffs:
                headline = f"Playoffs Day {delta_days} - Discussion Thread | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
            elif count_down:
                headline = f"{delta_days} Days Until Tip-Off - Off-Season Discussion Thread | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
            else:
                headline = f"Nuggets Reign - Day {delta_days} | Discussion Thread | {post_date.strftime(f'%b {platform_day_fmt}, %Y')}"
        new_schedule[post_stamp]['summary'] = headline
        new_schedule[post_stamp]['description'] = f"{description_tags['daily_games']}"

        new_schedule[post_stamp]['meta']['title_hash'] = create_hash(new_schedule[post_stamp]['summary'])
        new_schedule[post_stamp]['meta']['body_hash'] = create_hash(new_schedule[post_stamp]['description'])

    existing_events = get_all_events_with_meta()
    for event in existing_events:
        if event.meta['event_type'] == 'pre':
            try:
                del(new_schedule[int(event.start.timestamp())])
            except KeyError:
                pass

    return new_schedule


def create_in_season_schedule(curr_sch):
    days_with = []
    days_without = []

    for utc in curr_sch.keys():
        dt = get_datetime_from_str(dt_str=curr_sch[utc]['meta']['game_start'], fmt="%m/%d/%y %I:%M %p")
        days_with.append(dt.date())

    for i, day in enumerate(days_with[:-1]):
        diff = (days_with[i+1] - day).days
        if diff > 0:
            for n in range(1, diff):
                days_without.append(day + timedelta(days=n))

    pgpt = setup['pre_game_post_time'].split(':')
    new_schedule = {}

    for d in days_without:
        post_time_dict = {
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "hour": int(pgpt[0]),
            "minute": int(pgpt[1])
        }
        post_time = get_datetime(dt=post_time_dict, add_tz=True)
        post_stamp = int(post_time.timestamp())

        new_schedule[post_stamp] = {}
        new_schedule[post_stamp]['meta'] = {}
        new_schedule[post_stamp]['meta']['event_type'] = 'off'
        loc_time_str = get_str_from_datetime(dt=post_time, fmt=f'{platform_hr_min_fmt} %p')
        new_schedule[post_stamp]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[post_stamp]['start'] = {}
        new_schedule[post_stamp]['start']['dateTime'] = post_time.strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['start']['timeZone'] = setup['timezone']
        new_schedule[post_stamp]['end'] = {}
        new_schedule[post_stamp]['end']['dateTime'] = (post_time + timedelta(seconds=61)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['end']['timeZone'] = setup['timezone']
        new_schedule[post_stamp]['location'] = 'Parts Unknown'

        if d.weekday() == 4:
            headline = f"Free Talk Friday | {d.strftime(f'%b {platform_day_fmt}, %Y')}"
        else:
            headline = f"Off-Day Discussion Thread | {d.strftime(f'%b {platform_day_fmt}, %Y')}"

        new_schedule[post_stamp]['summary'] = headline
        new_schedule[post_stamp]['description'] = f"{description_tags['daily_games']}"

        new_schedule[post_stamp]['meta']['title_hash'] = create_hash(new_schedule[post_stamp]['summary'])
        new_schedule[post_stamp]['meta']['body_hash'] = create_hash(new_schedule[post_stamp]['description'])

    return new_schedule


if __name__ == '__main__':
    if IN_SEASON_OFFDAYS:
        raw_schedule = get_dict_from_json_file(FILE_NAME_IN)
        schedule = create_in_season_schedule(raw_schedule)
        update_calendar(schedule)
    elif IN_PLAYOFFS:
        start_date = date(2023, 4, 15)
        end_date = date(2023, 6, 18)

        schedule = create_schedule(start_date, end_date)
        update_calendar(schedule)

        write_dict_to_json_file(FILE_NAME_OUT, dict(sorted(schedule.items())))
    else:
        start_date = date(2023, 10, 10)
        end_date = date(2023, 10, 24)

        schedule = create_schedule(start_date, end_date, playoffs=False, count_down=True)
        update_calendar(schedule)

        write_dict_to_json_file(FILE_NAME_OUT, dict(sorted(schedule.items())))
