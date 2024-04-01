import logging
import time

import praw
import prawcore
from praw.exceptions import RedditAPIException

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.threads.static.templates import ThreadStats


TARGET_SUB = get_env('TARGET_SUB')
USERNAME = get_env('PRAW_USERNAME')
PASSWORD = get_env('PRAW_PASSWORD')
CLIENT_ID = get_env('PRAW_CLIENT_ID')
CLIENT_SECRET = get_env('PRAW_CLIENT_SECRET')
USER_AGENT = setup['user_agent']

logger = logging.getLogger(get_pname_fname_str(__file__))

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
        "pre": get_env('FLAIR_PRE'),
        "game": get_env('FLAIR_GAME'),
        "post": get_env('FLAIR_POST'),
        "off": get_env('FLAIR_OFF')
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
        prev_post = get_thread(event.prev_reddit_id)
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


def post_comment(thread, comment):
    """Submit a new comment to a given thread"""

    comment_obj = thread.reply(comment)

    return comment_obj.id
    

def generate_thread_stats(prev_thread, prev_event_type, curr_thread):
    
    def _get_thread_details(thread):
        """Determine thread stats from given thread."""

        results = {}
        
        thread.comments.replace_more(limit=None)

        num_comments = thread.num_comments

        top_comment = [None, 0, None, None]
        total_karma = 0
        all_authors = {}
        most_posts = ['', 0]
        most_karma = ['', 0]

        for comment in thread.comments.list():
            if not comment.author:
                continue
            all_authors.setdefault(comment.author.name, {'post_count': 0, 'karma': 0})
            all_authors[comment.author.name]['post_count'] += 1
            all_authors[comment.author.name]['karma'] += comment.score
            total_karma += comment.score
            if comment.score > top_comment[1]:
                top_comment = [comment.author.name, comment.score, comment.body, comment.permalink]

        for author, stats in all_authors.items():
            stats['score'] = stats['post_count'] + stats['karma']
            try:
                stats['ratio'] = round((stats['karma'] / stats['post_count']), 2)
            except ZeroDivisionError:
                stats['ratio'] = 0
            if stats['post_count'] > most_posts[1]:
                most_posts = [author, stats['post_count']]
            if stats['karma'] > most_karma[1]:
                most_karma = [author, stats['karma']]

        top_posters_names = sorted(all_authors, key=lambda x: (all_authors[x]['score']), reverse=True)
        top_posters = []

        for poster in top_posters_names[0:5]:
            top_posters.append([poster,
                                all_authors[poster]['post_count'],
                                all_authors[poster]['karma'],
                                all_authors[poster]['ratio']])
            
        results['num_comments'] = thread.num_comments
        results['len_all_authors'] = len(all_authors)
        results['total_karma'] = total_karma
        results['top_comment'] = top_comment
        results['most_posts'] = most_posts
        results['most_karma'] = most_karma
        results['top_posters'] = top_posters
        
        return results

    # Main logic
    logger.info(f"Gathering stats for: {prev_thread.id}, Replying to: {curr_thread.id}")
    
    results = _get_thread_details(prev_thread)
    results['thread_type'] = prev_event_type
    comment = ThreadStats.format_post(results)
    comment_id = post_comment(curr_thread, comment)

    logger.info(f"Thread stats reply finished, ID: {comment_id}")
