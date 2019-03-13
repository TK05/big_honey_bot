from datetime import datetime
import os
import random
import json
import requests
from threads.post_game.nbacom_boxscore_scrape import generate_markdown_tables
from threads.post_game.game_status_check import status_check
from bots.thread_handler_bot import new_thread, edit_thread
from threads.static.templates import PostGame


DEBUG = True if os.environ['DEBUG'] == 'True' else False

TEAM = os.environ['TEAM']
URL = f"https://api.myjson.com/bins/{os.environ['HEADLINE_BIN']}"


def post_game_headline(opp_team, date, result, margin, final_score):
    """Generate a post game thread title based on game result.

    Thread title will be randomly selected from post_game_headlines.json based on win/loss and margin.
    """

    if DEBUG:
        with open('../threads/post_game/post_game_headlines.json', 'r') as f:
            hl_list = json.load(f)
    else:
        # Download json from myjson bin
        try:
            hl_list = requests.get(URL).json()
            print(f"Headline JSON Downloaded @ {datetime.now()}")
        except ValueError:
            print("Error downloading json file.")

    for score, lines in hl_list[result].items():
        if margin < int(score):
            rand = random.randrange(len(hl_list[result][score]))
            template = hl_list[result][score][rand]

            return f"POST GAME THREAD: {template.format(TEAM, opp_team, final_score, date)}"


def format_post(schedule_data):
    """Create body of post-game thread as markdown text."""

    bs_tables, win, margin, final_score = generate_markdown_tables(schedule_data['NBA_ID'], schedule_data['Location'])
    headline = post_game_headline(schedule_data['Opponent'], schedule_data['Date_Str'], str(win), margin, final_score)

    top_links = PostGame.top_links(schedule_data['ESPN_Recap'], schedule_data['ESPN_Box'],
                                   schedule_data['ESPN_Gamecast'], schedule_data['NBA_Box'],
                                   schedule_data['NBA_Shot'])

    body = f"{top_links}\n\n&nbsp;\n\n{bs_tables}"

    return headline, body


def post_new_thread(headline, body, thread_type):
    """Posts a new thread, returns a Submission object for editing later."""

    post_obj = new_thread(headline, body, thread_type)
    print(f"Thread posted to r/{os.environ['TARGET_SUB']}")

    return post_obj


def edit_existing_thread(prev_post_obj, new_body):
    """Edits an existing thread given a Submission object."""

    edit_thread(prev_post_obj, new_body)
    print(f"Thread id: '{prev_post_obj}' edited on r/{os.environ['TARGET_SUB']}")

    return prev_post_obj


def post_game_thread_handler(event_data, only_final=False, was_prev_post=False, prev_post=None):
    """Wait for game completion and, upon completion, create headline and body reflecting game result.

    If data returned is not the final boxscore, function will recursive call itself to later return
    finalized data to edit the thread."""

    print(f"Sending to game_status_check, final version only: {str(only_final)}")
    was_final = status_check(event_data["NBA_ID"], only_final)
    print(f"Generating thread data for {event_data['Date_Str']} --- "
          f"{event_data['Type']} - Final Version: {str(was_final)}")
    headline, body = format_post(event_data)

    # Game final, no need for a future edit
    if was_final and not was_prev_post:
        post_game_thread = post_new_thread(headline, body, event_data['Type'])
    # Game final after initial post
    elif was_final and was_prev_post:
        post_game_thread = edit_existing_thread(prev_post, body)
    # Game finished but not final, initial post
    else:
        initial_post = post_new_thread(headline, body, event_data['Type'])
        post_game_thread_handler(event_data, only_final=True, was_prev_post=True, prev_post=initial_post)

    return headline, body, post_game_thread
