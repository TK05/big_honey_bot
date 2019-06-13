import os
import praw

from config import DEBUG, setup
from threads.static.templates import ThreadStats


USER_AGENT = setup['user_agent']

USERNAME = os.environ['praw_username']
PASSWORD = os.environ['praw_password']
CLIENT_ID = os.environ['praw_client_id']
CLIENT_SECRET = os.environ['praw_client_secret']

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)


def thread_details(thread):
    """Determine thread stats from given thread."""

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

    return [num_comments, len(all_authors), total_karma, top_comment, most_posts, most_karma, top_posters]


def post_reply(thread, comment):
    """Submit a new comment to a given thread"""

    comment_obj = thread.reply(comment)

    return comment_obj.id


def generate_stats_comment(game_thread, post_game_thread):

    print(f"Gathering stats for: {game_thread.id}, Replying to: {post_game_thread.id}")
    details = thread_details(game_thread)
    comment = ThreadStats.format_post(*details)
    if not DEBUG:
        comment_id = post_reply(post_game_thread, comment)
        print(f"Thread stats reply finished, ID: {comment_id}")
    else:
        print(comment)
