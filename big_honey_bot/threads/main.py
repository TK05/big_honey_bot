import os
import logging
import time

import praw
import prawcore
from praw.exceptions import RedditAPIException

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_env


TARGET_SUB = get_env('TARGET_SUB')
USERNAME = get_env('PRAW_USERNAME')
PASSWORD = get_env('PRAW_PASSWORD')
CLIENT_ID = get_env('PRAW_CLIENT_ID')
CLIENT_SECRET = get_env('PRAW_CLIENT_SECRET')
USER_AGENT = setup['user_agent']

logger = logging.getLogger(f"{os.path.basename(__file__)}")

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)
reddit.validate_on_submit = True
subreddit = reddit.subreddit(TARGET_SUB)


def get_thread(post_id):
    """Find thread by ID

    :param post_id: ID of post to be found
    :type post_id: str
    :returns: post if found else None
    :rtype: class praw.models.reddit.submission.Submission or NoneType
    """
    post = reddit.submission(id=post_id)

    try:
        post.title
        return post
    except prawcore.NotFound:
        return None
    

def get_flair_uuid_from_event_type(event_type):
    flair_map = {
        "pre": os.getenv('FLAIR_PRE', None),
        "game": os.getenv('FLAIR_GAME', None),
        "post": os.getenv('FLAIR_POST', None),
        "off": os.getenv('FLAIR_OFF', None)
    }

    return flair_map.get(event_type)


def new_thread(event):
    """Posts new thread. Uses PRAW settings from env & config.py. Unstickies previous post or any other thread with
    "THREAD" in the title. Stickies new thread and sorts by "new".

    :param event: event object
    :type event: class gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    # Unsticky the correct post
    try:
        prev_post = get_thread(event.prev_post_id)
        prev_post.mod.sticky(state=False)
        logger.info(f"Unstickied previous post - {prev_post.title}")
    except AttributeError:
        top2_posts = subreddit.hot(limit=2)

        for post in top2_posts:
            if post.author.name == USERNAME:
                post.mod.sticky(state=False)
                logger.info(f"Unstickied - {post.title}")
                break

    post_attempts = 5
    flair_uuid = get_flair_uuid_from_event_type(event.meta['event_type'])

    while post_attempts > 0:
        try:
            post = subreddit.submit(event.summary, event.body, flair_id=flair_uuid, send_replies=False)
        except RedditAPIException:
            logger.error(f"Flair UUID ({flair_uuid}) is not valid for type={event.meta['event_type']}, attempting again without flair")
            flair_uuid = None
        # TODO: see if better handling of other/common praw errors
        except prawcore.BadRequest:
            time.sleep(30)
        else:
            post_attempts = 0
        finally:
            post_attempts -= 1
        
    post.mod.sticky(bottom=False)
    post.mod.suggested_sort(sort='new')
    logger.info(f"Thread posted to r/{TARGET_SUB} - {post.id}")

    setattr(event, 'post', post)
    event.meta['reddit_id'] = post.id


def edit_thread(event):
    """Edits body of existing thread

    :param event: event object
    :type event: class gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    event.post.edit(event.body)
    logger.info(f"Thread updated on r/{TARGET_SUB} - {event.post.id}")
