import os
import platform
import logging
from datetime import datetime

import requests
import pytz
from parsel import Selector

from bots.thread_handler_bot import new_thread
from config import setup, get_env
from tools.toolkit import description_tags
from data.static.data import lookup_by_loc
from threads.off_day.static_events import events as se
from threads.game.lineup_injury_odds import line_inj_odds


IN_PLAYOFFS = get_env('IN_PLAYOFFS')
IS_OFFSEASON = get_env('IS_OFFSEASON')

platform_hr_min_fmt = "%#I:%M" if platform.system() == 'Windows' else "%-I:%M"
platform_mo_day_fmt = "%#m/%#d" if platform.system() == 'Windows' else "%-m/%-d"

logger = logging.getLogger(f"{os.path.basename(__file__)}")


def get_nba_games(playoffs=False):
    all_games = requests.get(setup['nba_url']).json()

    def get_game_data(game, for_team=''):
        game_data = []
        time_utc = datetime.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ')
        time_local_dt = time_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(setup['timezone']))
        date_local = time_local_dt.strftime(platform_mo_day_fmt)
        time_local = f"{datetime.strftime(time_local_dt, format(f'{platform_hr_min_fmt} %p %Z'))}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{datetime.strftime(time_local_dt, format(f'{platform_hr_min_fmt} %p'))}" \
                    f"&tz={setup['location']}&"
        game_data.append(f"{date_local} - [{time_local}]({time_link})" if for_team else f"[{time_local}]({time_link})")
        game_data.append(f"{game['awayTeam']['teamName']} @ {game['homeTeam']['teamName']}")
        nat_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['nationalTvBroadcasters']]

        if for_team:
            if playoffs:
                game_data.insert(0, game['seriesGameNumber'])
            home_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['homeTvBroadcasters']]
            away_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['awayTvBroadcasters']]
            tv_ordered = [nat_tv, home_tv] if for_team == 'home' else [nat_tv, away_tv]
            game_data.append(", ".join([i for s in tv_ordered for i in s]))
        else:
            if playoffs:
                game_data.insert(0, game['seriesGameNumber'])
                game_data.append(game['seriesText'])
            odds = line_inj_odds(game['homeTeam']['teamName'])[-1]
            game_data.append(" ".join(odds) if "N/A" not in odds else "")
            game_data.append(", ".join(nat_tv))

        return time_utc, game_data

    def get_teams_next_games(start, n=5):
        games = []
        sort_order = []

        for date in all_games['leagueSchedule']['gameDates'][start:]:
            for game in date['games']:
                if setup['team'] in [game['awayTeam']['teamName'], game['homeTeam']['teamName']]:
                    loc = 'home' if setup['team'] == game['homeTeam']['teamName'] else 'away'
                    sort_time, game_data = get_game_data(game, for_team=loc)
                    sort_order.append(sort_time)
                    games.append(game_data)
                    n -= 1
            if n == 0:
                break

        return [game for _, game in sorted(zip(sort_order, games))]

    def get_days_games():
        games = []
        sort_order = []
        today = datetime.now().date()
        i = 0

        for date in all_games['leagueSchedule']['gameDates']:
            day = datetime.strptime(date['gameDate'], '%m/%d/%Y %H:%M:%S').date()

            if today == day:
                for game in date['games']:
                    sort_time, game_data = get_game_data(game)
                    sort_order.append(sort_time)
                    games.append(game_data)
                break
            # handle days w/ no games (not in league schedule)
            elif day > today:
                break
            else:
                i += 1

        return i, [game for _, game in sorted(zip(sort_order, games))]

    idx, todays_games_list = get_days_games()
    team_next_games_list = get_teams_next_games(idx)
    todays_games = []
    team_games = []

    for g in todays_games_list:
        todays_games.append(f'|{"|".join(g)}|')

    for g in team_next_games_list:
        team_games.append(f'|{"|".join(g)}|')

    return todays_games, team_games


