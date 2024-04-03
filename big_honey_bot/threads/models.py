import asyncpraw

from big_honey_bot.config.main import setup
from big_honey_bot.config.helpers import get_env


class Reddit(asyncpraw.Reddit):
    
    def __init__(self):
        super().__init__(
            client_id = get_env('PRAW_CLIENT_ID'),
            client_secret = get_env('PRAW_CLIENT_SECRET'),
            username = get_env('PRAW_USERNAME'),
            password = get_env('PRAW_PASSWORD'),
            user_agent = setup['user_agent']
        )
        self.validate_on_submit = True

    @property
    def _subreddit(self):
        return Subreddit(self, get_env('TARGET_SUB'))


class Subreddit:
    def __init__(self, reddit_instance, subreddit_name):
        self.reddit_instance = reddit_instance
        self.subreddit_name = subreddit_name

    async def __call__(self):
        return await self.reddit_instance.subreddit(self.subreddit_name)
    
    def __getattr__(self, attr):
        return getattr(self.reddit_instance.subreddit(self.subreddit_name), attr)
