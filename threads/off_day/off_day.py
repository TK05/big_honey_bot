import os
from datetime import datetime
import requests
import pytz

from bots.thread_handler_bot import new_thread
from config import setup
from tools.toolkit import description_tags


def generate_thread_body(event):
    """Generates off day thread body based on that days games. Replaces placeholder tags with
    this generated data.

    :param event: Event to generate thread body for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """
    req = requests.get('https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json').json()
    games = sorted(req['scoreboard']['games'], key=lambda i: i['gameId'])

    body = f"|Today's Games||||\n" \
           f"|:--|:--|:--|:--|\n"

    for game in games:
        time = datetime.strptime(game['gameTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
        time_local = f"{datetime.strftime(time.astimezone(pytz.timezone(setup['timezone'])), format('%#I:%M %p %Z'))}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{datetime.strftime(time.astimezone(pytz.timezone(setup['timezone'])), format('%#I:%M %p'))}" \
                    f"&tz={setup['location']}&"
        time_fmt = f"[{time_local}]({time_link})"
        teams = f"{game['awayTeam']['teamName']}({game['awayTeam']['seed']}) @ {game['homeTeam']['teamName']}({game['homeTeam']['seed']})"
        series = f"{game['seriesGameNumber']}, {game['seriesText']}"
        nba_link = f"[nba.com](https://www.nba.com/game/{game['gameId']})"
        body += f"|{teams}|{time_fmt}|{series}|{nba_link}|\n"

    if len(games) == 0:
        body = "No games scheduled today"

    event.body = event.body.replace(description_tags['daily_games'], f"{body}")


def off_day_thread_handler(event):
    """Generates thread title and body for event. Posts generated thread.

    :param event: Event to generate thread for
    :type event: gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    generate_thread_body(event)

    print(f"{os.path.basename(__file__)}: Created headline: {event.summary}")
    new_thread(event)
