# datetime.strftime(datetime.strptime("July 02, 2022", "%B %d, %Y"), "%j")
events = {
    188: {
        "start_doy": 188,
        "end_doy": 198,
        "date_str": "July 7-17",
        "desc": "NBA Summer League 2023 (Las Vegas, NV)",
        "links": {"NBA.com": "https://www.nba.com/summer-league/2023"}
     },
    190: {
        "start_doy": 190,
        "end_doy": 190,
        "date_str": "July 9",
        "desc": "Nuggets vs. Hawks - 7:30 PM MT",
        "links": {"ESPN": "https://www.espn.com/nba-summer-league/game?gameId=401558329&league=nba-summer-las-vegas"}
    },
    193: {
        "start_doy": 193,
        "end_doy": 193,
        "date_str": "July 12",
        "desc": "Nuggets vs. Jazz - 7:30 PM MT",
        "links": {"ESPN": "https://www.espn.com/nba-summer-league/game?gameId=401558349&league=nba-summer-las-vegas"}
    },
    195: {
        "start_doy": 195,
        "end_doy": 195,
        "date_str": "July 14",
        "desc": "Nuggets vs. Heat - 7:00 PM MT",
        "links": {"ESPN": "https://www.espn.com/nba-summer-league/game?gameId=401558364&league=nba-summer-las-vegas"}
    },
    223: {
        "start_doy": 223,
        "end_doy": 224,
        "date_str": "August 11-12",
        "desc": "Naismith Memorial Basketball Hall of Fame Enshrinement Weekend (Springfield, MA)",
        "links": {}
    },
    237: {
        "start_doy": 237,
        "end_doy": 253,
        "date_str": "August 25 - September 10",
        "desc": "FIBA Basketball World Cup (Philippines / Japan / Indonesia)",
        "links": {"FIBA.basketball": "https://www.fiba.basketball/basketballworldcup/2023"}
    },
    # 186: {
    #     "start_doy": 186,
    #     "end_doy": 188,
    #     "date_str": "July 5-7",
    #     "desc": "SLC Summer League - (Grizzlies, Thunder, 76ers, Jazz)",
    #     "links": {}
    # },
    # 187: {
    #     "start_doy": 187,
    #     "end_doy": 187,
    #     "date_str": "July 6",
    #     "desc": "Teams may begin signing free agents to contracts (12:01PM ET)",
    #     "links": {}
    # },
    # 188: {
    #     "start_doy": 188,
    #     "end_doy": 198,
    #     "date_str": "July 7-17",
    #     "desc": "NBA2K23 Summer League in Las Vegas (All 30 teams)",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 189: {
    #     "start_doy": 189,
    #     "end_doy": 189,
    #     "date_str": "July 8",
    #     "desc": "Denver vs. Minnesota - 7:00PM - NBA TV - Summer League Game 1",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 191: {
    #     "start_doy": 191,
    #     "end_doy": 191,
    #     "date_str": "July 10",
    #     "desc": "Denver vs. Cleveland - 5:00PM - ESPNU - Summer League Game 2",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 194: {
    #     "start_doy": 194,
    #     "end_doy": 194,
    #     "date_str": "July 13",
    #     "desc": "Denver vs. LA Clippers - 8:00PM - NBA TV - Summer League Game 3",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 196: {
    #     "start_doy": 196,
    #     "end_doy": 196,
    #     "date_str": "July 15",
    #     "desc": "Denver vs. Philadelphia - 4:00PM - NBA TV - Summer League Game 4",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 229: {
    #     "start_doy": 229,
    #     "end_doy": 229,
    #     "date_str": "August 17",
    #     "desc": "Serbia @ Slovenia - NT Friendly - 12:15AM MDT - Ljubjana, Slovenia",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=12:15%20AM&tz=Denver&"
    #     }
    # },
    # 231: {
    #     "start_doy": 231,
    #     "end_doy": 231,
    #     "date_str": "August 19",
    #     "desc": "Serbia vs. Italy - NT Friendly - 10:00AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 232.1: {
    #     "start_doy": 232,
    #     "end_doy": 232,
    #     "date_str": "August 20",
    #     "desc": "Serbia vs. Czech Republic - NT Friendly - 10:00AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 232.2: {
    #     "start_doy": 232,
    #     "end_doy": 232,
    #     "date_str": "August 20",
    #     "desc": "Serbia @ Germany - NT Friendly - 12:30AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=12:30%20AM&tz=Denver&"
    #     }
    # },
    # 237: {
    #     "start_doy": 237,
    #     "end_doy": 237,
    #     "date_str": "August 25",
    #     "desc": "Serbia vs. Greece - World Cup Qualifier - 10:00AM MDT - Belgrade, Serbia",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 240: {
    #     "start_doy": 240,
    #     "end_doy": 240,
    #     "date_str": "August 28",
    #     "desc": "Serbia @ Turkey - World Cup Qualifier - 9:00AM MDT - Istanbul, Turkey",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=9:00%20AM&tz=Denver&"
    #     }
    # },
    # 245: {
    #     "start_doy": 245,
    #     "end_doy": 245,
    #     "date_str": "September 2",
    #     "desc": "Serbia vs. Netherlands - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 246.1: {
    #     "start_doy": 246,
    #     "end_doy": 246,
    #     "date_str": "September 3",
    #     "desc": "Serbia vs. Czech Republic - Eurobasket '22 - 9:30AM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=9:30%20AM&tz=Denver&"
    #     }
    # },
    # 246.2: {
    #     "start_doy": 246,
    #     "end_doy": 246,
    #     "date_str": "September 3",
    #     "desc": "Serbia vs. Finland - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 249: {
    #     "start_doy": 249,
    #     "end_doy": 249,
    #     "date_str": "September 6",
    #     "desc": "Serbia vs. Isreal - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 251: {
    #     "start_doy": 251,
    #     "end_doy": 251,
    #     "date_str": "September 8",
    #     "desc": "Serbia vs. Poland - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 252: {
    #     "start_doy": 252,
    #     "end_doy": 253,
    #     "date_str": "September 9-10",
    #     "desc": "Naismith Memorial Basketball Hall of Fame Enshrinement Weekend (Springfield, MA)",
    #     "links": {}
    # },
    # 270: {
    #     "start_doy": 270,
    #     "end_doy": 270,
    #     "date_str": "September 27",
    #     "desc": "NBA training camps open",
    #     "links": {}
    # },
    # 273: {
    #     "start_doy": 273,
    #     "end_doy": 273,
    #     "date_str": "September 30",
    #     "desc": "NBA preseason games begin",
    #     "links": {}
    # },
    # 287: {
    #     "start_doy": 287,
    #     "end_doy": 287,
    #     "date_str": "October 14",
    #     "desc": "NBA preseason ends",
    #     "links": {}
    # },
    # 290: {
    #     "start_doy": 290,
    #     "end_doy": 290,
    #     "date_str": "October 17",
    #     "desc": "Rosters set for start of 2022-23 NBA regular season (5pm ET)",
    #     "links": {}
    # },
    # 291: {
    #     "start_doy": 291,
    #     "end_doy": 291,
    #     "date_str": "October 18",
    #     "desc": "NBA regular season begins",
    #     "links": {}
    # }
}