def get_espn_games():
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
        time = pytz.timezone('US/Eastern').localize(
            datetime.strptime(f"{date_str} {time_str}", '%A, %B %d, %Y %I:%M %p'))
        time_tz = time.astimezone(pytz.timezone(setup['timezone']))

        date_local = f"{datetime.strftime(time_tz, format(platform_mo_day_fmt))}"

        time_local = f"{datetime.strftime(time_tz, format(f'{platform_hr_min_fmt} %p %Z'))}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{datetime.strftime(time_tz, format(f'{platform_hr_min_fmt} %p'))}" \
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
            games_today.append(
                f"|{away_team} {lookup_by_loc[away_team][0]} @ {home_team} {lookup_by_loc[home_team][0]}|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")
        else:
            # Catch when home or away team is none/tbd
            if not home_team:
                body_rows.append(
                    f"|{away_team} {lookup_by_loc[away_team][0]} @ TBD|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")
            elif not away_team:
                body_rows.append(
                    f"|TBD @ {home_team} {lookup_by_loc[home_team][0]}|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")
            else:
                body_rows.append(
                    f"|{away_team} {lookup_by_loc[away_team][0]} @ {home_team} {lookup_by_loc[home_team][0]}|{time_fmt}|{game_note}|{tv}|{espn_link}|\n")

    return body_rows, games_today


def generate_thread_body(event=None):
    """Generates off day thread body based on that days games. Replaces placeholder tags with
    this generated data.

    :param event: Event to generate thread body for
    :type event: gcsa.event.Event
    :returns: Nothing, modifies event in place
    :rtype: None
    """

    def get_static_events():
        def format_links(links):
            return ', '.join(f"[{k}]({v})" for k, v in links.items())

        upcoming_events = []
        events_today = []
        current_doy = int(datetime.strftime(datetime.now(), "%j"))

        for i in sorted(se.keys()):
            if se[i]["start_doy"] <= current_doy <= se[i]["end_doy"]:
                events_today.append(f"|{se[i]['desc']}|{se[i]['date_str']}|{format_links(se[i]['links'])}|")
            elif i < current_doy:
                pass
            else:
                upcoming_events.append(f"|{se[i]['desc']}|{se[i]['date_str']}|{format_links(se[i]['links'])}|")

        if upcoming_events:
            upcoming_events = ["|Upcoming Events|||", "|:--|:--|:--|", upcoming_events]

        if events_today:
            events_today = ["|Today's Events|||", "|:--|:--|:--|", events_today]

        return events_today, upcoming_events

    body_events = []
    todays_games, team_games = get_nba_games(playoffs=IN_PLAYOFFS)

    if team_games:
        if IN_PLAYOFFS:
            row_to_add = [f"|Upcoming {setup['team']} Playoff Games|||", "|:--|:--|:--|:--|", []]
        else:
            row_to_add = [f"|{setup['team']} Next {len(team_games)}|||", "|:--|:--|:--|", []]

        for game in team_games:
            row_to_add[-1].append(game)

        body_events.insert(0, row_to_add)

    if todays_games:
        if IN_PLAYOFFS:
            row_to_add = ["|Today's Playoff Games||||", "|:--|:--|:--|:--|:--|:--|", []]
        else:
            row_to_add = ["|Today's Games||||", "|:--|:--|:--|:--|", []]

        for game in todays_games:
            row_to_add[-1].append(game)

        body_events.insert(1, row_to_add)

    if IS_OFFSEASON:  # include static events
        static_top, static_bottom = get_static_events()

        if static_top:
            body_events.insert(1, static_top)

        if static_bottom:
            body_events.append(static_bottom)

    body = ""

    if body_events:
        separator = "\n\n&nbsp;\n\n"

        for table in body_events[:-1]:
            body += f"{table[0]}\n{table[1]}\n"
            body += "\n".join(table[2])
            body += separator

        # avoid adding separator to end of body
        body += f"{body_events[-1][0]}\n{body_events[-1][1]}\n"
        body += "\n".join(body_events[-1][2])

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

    logger.info(f"Created headline: {event.summary}")
    new_thread(event)


if __name__ == "__main__":
    generate_thread_body()
