import logging
import re

import requests
from parsel import Selector

from big_honey_bot.helpers import (
    get_datetime_from_str,
    change_timezone,
    get_str_from_datetime,
    get_datetime,
    description_tags,
    hidden_tags,
    platform_hr_min_fmt,
    platform_mo_day_fmt,
    last_updated_fmt
)
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.config.main import setup
from big_honey_bot.threads.main import new_thread, edit_thread
from big_honey_bot.threads.static.lookups import lookup_by_loc
from big_honey_bot.threads.static.events import events as se
from big_honey_bot.threads.helpers import lineup_injury_odds


logger = logging.getLogger(get_pname_fname_str(__file__))


def get_nba_games(playoffs=False):
    all_games = requests.get(setup['nba_url']).json()

    def get_game_data(game, for_team=''):
        game_data = []

        time_utc = get_datetime_from_str(dt_str=game['gameDateTimeUTC'], fmt='%Y-%m-%dT%H:%M:%SZ', add_tz=True, tz='UTC')
        time_local_dt = change_timezone(dt=time_utc, tz=setup['timezone'])
        date_local = get_str_from_datetime(dt=time_local_dt, fmt=platform_mo_day_fmt)
        time_local = get_str_from_datetime(dt=time_local_dt, fmt=f'{platform_hr_min_fmt} %p %Z')
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{get_str_from_datetime(dt=time_local_dt, fmt=f'{platform_hr_min_fmt} %p')}" \
                    f"&tz={setup['location']}&"
        
        away_team = game['awayTeam']['teamName'] if game['awayTeam']['teamId'] != 0 else "TBD"
        home_team = game['homeTeam']['teamName'] if game['homeTeam']['teamId'] != 0 else "TBD"

        game_data.append(f"{away_team} @ {home_team}")
        game_data.append(f"{date_local} - [{time_local}]({time_link})" if for_team else f"[{time_local}]({time_link})")
        nat_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['nationalTvBroadcasters']]

        if playoffs:
            if game['seriesGameNumber'] == "":
                    game_data.insert(0, game['gameLabel'])
            else:
                game_data.insert(0, game['seriesGameNumber'])
            if not for_team:
                game_data.append(game['seriesText'])

        if for_team:
            home_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['homeTvBroadcasters']]
            away_tv = [i['broadcasterDisplay'] for i in game['broadcasters']['awayTvBroadcasters']]
            tv_ordered = [nat_tv, home_tv] if for_team == 'home' else [nat_tv, away_tv]
            game_data.append(", ".join([i for s in tv_ordered for i in s]))
        else:
            odds = lineup_injury_odds(game['homeTeam']['teamName'])[-1]
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
        today = get_datetime().date()
        i = 0

        for date in all_games['leagueSchedule']['gameDates']:
            day = get_datetime_from_str(dt_str=date['gameDate'], fmt='%m/%d/%Y %H:%M:%S').date()

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
        time = get_datetime_from_str(dt_str=f"{date_str} {time_str}", fmt='%A, %B %d, %Y %I:%M %p', add_tz=True, tz='US/Eastern')
        time_tz = change_timezone(dt=time, tz=setup['timezone'])

        date_local = f"{get_str_from_datetime(dt=time_tz, fmt=platform_mo_day_fmt)}"
        time_local = f"{get_str_from_datetime(dt=time_tz, fmt=f'{platform_hr_min_fmt} %p %Z')}"
        time_link = f"https://dateful.com/time-zone-converter?t=" \
                    f"{get_str_from_datetime(dt=time_tz, fmt=f'{platform_hr_min_fmt} %p')}" \
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

        if time_tz.date() == get_datetime(add_tz=True).date():
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
        current_doy = int(get_str_from_datetime(fmt="%j"))

        for i in sorted(se.keys()):
            if se[i]["start_day"] <= current_doy <= se[i]["end_day"]:
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
    in_playoffs = get_env('IN_PLAYOFFS')
    todays_games, team_games = get_nba_games(playoffs=in_playoffs)

    if team_games:
        if in_playoffs:
            row_to_add = [f"|Upcoming|{setup['team']}|Playoff|Games|", "|:--|:--|:--|:--|", []]
        else:
            row_to_add = [f"|{setup['team']} Next {len(team_games)}|||", "|:--|:--|:--|", []]

        for game in team_games:
            row_to_add[-1].append(game)

        body_events.insert(0, row_to_add)

    if todays_games:
        if in_playoffs:
            row_to_add = ["|Today's|Playoff|Games||||", "|:--|:--|:--|:--|:--|:--|", []]
        else:
            row_to_add = ["|Today's|Games|||", "|:--|:--|:--|:--|", []]

        for game in todays_games:
            row_to_add[-1].append(game)

        body_events.insert(1, row_to_add)

    if get_env('IS_OFFSEASON'):  # include static events
        static_top, static_bottom = get_static_events()

        if static_top:
            body_events.insert(1, static_top)

        if static_bottom:
            body_events.append(static_bottom)

    body = f"{hidden_tags['dg_start']}\n\n"

    if body_events:
        separator = "\n\n&nbsp;\n\n"

        for table in body_events[:-1]:
            body += f"{table[0]}\n{table[1]}\n"
            body += "\n".join(table[2])
            body += separator

        # avoid adding separator to end of body
        body += f"{body_events[-1][0]}\n{body_events[-1][1]}\n"
        body += "\n".join(body_events[-1][2])

    # # Add last updated timestamp to end
    # last_updated_time = get_str_from_datetime(fmt=last_updated_fmt, to_tz=True)
    # body += f"\n{last_updated_time}\n{hidden_tags['dg_end']}"
    body += f"\n{hidden_tags['dg_end']}"

    if not event:
        print(body)
    else:
        if description_tags['daily_games'] in event.body:
            event.body = event.body.replace(description_tags['daily_games'], body)
        else:
            dg_regex_str = f"{re.escape(hidden_tags['dg_start'])}(.*?){re.escape(hidden_tags['dg_end'])}"
            dg_pattern = re.compile(rf"{dg_regex_str}", re.DOTALL)
            event.body = re.sub(dg_pattern, body, event.body)


def off_day_thread_handler(event, update_only=False):
    """Generates thread title and body for event. Posts generated thread.

    :param event: Event to generate thread for
    :type event: gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    generate_thread_body(event)

    if not update_only:
        logger.info(f"Created headline: {event.summary}")
        new_thread(event)
    else:
        logger.info(f"Updating existing thread with new event data: {event.summary}")
        edit_thread(event)


if __name__ == "__main__":
    generate_thread_body()
