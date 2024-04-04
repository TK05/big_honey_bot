import logging
import time

import asyncprawcore
from asyncpraw.exceptions import APIException

from big_honey_bot.config.helpers import get_env, get_pname_fname_str
from big_honey_bot.threads.models import Reddit
from big_honey_bot.threads.helpers import replace_nbs, get_flair_uuid_from_event_type
from big_honey_bot.threads.static.templates import ThreadStats


logger = logging.getLogger(get_pname_fname_str(__file__))


async def get_thread(post_id, fetch=True):
    """Find thread by ID

    :param post_id: ID of post to be found
    :type post_id: str
    :returns: post if found else None
    :rtype: class praw.models.reddit.submission.Submission or NoneType
    """

    async with Reddit() as reddit:
        post = await reddit.submission(id=post_id, fetch=fetch)

        try:
            post.title
            return post
        except asyncprawcore.NotFound:
            return None


async def new_thread(event):
    """Posts new thread. Uses PRAW settings from env & config.py. Unstickies previous post or any other thread with
    "THREAD" in the title. Stickies new thread and sorts by "new".

    :param event: event object
    :type event: class gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    with Reddit() as reddit:
        subreddit = await reddit._subreddit()

        # Unsticky the correct post
        try:
            prev_post = await get_thread(event.meta['prev_reddit_id'], fetch=False)
            await prev_post.mod.sticky(state=False)
            logger.info(f"Unstickied previous post - {prev_post.title}")
        except AttributeError:
            async for post in subreddit.hot(limit=2):
                if post.author.name == get_env('USERNAME'):
                    await post.mod.sticky(state=False)
                    logger.info(f"Unstickied - {post.title}")
                    break

        
        flair_uuid = get_flair_uuid_from_event_type(event.meta['event_type'])
        event.body = replace_nbs(event.body)
        
        post_attempts = 5
        while post_attempts > 0:
            try:
                post = await subreddit.submit(event.summary, event.body, flair_id=flair_uuid, send_replies=False)
            except APIException:
                logger.error(f"Flair UUID ({flair_uuid}) is not valid for type={event.meta['event_type']}, attempting again without flair")
                flair_uuid = None
            # TODO: see if better handling of other/common praw errors
            except asyncprawcore.BadRequest:
                time.sleep(30)
            else:
                post_attempts = 0
            finally:
                post_attempts -= 1
            
        await post.mod.sticky(bottom=False)
        await post.mod.suggested_sort(sort='new')

        logger.info(f"Thread posted to r/{get_env('TARGET_SUB')} - {post.id}")

        event.meta['reddit_id'] = post.id


async def edit_thread(event):
    """Edits body of existing thread

    :param event: event object
    :type event: class gcsa.event.Event
    :returns: None
    :rtype: NoneType
    """

    # First get post from reddit
    post = await get_thread(event.meta['reddit_id'])

    # Clean then replace post w/ current event's body
    event.body = replace_nbs(event.body)
    await post.edit(event.body)

    logger.info(f"Thread updated on r/{get_env('TARGET_SUB')} - {event.post.id}")


async def post_comment(thread, comment):
    """Submit a new comment to a given thread"""

    comment_obj = await thread.reply(comment)

    return comment_obj.id
    

async def generate_thread_stats(prev_thread, prev_event_type, curr_reddit_id):
    
    async def _get_thread_details(thread):
        """Determine thread stats from given thread."""

        results = {}
        
        comments = await thread.comments()
        await comments.replace_more(limit=None)
        all_comments = await comments.list()

        top_comment = [None, 0, None, None]
        total_karma = 0
        all_authors = {}
        most_posts = ['', 0]
        most_karma = ['', 0]

        for comment in all_comments:
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
    logger.info(f"Gathering stats for: {prev_thread.id}, Replying to: {curr_reddit_id}")
    
    results = await _get_thread_details(prev_thread)
    results['thread_type'] = prev_event_type
    comment = ThreadStats.format_post(results)
    curr_thread = await get_thread(curr_reddit_id)
    comment_id = await post_comment(curr_thread, comment)

    logger.info(f"Thread stats reply finished, ID: {comment_id}")
