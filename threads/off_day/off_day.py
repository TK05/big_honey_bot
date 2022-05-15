import os
from datetime import datetime
import requests
import pytz

from bots.thread_handler_bot import new_thread
from config import setup
from tools.toolkit import description_tags


def generate_thread_body(event=None):
    """Generates off day thread body based on that days games (from ESPN). Replaces placeholder tags with
    this generated data.

    :param event: Event to generate thread body for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """
    req = requests.get('https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=basketball&league=nba&region=us&lang=en&contentorigin=espn&buyWindow=1m&showAirings=buy,live,replay&showZipLookup=true&tz=America/New_York').json()
    games = sorted(req['sports'][0]['leagues'][0]['events'], key=lambda i: i['id'])

    body = f"|Today's Games||||\n" \
           f"|:--|:--|:--|:--|\n"

    for game in games:
        time = datetime.strptime(game['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
        time_local = f"{datetime.strftime(time.astimezone(pytz.timezone(setup['timezone'])), format('%#I:%M %p %Z'))}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{datetime.strftime(time.astimezone(pytz.timezone(setup['timezone'])), format('%#I:%M %p'))}" \
                    f"&tz={setup['location']}&"
        time_fmt = f"[{time_local}]({time_link})"
        teams = f"{game['name']}"
        series = f"{game['note']}, {game['seriesSummary']}"
        nba_link = f"[ESPN](https://www.espn.com/nba/game?gameId={game['id']})"
        body += f"|{teams}|{time_fmt}|{series}|{nba_link}|\n"

    if len(games) == 0:
        body = "No games scheduled today"

    if not event:
        print(body)
    else:
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


if __name__ == "__main__":
    generate_thread_body()
