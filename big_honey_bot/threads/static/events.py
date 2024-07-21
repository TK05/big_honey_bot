# datetime.strftime(datetime.strptime("July 02, 2022", "%B %d, %Y"), "%j")
events = {
    # 178: {
    #     "start_day": 178,
    #     "end_day": 178,
    #     "date_str": "June 26",
    #     "desc": "NBA Draft 2024 (First Round) - 6:00 PM MT",
    #     "links": {"NBA.com": "https://www.nba.com/news/nba-draft-2024-two-nights-official-release"}
    #  },
    # 179: {
    #     "start_day": 179,
    #     "end_day": 179,
    #     "date_str": "June 27",
    #     "desc": "NBA Draft 2024 (Second Round) - 2:00 PM MT",
    #     "links": {"NBA.com": "https://www.nba.com/news/nba-draft-2024-two-nights-official-release"}
    #  },
    # 182: {
    #     "start_day": 182,
    #     "end_day": 182,
    #     "date_str": "June 30",
    #     "desc": "Free agent negotiation starts (beginning at 4 p.m. MT)",
    #     "links": {}
    # },
    # 187: {
    #     "start_day": 187,
    #     "end_day": 187,
    #     "date_str": "July 5",
    #     "desc": "Free agent signing starts (10:01 p.m. MT)",
    #     "links": {}
    # },
    194: {
        "start_day": 194,
        "end_day": 204,
        "date_str": "July 12-22",
        "desc": "NBA Summer League",
        "links": {"NBA.com": "https://www.nba.com/summer-league/2024"}
    },
    202: {
        "start_day": 202,
        "end_day": 202,
        "date_str": "July 20",
        "desc": "Nuggets vs. Pelicans @ 7:00PM - Summer League",
        "links": {}
    },
    208: {
        "start_day": 208,
        "end_day": 224,
        "date_str": "July 26 - August 11",
        "desc": "Paris 2024 Olympic Games",
        "links": {}
    },
    278: {
        "start_day": 278,
        "end_day": 278,
        "date_str": "October 4 & 6",
        "desc": "NBA Abu Dhabi Games 2024 (Nuggets vs. Celtics)",
        "links": {}
    },
    296: {
        "start_day": 296,
        "end_day": 296,
        "date_str": "October 22",
        "desc": "Start of the 2024-25 NBA regular season",
        "links": {}
    },
    # 186: {
    #     "start_day": 186,
    #     "end_day": 188,
    #     "date_str": "July 5-7",
    #     "desc": "SLC Summer League - (Grizzlies, Thunder, 76ers, Jazz)",
    #     "links": {}
    # },
    # 187: {
    #     "start_day": 187,
    #     "end_day": 187,
    #     "date_str": "July 6",
    #     "desc": "Teams may begin signing free agents to contracts (12:01PM ET)",
    #     "links": {}
    # },
    # 188: {
    #     "start_day": 188,
    #     "end_day": 198,
    #     "date_str": "July 7-17",
    #     "desc": "NBA2K23 Summer League in Las Vegas (All 30 teams)",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 189: {
    #     "start_day": 189,
    #     "end_day": 189,
    #     "date_str": "July 8",
    #     "desc": "Denver vs. Minnesota - 7:00PM - NBA TV - Summer League Game 1",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 191: {
    #     "start_day": 191,
    #     "end_day": 191,
    #     "date_str": "July 10",
    #     "desc": "Denver vs. Cleveland - 5:00PM - ESPNU - Summer League Game 2",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 194: {
    #     "start_day": 194,
    #     "end_day": 194,
    #     "date_str": "July 13",
    #     "desc": "Denver vs. LA Clippers - 8:00PM - NBA TV - Summer League Game 3",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 196: {
    #     "start_day": 196,
    #     "end_day": 196,
    #     "date_str": "July 15",
    #     "desc": "Denver vs. Philadelphia - 4:00PM - NBA TV - Summer League Game 4",
    #     "links": {
    #         "nba.com": "https://nbaevents.nba.com/events/nba-summer-league"
    #     }
    # },
    # 229: {
    #     "start_day": 229,
    #     "end_day": 229,
    #     "date_str": "August 17",
    #     "desc": "Serbia @ Slovenia - NT Friendly - 12:15AM MDT - Ljubjana, Slovenia",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=12:15%20AM&tz=Denver&"
    #     }
    # },
    # 231: {
    #     "start_day": 231,
    #     "end_day": 231,
    #     "date_str": "August 19",
    #     "desc": "Serbia vs. Italy - NT Friendly - 10:00AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 232.1: {
    #     "start_day": 232,
    #     "end_day": 232,
    #     "date_str": "August 20",
    #     "desc": "Serbia vs. Czech Republic - NT Friendly - 10:00AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 232.2: {
    #     "start_day": 232,
    #     "end_day": 232,
    #     "date_str": "August 20",
    #     "desc": "Serbia @ Germany - NT Friendly - 12:30AM MDT - Hamburg, Germany",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=12:30%20AM&tz=Denver&"
    #     }
    # },
    # 237: {
    #     "start_day": 237,
    #     "end_day": 237,
    #     "date_str": "August 25",
    #     "desc": "Serbia vs. Greece - World Cup Qualifier - 10:00AM MDT - Belgrade, Serbia",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=10:00%20AM&tz=Denver&"
    #     }
    # },
    # 240: {
    #     "start_day": 240,
    #     "end_day": 240,
    #     "date_str": "August 28",
    #     "desc": "Serbia @ Turkey - World Cup Qualifier - 9:00AM MDT - Istanbul, Turkey",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=9:00%20AM&tz=Denver&"
    #     }
    # },
    # 245: {
    #     "start_day": 245,
    #     "end_day": 245,
    #     "date_str": "September 2",
    #     "desc": "Serbia vs. Netherlands - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 246.1: {
    #     "start_day": 246,
    #     "end_day": 246,
    #     "date_str": "September 3",
    #     "desc": "Serbia vs. Czech Republic - Eurobasket '22 - 9:30AM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=9:30%20AM&tz=Denver&"
    #     }
    # },
    # 246.2: {
    #     "start_day": 246,
    #     "end_day": 246,
    #     "date_str": "September 3",
    #     "desc": "Serbia vs. Finland - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 249: {
    #     "start_day": 249,
    #     "end_day": 249,
    #     "date_str": "September 6",
    #     "desc": "Serbia vs. Isreal - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 251: {
    #     "start_day": 251,
    #     "end_day": 251,
    #     "date_str": "September 8",
    #     "desc": "Serbia vs. Poland - Eurobasket '22 - 1:00PM MDT - Prague, Czech Republic",
    #     "links": {
    #         "local time": "https://dateful.com/time-zone-converter?t=1:00%20PM&tz=Denver&"
    #     }
    # },
    # 252: {
    #     "start_day": 252,
    #     "end_day": 253,
    #     "date_str": "September 9-10",
    #     "desc": "Naismith Memorial Basketball Hall of Fame Enshrinement Weekend (Springfield, MA)",
    #     "links": {}
    # },
    # 270: {
    #     "start_day": 270,
    #     "end_day": 270,
    #     "date_str": "September 27",
    #     "desc": "NBA training camps open",
    #     "links": {}
    # },
    # 273: {
    #     "start_day": 273,
    #     "end_day": 273,
    #     "date_str": "September 30",
    #     "desc": "NBA preseason games begin",
    #     "links": {}
    # },
    # 287: {
    #     "start_day": 287,
    #     "end_day": 287,
    #     "date_str": "October 14",
    #     "desc": "NBA preseason ends",
    #     "links": {}
    # },
    # 290: {
    #     "start_day": 290,
    #     "end_day": 290,
    #     "date_str": "October 17",
    #     "desc": "Rosters set for start of 2022-23 NBA regular season (5pm ET)",
    #     "links": {}
    # },
    # 291: {
    #     "start_day": 291,
    #     "end_day": 291,
    #     "date_str": "October 18",
    #     "desc": "NBA regular season begins",
    #     "links": {}
    # }
}
