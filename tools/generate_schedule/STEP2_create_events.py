from datetime import datetime
import os
import copy
import json
import pytz

from config import setup
from data.static.data import team_lookup


TIMEZONE = setup['timezone']


def post_game_edit(schedule):
    """Modify current event to add in some missing key, value pairs for other scripts to use."""

    new_schedule = copy.deepcopy(schedule)

    for utc, event in schedule.items():

        new_schedule[utc]['utc'] = utc
        new_schedule[utc]['event_type'] = 'post'

        game_time = datetime.fromtimestamp(int(utc))
        loc_str = datetime.strftime(game_time.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))
        date_str = datetime.strftime(game_time.astimezone(tz=pytz.timezone(TIMEZONE)), format("%b %#d, %Y"))

        new_schedule[utc]['game_start'] = loc_str
        new_schedule[utc]['post_date'] = date_str
        new_schedule[utc]['post_time'] = event['game_start']

        new_schedule[utc]['opp_abv'] = team_lookup[event['opponent']][1]

    return new_schedule


def game_edit(schedule):
    """Add game thread events given a schedule of game events. Decrease UTC time."""

    new_schedule = copy.deepcopy(schedule)

    for old_utc, event in schedule.items():

        new_utc = str(int(old_utc) - 60*60)
        post_date = datetime.fromtimestamp(int(new_utc))
        loc_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))

        new_schedule[new_utc] = event
        new_schedule[new_utc]['event_type'] = 'game'
        new_schedule[new_utc]['post_time'] = loc_str

    return new_schedule


def pre_game_edit(schedule):
    """Add pre game event based on 8AM MT post time"""

    new_schedule = copy.deepcopy(schedule)

    for utc, event in schedule.items():

        # Avoid adding duplicates
        if event['event_type'] == 'post':

            game_day = datetime.fromtimestamp(int(utc), tz=pytz.timezone(TIMEZONE))
            game_day = game_day.replace(hour=8, minute=0)
            new_utc = f"{datetime.timestamp(game_day):.0f}"

            post_date = datetime.fromtimestamp(int(new_utc))
            loc_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))

            new_schedule[new_utc] = event
            new_schedule[new_utc]['type'] = 'pre'
            new_schedule[new_utc]['post_time'] = loc_str

    return new_schedule


if __name__ == '__main__':

    with open('../json_output/schedule_scrape_output.json', 'r') as f:
        raw_schedule = json.load(f)

    schedule1 = post_game_edit(raw_schedule)
    schedule2 = game_edit(schedule1)
    schedule3 = pre_game_edit(schedule2)
    ordered_schedule = dict()

    for event, details in sorted(schedule3.items()):
        ordered_schedule[event] = details

    try:
        os.mkdir('../json_output')
    except FileExistsError:
        pass

    with open('../json_output/all_events.json', 'w') as f:
        json.dump(ordered_schedule, f, indent=4)
