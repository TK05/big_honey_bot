import os
import logging

import praw
import prawcore.exceptions

from config import setup


logger = logging.getLogger(f"{os.path.basename(__file__)}")

TARGET_SUB = os.environ['TARGET_SUB']
USERNAME = os.environ['PRAW_USERNAME']
PASSWORD = os.environ['PRAW_PASSWORD']
CLIENT_ID = os.environ['PRAW_CLIENT_ID']
CLIENT_SECRET = os.environ['PRAW_CLIENT_SECRET']

USER_AGENT = setup['user_agent']
FLAIRS = setup['flairs']

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
    except prawcore.exceptions.NotFound:
        return None


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

    # TODO: prawcore.exceptions.BadRequest: received 400 HTTP response
    post = subreddit.submit(event.summary, event.body, flair_id=FLAIRS[event.meta['event_type']], send_replies=False)
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
