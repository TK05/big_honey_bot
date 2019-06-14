**r/denvernuggets BigHoneyBot**

A reddit bot to automate the posting of game threads on r/denvernuggets.

**What's a BigHoneyBot?**

BigHoneyBot includes tools that scrape and generate a posting schedule for upcoming games. It uses the stats.nba API to 
grab event details (HTML scrape for ESPN data). Each event has an associated timestamp from which a posting schedule is
generated for pre game and game thread events. This schedule is then uploaded as JSON to 
[Github Gist](https://gist.github.com/).

When running `manage_event_bots.py`, the bot will pull the schedule gist and wait until the next appropriate event 
triggers. Pre Game Threads are posted at 8AM MT on game days, Game Threads are posted 1 hour before scheduled tipoff.
Game Threads utilize the [lineups.com](https://www.lineups.com/nba/lineups) API for brief stats, current injuries and 
projected lineups. 

During the game, the bot will check stats.nba to get an update on the status of the game. When the game is finished, the
bot uses the stats.nba API to gather and format the box score and posts a Post Game Thread. The bot will then go to
sleep until the next scheduled posting event. 

Other features include automating some trivial sidebar updates, posting "thread stats" for comments & commenters from
the game thread, tracking playoff magic numbers and other playoff specific features.

BigHoneyBot is currently running on Heroku with a single worker. This has proven to be more than enough to manage a
single schedule and has the added benefit of being able to run 24/7 on Heroku's free-tier. Status can be monitored with
a something like `heroku logs -t` using the heroku-cli.

**Can I Use It?**

Absolutely! Admittedly, scraping the web and generating threads is a somewhat manual "one-off" process where much of the
configuration is specific to your needs but the core of BigHoneyBot can be used to manage a JSON schedule and post
threads at a given time. If you need help adapting BigHoneyBot to your needs, feel free to reach out. Much of the
r/denvernuggets specific style has to do with title style and sidebar specific settings. 

---

## Configuration

Sensitive environment variables will need to be set in environment. Other setup config and options are accessible in the 
`config.py` file.


### Required Environment Variables
`TARGET_SUB=:subreddit` - The subreddit the bot will operate in (no preceding r/).

`PRAW_USERNAME=:username` - Reddit username for the bot.

`PRAW_PASSWORD=:password` - Reddit password for the bot.

`PRAW_CLIENT_ID=:client_id` - Client ID from the registered app. 
[Reddit Apps](https://www.reddit.com/prefs/apps/)

`PRAW_CLIENT_SECRET=:client_secret` - Secret string from the registered app. 
[Reddit Apps](https://www.reddit.com/prefs/apps/)

`GISTS_USERNAME=:github_username` - Github username (Needed to manage Gists)

`GISTS_API=:github_access_token` - A personal access token with the gists scope enabled 
[Personal Access Token](https://github.com/settings/tokens)


### Config.py 

#### Debug

`DEBUG=:Boolean` - Sets some processes to output more information to the console. Still needs work.

#### Config/Setup variables

`'season': year` - Ex: 2018, *First year in season; ex: 2018 for '18-'19*

`'team': 'Team Name'` - Ex: 'Nuggets'

`'location': 'City'` - Ex: 'Denver'

`'timezone': 'pytz timezone'` - Ex: 'US/Mountain', *A valid 
[Pytz Timezone](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568)*

`'timezone_string': 'short timezone'` - Ex: 'MT'

`'user_agent': 'custom user agent'` - Ex: 'BigHoneyBot_by_TK'

`'flairs': {'pre':, 'game':, 'post':}` - Ex: 'pre': '51a03fc6-3e0c-11e9-8856-0e97475b835e', *Link flair template id,
[more info](https://praw.readthedocs.io/en/latest/code_overview/other/subredditflair.html)*


#### Config/Options

`'update_sidebar': True` - When enabled, the subreddit's sidebar will be updated after a game event.

`'thread_stats': True` - When enabled, the bot will post a comment about various stats from comments/commentators from 
previous Game Thread.

`'in_playoffs': False` - When enabled, it will track series status and use custom playoff headlines.

`'playoff_watch': False` - When enabled, a Playoffs [Magic Number](https://en.wikipedia.org/wiki/Magic_number_(sports))
is added to the sidebar.


#### Config/Gists
`'pre':/'game':/'post': {filename:, id:,}` - Gists specific to each thread type. These contain the markdown text for
easier manual editing if required.

`'schedule': {filename:, id:,}` - This is the main schedule JSON that the bot uses to stay on track. It's created once
after `tools/generate_schedule/create_gist.py` is run.

---

###### Contact

[lightweightpaint](https://www.lightweightpaint.com) - [tk@lightweightpaint.com](mailto:TK@lightweightpaint.com)
