import os
import praw

from config import setup


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
    :returns: found post
    :rtype: class praw.models.reddit.submission.Submission
    """
    return reddit.submission(id=post_id)


def new_thread(event):
    """Posts new thread. Uses PRAW settings from env & config.py. Unstickies previous post or any other thread with
    "THREAD" in the title. Stickies new thread and sorts by "new".

    :param event: event object
    :type event: class gcsa.event.Event
    :returns: reddit thread object after creation
    :rtype: class praw.models.reddit.submission.Submission
    """

    # Unsticky the correct post
    try:
        prev_post = get_thread(event.meta['prev_post_id'])
        prev_post.mod.sticky(state=False)
        print(f"{os.path.basename(__file__)}: Unstickied {prev_post.title}")
    except KeyError:
        top2_posts = subreddit.hot(limit=2)

        for post in top2_posts:
            if post.stickied:
                if "THREAD" in post.title:
                    post.mod.sticky(state=False)
                    print(f"{os.path.basename(__file__)}: Unstickied {post.title}")
                    break

    post = subreddit.submit(event.summary, event.body, flair_id=FLAIRS[event.meta['event_type']], send_replies=False)
    post.mod.sticky(bottom=False)
    post.mod.suggested_sort(sort='new')
    print(f"{os.path.basename(__file__)}: Thread posted to r/{TARGET_SUB} - {post.id}")

    return post


def edit_thread(post_obj, body):
    """Edits body of existing thread

    :param post_obj: existing thread to be edited
    :type post_obj: class praw.models.reddit.submission.Submission
    :param body: new body to post
    :type body: str
    :returns: None
    :rtype: NoneType
    """

    post_obj.edit(body)
    print(f"{os.path.basename(__file__)}: Thread updated on r/{TARGET_SUB} - {post_obj.id}")
