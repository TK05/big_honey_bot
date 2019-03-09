from datetime import datetime
import os
import copy
import json
import pytz
from data.static.data import Data


TIMEZONE = os.environ['TIMEZONE']


def post_game_edit(schedule):
    """Modify current event to add in some missing key, value pairs for other scripts to use."""

    new_schedule = copy.deepcopy(schedule)

    for utc, event in schedule.items():

        new_schedule[utc]['UTC'] = utc
        new_schedule[utc]['Type'] = 'post'

        if event['Location'] == 'home':
            new_schedule[utc]['Home_Away_Fix'] = 'vs.'
        else:
            new_schedule[utc]['Home_Away_Fix'] = '@'

        game_time = datetime.fromtimestamp(int(utc))
        loc_str = datetime.strftime(game_time.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))
        # TODO: Double check time fmt based on platform requirements (- or #)
        date_str = datetime.strftime(game_time.astimezone(tz=pytz.timezone(TIMEZONE)), format("%b %#d, %Y"))

        new_schedule[utc]['Time'] = loc_str
        new_schedule[utc]['Date_Str'] = date_str
        new_schedule[utc]['Post_Date'] = event['Date']

        opp_abv = Data.team_lookup()
        new_schedule[utc]['Opp_Abv'] = opp_abv[event['Opponent']][1]

    return new_schedule


def game_edit(schedule):
    """Add game thread events given a schedule of game events. Decrease UTC time."""

    new_schedule = copy.deepcopy(schedule)

    for old_utc, event in schedule.items():

        new_utc = str(int(old_utc) - 60*60)
        post_date = datetime.fromtimestamp(int(new_utc))
        loc_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))

        new_schedule[new_utc] = event
        new_schedule[new_utc]['Type'] = 'game'

        new_schedule[new_utc]['Post_Date'] = loc_str

    return new_schedule


def pre_game_edit(schedule):
    """Add pre game event based on 8AM MT post time"""

    new_schedule = copy.deepcopy(schedule)

    for utc, event in schedule.items():

        # Avoid adding duplicates
        if event['Type'] == 'post':

            game_day = datetime.fromtimestamp(int(utc), tz=pytz.timezone(TIMEZONE))
            game_day = game_day.replace(hour=8, minute=0)
            new_utc = f"{datetime.timestamp(game_day):.0f}"

            post_date = datetime.fromtimestamp(int(new_utc))
            loc_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))

            new_schedule[new_utc] = event
            new_schedule[new_utc]['Type'] = 'pre'
            new_schedule[new_utc]['Post_Date'] = loc_str

    return new_schedule


if __name__ == '__main__':

    with open('../data/schedule_scrape_output.json', 'r') as f:
        raw_schedule = json.load(f)

    schedule1 = post_game_edit(raw_schedule)
    schedule2 = game_edit(schedule1)
    schedule3 = pre_game_edit(schedule2)

    with open('../data/all_events.json', 'w') as f:
        json.dump(schedule3, f, indent=4)
