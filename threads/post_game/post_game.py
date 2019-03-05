# 3/2/2019 - v1.0
# TK

from datetime import datetime
import os
import random
import requests
from threads.post_game.nbacom_boxscore_scrape import generate_markdown_tables
from threads.post_game.game_status_check import status_check
from bots.new_thread_bot import new_thread
from threads.static.templates import PostGame


DEBUG = True if os.environ['DEBUG'] == 'True' else False

TEAM = os.environ['TEAM']
URL = f"https://api.myjson.com/bins/{os.environ['HEADLINE_BIN']}"


def post_game_headline(opp_team, date, result, margin, final_score):
    """Generate a post game thread title based on game result.

    Thread title will be randomly selected from post_game_headlines.json based on win/loss and margin.
    """

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


def post_game_thread_handler(event_data):
    """Wait for game completion and, upon completion, create headline and body reflecting game result."""

    print("Sending to game_status_check")
    status_check(event_data["NBA_ID"])
    print(f"Generating thread data for {event_data['Date_Str']} --- {event_data['Type']}")
    headline, body = format_post(event_data)

    if not DEBUG:
        new_thread(headline, body, event_data['Type'])
        print(f"Thread posted to r/{os.environ['TARGET_SUB']}")
    else:
        print(headline)
        print(body)

    return headline, body
