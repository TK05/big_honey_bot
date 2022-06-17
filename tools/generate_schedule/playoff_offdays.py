import os
import json
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from events.manager import get_all_events_with_meta
from config import setup
from tools.toolkit import description_tags, create_hash
from tools.generate_schedule.STEP3_create_calendar import update_calendar


TIMEZONE = setup['timezone']


def create_schedule(start, end, playoffs=True):
    now = datetime.now(tz=ZoneInfo(TIMEZONE))
    pgpt = setup['pre_game_post_time'].split(':')
    new_schedule = {}
    for d in range((end - now.date()).days):
        post_date = now + timedelta(days=d+1)
        post_time = datetime(
            year=post_date.year,
            month=post_date.month,
            day=post_date.day,
            hour=int(pgpt[0]),
            minute=int(pgpt[1]),
            tzinfo=ZoneInfo(TIMEZONE)
        )
        post_stamp = int(post_time.timestamp())

        new_schedule[post_stamp] = {}
        new_schedule[post_stamp]['meta'] = {}
        new_schedule[post_stamp]['meta']['event_type'] = 'off'
        loc_time_str = datetime.strftime(post_time, format('%#I:%M %p'))
        new_schedule[post_stamp]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[post_stamp]['start'] = {}
        new_schedule[post_stamp]['start']['dateTime'] = post_time.strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['start']['timeZone'] = TIMEZONE
        new_schedule[post_stamp]['end'] = {}
        new_schedule[post_stamp]['end']['dateTime'] = (post_time + timedelta(seconds=61)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[post_stamp]['end']['timeZone'] = TIMEZONE
        new_schedule[post_stamp]['location'] = 'Parts Unknown'

        delta = post_date.date() - start
        if post_date.weekday() == 4:
            if playoffs:
                headline = f"Playoffs Day {delta.days + 1} - Free Talk Friday | {post_date.strftime('%b %#d, %Y')}"
            else:
                headline = f"Off-Season Day {delta.days + 1} - Free Talk Friday | {post_date.strftime('%b %#d, %Y')}"
        else:
            if playoffs:
                headline = f"Playoffs Day {delta.days + 1} - Discussion Thread | {post_date.strftime('%b %#d, %Y')}"
            else:
                headline = f"Off-Season Day {delta.days + 1} - Discussion Thread | {post_date.strftime('%b %#d, %Y')}"
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


if __name__ == '__main__':
    start_date = date(2022, 6, 17)
    end_date = date(2022, 10, 28)

    schedule = create_schedule(start_date, end_date, playoffs=False)
    update_calendar(schedule)

    try:
        os.mkdir('../json_output')
    except FileExistsError:
        pass

    with open('../json_output/off_day_events.json', 'w') as f:
        json.dump(dict(sorted(schedule.items())), f, indent=4)
