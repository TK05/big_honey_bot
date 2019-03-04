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


**config.py**

Contains most of the necessary global configuration variables needed to configure the bot. 



**_config.py**

Contains the login and configuration necessary to upload gists. In the style of...


```json
GISTS = {
	'USERNAME': :github_username,
	'API_TOKEN': :github_api_token,
	'URL': 'https://api.github.com/gists',
	'pre': ['pre_game.md', :gists_id_to_pre],
	'game': ['game_thread.md', :gists_id_to_game],
	'post': ['post_game.md', :gists_id_to_post]
	}
```


**praw.ini**

Configuration file necessary for [PRAW](https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) to work.

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

