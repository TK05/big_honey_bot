import os
import praw


USER_AGENT = os.environ['USER_AGENT']

username = os.environ['praw_username']
password = os.environ['praw_password']
client_id = os.environ['praw_client_id']
client_secret = os.environ['praw_client_secret']

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=USER_AGENT)


def thread_details(thread):
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


def format_post(num_comments, num_commenters, total_karma, top_comment, most_posts, most_karma, top_posters):
    comment = f"##BHB's Game Thread Stats\n\n&nbsp;\n\n" \
              f"**Posts:** {num_comments}\n\n" \
              f"**Bees:** {num_commenters}\n\n" \
              f"**Honey Harvested:** +{total_karma}\n\n"

    try:
        karma_per_comment = round((total_karma / num_comments), 2)
    except ZeroDivisionError:
        karma_per_comment = 0

    comment += f"**Honey/Post Avg.:** {karma_per_comment}\n\n&nbsp;\n\n" \
               f"**BHB's POTT:** +{top_comment[1]} Honey\n" \
               f">[{top_comment[0]}]({top_comment[3]})\n" \
               f">>{top_comment[2]}\n\n&nbsp;\n\n" \
               f"**Busiest Bee:** {most_posts[0]} w/ {most_posts[1]} Posts\n\n" \
               f"**Most Honey:** {most_karma[0]} +{most_karma[1]} Honey\n\n&nbsp;\n\n" \
               f"**BHB's Top-Bees**\n\n" \
               f"Bee|Posts|Honey|H/P|\n" \
               f":-|:-:|:-:|:-:|\n"

    for poster in top_posters:
        comment += f"**{poster[0]}**|{poster[1]}|+{poster[2]}|{poster[3]}|\n"

    return comment


def post_reply(thread, comment):
    comment_obj = thread.reply(comment)

    return comment_obj.id


def generate_stats_comment(game_thread, post_game_thread):
    print(f"Gathering stats for: {game_thread.id}, Replying to: {post_game_thread.id}")
    details = thread_details(game_thread)
    comment = format_post(*details)
    comment_id = post_reply(post_game_thread, comment)
    print(f"Thread stats reply finished, ID: {comment_id}")
