import os
import random
import logging
from datetime import datetime

from big_honey_bot.config.helpers import get_env
from big_honey_bot.config.main import setup
from big_honey_bot.events.main import update_event, get_event
from big_honey_bot.threads.main import new_thread, edit_thread
from big_honey_bot.threads.post_game.nbacom_boxscore_scrape import generate_markdown_tables
from big_honey_bot.threads.post_game.game_status_check import status_check
from big_honey_bot.threads.static.headlines import headlines, playoff_headlines, pgt_placeholders
from big_honey_bot.threads.static.templates import PostGame


TEAM = setup['team']
TARGET_SUB = get_env('TARGET_SUB')

logger = logging.getLogger(f"{os.path.basename(__file__)}")


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


def playoff_headline(opp_team, game_start, win, final_score, playoff_data):
    """Generate a post game thread title based on game result for playoff game."""

    date_str = format_date_and_time(game_start)
    team_wins, opp_wins = playoff_data[2]

    if win:
        team_wins += 1
    else:
        opp_wins += 1

    if team_wins >= 4:
        headline = playoff_headlines['clinch']
        return headline.format(final_score, TEAM.upper(), opp_team.upper(), team_wins, opp_wins, date_str)

    if opp_wins >= 4:
        headline = playoff_headlines['over']
        return headline.format(final_score, TEAM, playoff_data[1], opp_team, date_str)

    if win:
        headline = playoff_headlines['win'].format(TEAM.upper(), playoff_data[1], ('!' * int(team_wins)), final_score)
    else:
        headline = playoff_headlines['lose'].format(TEAM.upper(), playoff_data[1], final_score)

    if team_wins > opp_wins:
        headline += playoff_headlines['leading'].format(opp_team, team_wins, opp_wins, date_str)
    elif team_wins < opp_wins:
        headline += playoff_headlines['trailing'].format(opp_team, team_wins, opp_wins, date_str)
    else:
        headline += playoff_headlines['tied'].format(opp_team, team_wins, opp_wins, date_str)

    return headline


def format_post(event, playoff_data):
    """Create body of post-game thread as markdown text."""

    bs_tables, win, margin, final_score = generate_markdown_tables(event.meta['nba_id'], event.meta['home_away'])

    # Check for custom win/lose title from event.meta
    outcome_key = 'win' if win else 'lose'
    event_new = get_event(event.id)
    custom_title = event_new.meta.get(outcome_key)

    if custom_title:
        logger.info(f"Custom post game title detected: {custom_title}")
        custom_title = custom_title.replace(pgt_placeholders['team'], TEAM)
        custom_title = custom_title.replace(pgt_placeholders['opponent'], event.meta['opponent'])
        custom_title = custom_title.replace(pgt_placeholders['margin'], str(margin))
        custom_title = custom_title.replace(pgt_placeholders['score'], final_score)
        custom_title = custom_title.replace(pgt_placeholders['date'], format_date_and_time(event.meta['game_start']))
        event.summary = custom_title
    elif playoff_data:
        event.summary = playoff_headline(event.meta['opponent'], event.meta['game_start'], win, final_score, playoff_data)
    else:
        event.summary = post_game_headline(event.meta['opponent'], event.meta['game_start'], str(win), margin, final_score)

    top_links = PostGame.top_links(event.meta['espn_id'], event.meta['nba_id'])

    event.body = f"{top_links}\n\n&nbsp;\n\n{bs_tables}"


def post_game_thread_handler(event, playoff_data, only_final=False, was_prev_post=False):
    """Wait for game completion and, upon completion, create headline and body reflecting game result.

    If data returned is not the final boxscore, function will recursive call itself to later return
    finalized data to edit the thread."""

    logger.info(f"Sending to game_status_check, final version only: {str(only_final)}")
    was_final = status_check(event.meta["nba_id"], only_final)
    logger.info(f"Generating thread data for {event.summary} - Final Version: {str(was_final)}")

    format_post(event, playoff_data)

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
