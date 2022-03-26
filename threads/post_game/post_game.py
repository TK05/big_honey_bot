import os
import random
from datetime import datetime

from config import setup
from threads.post_game.nbacom_boxscore_scrape import generate_markdown_tables
from threads.post_game.game_status_check import status_check
from bots.thread_handler_bot import new_thread, edit_thread
from threads.static.headlines import headlines
from threads.static.headlines_playoffs import po_headlines
from threads.static.templates import PostGame
from events.manager import update_event, get_event


TEAM = setup['team']
TARGET_SUB = os.environ['TARGET_SUB']


def format_date_and_time(time_in):
    try:
        date_out = datetime.strptime(time_in, "%m/%d/%y %I:%M %p").strftime('%b %-d, %Y')
    except ValueError:
        date_out = datetime.strptime(time_in, "%m/%d/%y %I:%M %p").strftime('%b %#d, %Y')

    return date_out


def post_game_headline(opp_team, game_start, result, margin, final_score):
    """Generate a post game thread title based on game result.

    Thread title will be randomly selected from post_game_headlines.json based on win/loss and margin.
    """

    date_str = format_date_and_time(game_start)

    for score, lines in headlines[result].items():
        if margin < int(score):
            rand = random.randrange(len(headlines[result][score]))
            template = headlines[result][score][rand]

            return f"POST GAME THREAD: {template.format(TEAM, opp_team, final_score, date_str)}"


def playoff_headline(opp_team, date, win, margin, final_score, playoff_data):
    """Generate a post game thread title based on game result for playoff game."""

    team_wins, opp_wins = playoff_data[2]

    if win:
        team_wins += 1
    else:
        opp_wins += 1

    if team_wins >= 4:
        headline = po_headlines['clinch']
        return headline.format(final_score, TEAM.upper(), opp_team.upper(), team_wins, opp_wins, date)

    if opp_wins >= 4:
        headline = po_headlines['over']
        return headline.format(final_score, TEAM, playoff_data[1], opp_team, date)

    if win:
        headline = po_headlines['win'].format(TEAM.upper(), playoff_data[1], ('!' * int(team_wins)), final_score)
    else:
        headline = po_headlines['lose'].format(TEAM.upper(), playoff_data[1], final_score)

    if team_wins > opp_wins:
        headline += po_headlines['leading'].format(opp_team, team_wins, opp_wins, date)
    elif team_wins < opp_wins:
        headline += po_headlines['trailing'].format(opp_team, team_wins, opp_wins, date)
    else:
        headline += po_headlines['tied'].format(opp_team, team_wins, opp_wins, date)

    return headline


def format_post(event, playoff_data=None):
    """Create body of post-game thread as markdown text."""

    bs_tables, win, margin, final_score = generate_markdown_tables(event.meta['nba_id'], event.meta['home_away'])

    # Check for custom win/lose title from event
    custom_title = str()
    outcome_key = 'win' if win else 'lose'
    event_new = get_event(event.id)

    try:
        custom_title = event_new.meta[outcome_key]
        print(f"{os.path.basename(__file__)}: Custom post game title detected: {custom_title}")
    except KeyError:
        pass

    if custom_title:
        custom_title = custom_title.replace('***team***', TEAM)
        custom_title = custom_title.replace('***opponent***', event.meta['opponent'])
        custom_title = custom_title.replace('***margin***', str(margin))
        custom_title = custom_title.replace('***score***', final_score)
        custom_title = custom_title.replace('***date***', format_date_and_time(event.meta['game_start']))
        event.summary = custom_title
    elif playoff_data:
        event.summary = playoff_headline(event.meta['opponent'], event.meta['game_start'], win, margin, final_score, playoff_data)
    else:
        event.summary = post_game_headline(event.meta['opponent'], event.meta['game_start'], str(win), margin, final_score)

    top_links = PostGame.top_links(event.meta['espn_id'], event.meta['nba_id'])

    event.body = f"{top_links}\n\n&nbsp;\n\n{bs_tables}"

    return win


def post_game_thread_handler(event, playoff_data, only_final=False, was_prev_post=False):
    """Wait for game completion and, upon completion, create headline and body reflecting game result.

    If data returned is not the final boxscore, function will recursive call itself to later return
    finalized data to edit the thread."""

    print(f"{os.path.basename(__file__)}: Sending to game_status_check, final version only: {str(only_final)}")
    was_final = status_check(event.meta["nba_id"], only_final)
    print(f"{os.path.basename(__file__)}: Generating thread data for {event.summary} - Final Version: {str(was_final)}")

    if playoff_data[0]:
        win = format_post(event, playoff_data=playoff_data)
    else:
        win = format_post(event)

    if was_final:
        # Game final after initial post
        if was_prev_post:
            edit_thread(event)
        # Game final, no need for a future edit
        else:
            new_thread(event)

        event.meta['event_type'] = 'active'
        update_event(event)

    # Game finished but not final, create thread and rerun for only_final
    else:
        new_thread(event)
        event.meta['event_type'] = 'active'
        update_event(event)
        post_game_thread_handler(event, playoff_data, only_final=True, was_prev_post=True)

    return win
