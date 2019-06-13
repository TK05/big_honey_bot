import os
import praw

from config import setup


TARGET_SUB = os.environ['TARGET_SUB']
USER_AGENT = setup['user_agent']

USERNAME = os.environ['praw_username']
PASSWORD = os.environ['praw_password']
CLIENT_ID = os.environ['praw_client_id']
CLIENT_SECRET = os.environ['praw_client_secret']

FLAIRS = setup['flairs']

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)
subreddit = reddit.subreddit(TARGET_SUB)


def new_thread(title, body, thread_type):
    """Post new thread given subject and body. Uses praw settings from env and config.py.

    Will automatically unsticky any other "THREAD" type thread, turn off send_replies,
    sticky the thread, set appropriate flair and sort by new.
    Returns a submission object in case the thread needs to be edited in the future.
    """

    # Unsticky the correct post
    top2_posts = subreddit.hot(limit=2)

    for post in top2_posts:
        if post.stickied:
            if "THREAD" in post.title:
                post.mod.sticky(state=False)
                print(f"Unstickied {post.title}")
                break

    post = subreddit.submit(title, body, flair_id=FLAIRS[thread_type], send_replies=False)
    post.mod.sticky(bottom=False)
    post.mod.suggested_sort(sort='new')

    return post


def edit_thread(post_obj, body):
    """Takes a Submission object and edits the body."""
    post_obj.edit(body)
