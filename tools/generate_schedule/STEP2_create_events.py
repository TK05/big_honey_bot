from datetime import datetime
import os
import copy
import json
import pytz

from config import setup
from data.static.data import team_lookup
from threads.static.templates import Game


TIMEZONE = setup['timezone']


def create_pre_game_event(schedule):
    new_schedule = {}

    for old_utc, event_data in schedule.items():

        post_time = setup['pre_game_post_time'].split(':')
        game_day = datetime.fromtimestamp(int(old_utc), tz=pytz.timezone(TIMEZONE))
        game_day = game_day.replace(hour=int(post_time[0]), minute=int(post_time[1]))   # Offsets time based on config's pre_game_post_time
        new_utc = f"{datetime.timestamp(game_day):.0f}"

        new_schedule[new_utc] = {}
        new_schedule[new_utc]['meta'] = {}
        new_schedule[new_utc]['meta'] = event_data
        new_schedule[new_utc]['meta']['event_type'] = 'pre'

        post_date = datetime.fromtimestamp(int(new_utc))
        loc_time_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))
        new_schedule[new_utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[new_utc]['start'] = {}
        new_schedule[new_utc]['start']['dateTime'] = datetime.fromtimestamp(int(new_utc), tz=pytz.timezone(TIMEZONE)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['start']['timeZone'] = TIMEZONE

        home_away = "vs." if event_data['home_away'] == 'home' else '@'
        headline = f"GAME DAY THREAD: {setup['team']} {home_away} {event_data['opponent']}"
        new_schedule[new_utc]['summary'] = headline

        game_time = " ".join(event_data['game_start'].split(" ")[1:])
        new_schedule[new_utc]['description'] = Game.pre_game_body(
            time=game_time,
            tz=setup['timezone_short'],
            url=f"https://dateful.com/time-zone-converter?t={game_time}&tz={setup['location']}&",
            arena=event_data['arena'],
            city=event_data['city'],
            tv=event_data['tv'],
            radio=event_data['radio']
        )
        new_schedule[new_utc]['location'] = f"{event_data['arena']} - {event_data['city']}"

    return new_schedule


def create_game_event(schedule):
    new_schedule = {}

    for old_utc, event_data in schedule.items():

        new_utc = str(int(old_utc) - 60*60)     # Offset time 1 hour prior to game start time
        post_date = datetime.fromtimestamp(int(new_utc))
        loc_time_str = datetime.strftime(post_date.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))

        new_schedule[new_utc] = {}
        new_schedule[new_utc]['meta'] = event_data
        new_schedule[new_utc]['meta']['event_type'] = 'game'
        new_schedule[new_utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[new_utc]['start'] = {}
        new_schedule[new_utc]['start']['dateTime'] = datetime.fromtimestamp(int(new_utc), tz=pytz.timezone(TIMEZONE)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[new_utc]['start']['timeZone'] = TIMEZONE

        new_schedule[new_utc]['location'] = f"{event_data['arena']} - {event_data['city']}"

        home_away = "vs." if event_data['home_away'] == 'home' else '@'
        headline = f"GAME THREAD: {setup['team']} {home_away} {event_data['opponent']}"
        new_schedule[new_utc]['summary'] = headline

        # Format a few times based on popular time zones in the subreddit
        time_fmt = '%#I:%M %p %Z'
        dt_obj = datetime.fromtimestamp(int(old_utc))
        est_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Eastern')), format(time_fmt))} - Kitchener"
        mst_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Mountain')), format(time_fmt))} - Denver"
        pst_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('US/Pacific')), format(time_fmt))} - Seattle"
        cest_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('Europe/Belgrade')), format(time_fmt))} - Sombor"
        aedt_time = f"{datetime.strftime(dt_obj.astimezone(pytz.timezone('Australia/Sydney')), format(time_fmt))} - Sydney"

        # subreddit links using team lookup dict
        top_sub = team_lookup[event_data['opponent']][0]
        bot_sub = team_lookup[setup['team']][0]

        # Top "General Information" table
        new_schedule[new_utc]['description'] = Game.gen_info_table(
            times=[est_time, mst_time, pst_time, cest_time, aedt_time],
            tv=event_data['tv'],
            radio=event_data['radio'],
            nba_links=[nba_link('box', event_data['nba_id']), nba_link('shot', event_data['nba_id'])],
            espn_links=[espn_link('boxscore', event_data['espn_id']), espn_link('game', event_data['espn_id'])],
            arena=event_data['arena'],
            city=event_data['city'],
            subreddits=[top_sub, bot_sub])

    return new_schedule


def post_game_edit(schedule):
    new_schedule = {}

    for utc, event_data in schedule.items():
        new_schedule[utc] = {}
        new_schedule[utc]['meta'] = event_data
        new_schedule[utc]['meta']['event_type'] = 'post'

        game_time = datetime.fromtimestamp(int(utc))
        loc_time_str = datetime.strftime(game_time.astimezone(tz=pytz.timezone(TIMEZONE)), format('%#I:%M %p'))
        new_schedule[utc]['meta']['post_time'] = loc_time_str

        # Format Google Cal Event
        new_schedule[utc]['start'] = {}
        new_schedule[utc]['start']['dateTime'] = datetime.fromtimestamp(int(utc), tz=pytz.timezone(TIMEZONE)).strftime('%G-%m-%dT%H:%M:%S')
        new_schedule[utc]['start']['timeZone'] = TIMEZONE

        new_schedule[utc]['location'] = f"{event_data['arena']} - {event_data['city']}"

        home_away = "vs." if event_data['home_away'] == 'home' else '@'
        headline = f"POST GAME THREAD: {setup['team']} {home_away} {event_data['opponent']}"
        new_schedule[utc]['summary'] = headline
        new_schedule[utc]['description'] = "TBD"

    return new_schedule


def espn_link(link_type, espn_id):
    """types: game, boxscore, recap"""

    return f"https://www.espn.com/nba/{link_type}/_/gameId/{espn_id}"


def nba_link(link_type, nba_id):
    """types: none is boxscore, shotchart"""

    link = f"https://stats.nba.com/game/{nba_id}"
    if link_type == 'shot':
        link += '/shotchart'

    return link


if __name__ == '__main__':

    with open('../json_output/schedule_scrape_output.json', 'r') as f:
        raw_schedule = json.load(f)

    schedule_pre_game = create_pre_game_event(copy.deepcopy(raw_schedule))
    schedule_game = create_game_event(copy.deepcopy(raw_schedule))
    schedule_post_game = post_game_edit(copy.deepcopy(raw_schedule))

    ordered_schedule = {}
    ordered_schedule.update(schedule_pre_game)
    ordered_schedule.update(schedule_game)
    ordered_schedule.update(schedule_post_game)

    try:
        os.mkdir('../json_output')
    except FileExistsError:
        pass

    with open('../json_output/all_events.json', 'w') as f:
        json.dump(dict(sorted(ordered_schedule.items())), f, indent=4)
