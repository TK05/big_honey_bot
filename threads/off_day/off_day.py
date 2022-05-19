import os
from datetime import datetime
import requests
import pytz
from parsel import Selector

from bots.thread_handler_bot import new_thread
from config import setup
from tools.toolkit import description_tags
from data.static.data import lookup_by_loc


def generate_thread_body(event=None):
    """Generates off day thread body based on that days games (from ESPN). Replaces placeholder tags with
    this generated data.

    :param event: Event to generate thread body for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    response = requests.get('https://www.espn.com/nba/schedule').text
    response_selector = Selector(text=response)
    games_raw = response_selector.xpath('.//div[@class="mt3"]/div')

    body_rows = []
    games_today = []

    for game in games_raw:

        # skip when game complete
        if game.xpath('.//tr[@class="Table__TR Table__even"]/th[2]/div/text()').get() == "result":
            continue

        game_base = game.xpath('.//tr[@class="Table__TR Table__TR--sm Table__even"]/td')

        date_str = game.xpath('.//div[@class="Table__Title"]/text()').get().strip()
        time_str = game_base[2].xpath('.//a[@class="AnchorLink"]/text()').get()
        time = pytz.timezone('US/Eastern').localize(datetime.strptime(f"{date_str} {time_str}", '%A, %b %d, %Y %I:%M %p'))
        time_tz = time.astimezone(pytz.timezone(setup['timezone']))

        try:
            date_local = f"{datetime.strftime(time_tz, format('%-m/%-d'))}"
        except ValueError:
            date_local = f"{datetime.strftime(time_tz, format('%#m/%#d'))}"

        time_local = f"{datetime.strftime(time_tz, format('%#I:%M %p %Z'))}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{datetime.strftime(time_tz, format('%#I:%M %p'))}" \
                    f"&tz={setup['location']}&"
        time_fmt = f"{date_local} - [{time_local}]({time_link})"

        away_team = game_base[0].xpath('.//a[@class="AnchorLink"]/text()').get()
        home_team = game_base[1].xpath('.//a[@class="AnchorLink"]/text()').get()
        game_note = game_base[0].xpath('.//span[contains(@class, "gameNote")]/text()').get()
        espn_id = game_base[2].xpath('.//a[@class="AnchorLink"]/@href').get()
        espn_link = f"[ESPN](https://www.espn.com{espn_id})"

        net_con = game_base[3].xpath('.//div[contains(@class, "network-container")]')

        if net_con.xpath('.//div[@class="Image__Wrapper Image__Wrapper--relative"]'):
            # network identified by logo (ESPN brand)
            tv = net_con.xpath('.//div[@class="Image__Wrapper Image__Wrapper--relative"]/img/@alt').get()
        else:
            # network identified by text
            tv = net_con.xpath('.//div[contains(@class, "network-name")]/text()').get()

        if time_tz.date() == datetime.now(tz=pytz.timezone(setup['timezone'])).date():
            games_today.append(f"|{away_team} {lookup_by_loc[away_team][0]} @ {home_team} {lookup_by_loc[home_team][0]}|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")
        else:
            body_rows.append(f"|{away_team} {lookup_by_loc[away_team][0]} @ {home_team} {lookup_by_loc[home_team][0]}|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")

    # build body based on today and upcoming games
    body = ""
    if games_today:
        body += f"|Today's Games|||||\n" \
               f"|:--|:--|:--|:--|:--|\n"
        for game in games_today:
            body += f"{game}"
        body += "\n&nbsp;\n\n"
    else:
        body += "No games scheduled today\n\n&nbsp;\n\n"
    if body_rows:
        body += f"|Upcoming Games|||||\n" \
               f"|:--|:--|:--|:--|:--|\n"
        for game in body_rows:
            body += f"{game}"

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
