# 3/6/2019 - v1.1
# TK

import os
import praw


TARGET_SUB = os.environ['TARGET_SUB']
USER_AGENT = os.environ['USER_AGENT']

username = os.environ['praw_username']
password = os.environ['praw_password']
client_id = os.environ['praw_client_id']
client_secret = os.environ['praw_client_secret']

FLAIRS = {
    'pre': os.environ['FLAIR_PRE'],
    'game': os.environ['FLAIR_GAME'],
    'post': os.environ['FLAIR_POST']
}

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=USER_AGENT)
subreddit = reddit.subreddit(TARGET_SUB)


def new_thread(title, body, thread_type):
    """Post new thread given subject and body. Uses praw settings in config.ini

    Will automatically unsticky any other "THREAD" type thread,
    turn off send_replies, sticky the thread and sort by new.
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
    post_obj.edit(body)
