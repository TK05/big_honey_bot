**Source code for r/denvernuggets BigHoneyBot**

An app to automate the posting of Pre-Game/Game/Post-Game threads on r/denvernuggets.

Capable of:

1. Generating an event schedule using data from ESPN and NBA.com.
2. Gathering needed event (before and after) information with web scrapes and API requests.
3. Formatting subject and body (in markdown) for the various thread types.
4. Posting a new thread to r/denvernuggets.
5. Saving a raw "gist" of the event subject and body for reference.

---

## Configuration


To configure properly, environment variables will need to be properly set.

### Debug setting
DEBUG=False

### App config settings
SEASON=2018 *first year in season; ex: 2018 for '18-'19*
TEAM=Nuggets
LOCATION=Denver
TZ_STR=MT
TIMEZONE=US/Mountain

# App/PRAW specific settings
TARGET_SUB=:targetsub
USER_AGENT=BigHoneyBot_v1.0 by SomeGuy

# Subreddit link_flair IDs
FLAIR_PRE=:id for link_flair
FLAIR_GAME=:id for link_flair
FLAIR_POST=:id for link_flair

# PRAW config end variables
praw_username=:bot_username
praw_password=:bot_password
praw_client_id=:reddit_app_client_id
praw_client_secret=:reddit_app_client_secret

# GISTS config env variables
GISTS_USERNAME=:github_username
GISTS_API=:github_access_token
GISTS_PRE_FN=:gist_filename
GISTS_GAME_FN=:gist_filename
GISTS_POST_FN=:gist_filename
GISTS_PRE_ID=:gist_id
GISTS_GAME_ID=:gist_id
GISTS_POST_ID=:gist_id


---

## Details

**manage_events_bot.py**

Uses event's UTC key to know when to post a thread. 
Pre/Game thread events will gather info and post immediately. 
Post thread will call game_status_check.py to continually check the status of the game until it is over.

**schedule_scrap.py & create_events.py**

Run schedule_scrape.py then create_events.py as create_events relies on the initial data scrape from schedule_scrape.


---

###### Contact

Feel free to email me @ tkelley05@gmail.com

