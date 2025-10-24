from big_honey_bot.config.main import setup
from big_honey_bot.threads.static.templates import PostGame
from big_honey_bot.threads.helpers import parse_game_clock
from big_honey_bot.threads.post_game.helpers import key_paths, get_value


SEASON = setup['season']


def team_boxscore(team_stats, player_stats, team_str, home_away):
    """Generate markdown boxscore for each player and team"""

    player_rows = ""
    dnp_list = []
    inactive_list = []

    # Create list of all column data needed for each row
    tm_total_data = [
        team_str,
        0,
        f'{team_stats["fieldGoalsMade"]}-{team_stats["fieldGoalsAttempted"]} '
        f'({round((team_stats["fieldGoalsPercentage"] * 100), 1)})',
        f'{team_stats["threePointersMade"]}-{team_stats["threePointersAttempted"]} '
        f'({round((team_stats["threePointersPercentage"] * 100), 1)})',
        f'{team_stats["freeThrowsMade"]}-{team_stats["freeThrowsAttempted"]} '
        f'({round((team_stats["freeThrowsPercentage"] * 100), 1)})',
        team_stats["reboundsOffensive"],
        team_stats["reboundsTotal"],
        team_stats["assists"],
        team_stats["turnoversTotal"],
        team_stats["steals"],
        team_stats["blocks"],
        team_stats["foulsTeam"],
        team_stats["points"],
        0,
    ]

    tm_total_row = PostGame.stat_row(*tm_total_data, team=True)

    # Each item is 1 player
    for pd in player_stats:

        # Create row for player that played
        if pd['played'] == "1":
            ps = pd['statistics']
            mp, sp, ss = parse_game_clock(ps['minutes'])
            player_data = [
                f'{pd["nameI"]}{("^^" + pd.get("position", ""))}',
                f'{mp}:{sp:02d}',
                f'{ps["fieldGoalsMade"]}-{ps["fieldGoalsAttempted"]} ({round((ps["fieldGoalsPercentage"] * 100), 1)})',
                f'{ps["threePointersMade"]}-{ps["threePointersAttempted"]} ({round((ps["threePointersPercentage"] * 100), 1)})',
                f'{ps["freeThrowsMade"]}-{ps["freeThrowsAttempted"]} ({round((ps["freeThrowsPercentage"] * 100), 1)})',
                ps["reboundsOffensive"],
                ps["reboundsTotal"],
                ps["assists"],
                ps["turnovers"],
                ps["steals"],
                ps["blocks"],
                ps["foulsPersonal"],
                ps["points"],
                round(ps["plusMinusPoints"]),
            ]

            player_rows += PostGame.stat_row(*player_data)

        elif pd["status"] == "ACTIVE":   # Add DNPs to dnp_list
            dnp_list.append(pd["nameI"])

        else:   # Add inactives to inactive_list
            inactive_list.append(pd["nameI"])

    # player_rows = "\n".join([player for player in all_players_list])
    dnp_string = "**DNP:** " + ", ".join([("***" + player + "***") for player in dnp_list])
    inactive_string = "**Inactive:** " + ", ".join([("***" + player + "***") for player in inactive_list])

    tm_total_row_top = PostGame.team_row(*tm_total_data)

    # Return Team Table w/ Away team on top
    if home_away == 'away':
        return (f"{PostGame.player_head_and_fmt(team_str)}{player_rows}"
                f"{tm_total_row}\n{dnp_string}\n\n{inactive_string}"
                f"\n\n&nbsp;\n\n",
                f"{PostGame.team_head_and_fmt()}{tm_total_row_top}")
    else:
        return (f"{PostGame.player_head_and_fmt(team_str)}{player_rows}"
                f"{tm_total_row}\n{dnp_string}\n\n{inactive_string}"
                f"\n\n&nbsp;\n\n",
                f"{tm_total_row_top}\n")


def game_boxscore(gd, ats, att, atpe, hts, htt, htpe, off):
    """Generate quarter-by-quarter table, extra game info table and added info string"""

    game_info_rows = ""
    qbq_rows = ""

    for stats, team_str in [[ats, att], [hts, htt]]:
        game_info_rows += PostGame.extra_g_info_row(
            team=team_str,
            pitp=stats['pointsInThePaint'],
            scp=stats['pointsSecondChance'],
            fbpts=stats['pointsFastBreak'],
            bigld=stats['biggestLead'],
            benpts=stats['benchPoints'],
            tottov=stats['turnoversTotal'],
            tovpts=stats['pointsFromTurnovers'],
        )

    # Generate each team quarter-by-quarter scores
    for p_stats, stats, team_str in [[atpe, ats, att], [htpe, hts, htt]]:
        q_pts = [p_stats[p]['score'] for p in range(0, gd['period'])]
        qbq_rows += PostGame.qbq_row(team_str, stats['points'], *q_pts)

    # Extra data; lead changes, times tied, gametime, attendance, officials
    officials = []
    for official in off:
        officials.append(f"{official['name']}")

    extra_string = PostGame.extra_game_string(
        lead_chng=hts['leadChanges'],
        time_tied=hts['timesTied'],
        duration=gd['duration'],
        attend=gd['attendance'],
        officials=officials,
    )

    return (f"{PostGame.qbq_head_and_fmt(gd['period'])}{qbq_rows}\n\n&nbsp;\n\n",
            f"{PostGame.extra_g_info_head_and_fmt()}{game_info_rows}\n\n&nbsp;\n\n",
            f"{extra_string}")


def generate_headline_data(away_stats, home_stats, home_away):
    """Determines win/loss, margin and final score for thread's subject.

    Arguments: game_data -> json object of game details
               home_away -> 'home' or 'away' as string; to determine win/loss
    Return: win -> win = 1, loss = 0
            margin -> abs(score difference); to determine which headline to use
            final_score -> string of final score
    """
    home_score = home_stats['points']
    away_score = away_stats['points']

    if home_away == 'home':
        win = 1 if home_score > away_score else 0
    else:
        win = 1 if away_score > home_score else 0

    margin = abs(home_score - away_score)
    final_score = f"{away_score}-{home_score}"

    return win, margin, final_score


def generate_markdown_tables(game_data, home_away):
    """Calls appropriate functions to generate a markdown boxscore.

    Arguments: game_id -> nba.com game_id
               home_away -> string of either 'home' or 'away', needed
               to determine win/loss result and which the order of player boxscores.
    Return: md_return -> body of text (string) in markdown language
            win -> win = 1, loss = 0
            margin -> abs(score difference); to determine which headline to use
            final_score -> string of final score
    """

    qtr_table, extra_info_table, btm_info = game_boxscore(
        gd=game_data,
        ats=get_value(game_data, key_paths.get("away_stats")),
        att=get_value(game_data, key_paths.get("away_tricode")),
        atpe=get_value(game_data, key_paths.get("away_periods")),
        hts=get_value(game_data, key_paths.get("home_stats")),
        htt=get_value(game_data, key_paths.get("home_tricode")),
        htpe=get_value(game_data, key_paths.get("home_periods")),
        off=get_value(game_data, key_paths.get("officials"))
    )
    away_box, top_tm_table = team_boxscore(
        get_value(game_data, key_paths.get("away_stats")),
        get_value(game_data, key_paths.get("away_players")),
        get_value(game_data, key_paths.get("away_tricode")),
        'away'
    )
    home_box, bot_tm_table = team_boxscore(
        get_value(game_data, key_paths.get("home_stats")),
        get_value(game_data, key_paths.get("home_players")),
        get_value(game_data, key_paths.get("home_tricode")),
        'home'
    )

    # Quarter by quarter table and team stats table
    md_return = f"{qtr_table}\n\n" \
                f"{top_tm_table}" \
                f"{bot_tm_table}\n\n&nbsp;\n\n"

    # Put TEAM_FOCUS team as top boxscore
    if home_away == 'home':
        md_return += f"{home_box}\n\n{away_box}\n\n{extra_info_table}\n\n{btm_info}"
    else:
        md_return += f"{away_box}\n\n{home_box}\n\n{extra_info_table}\n\n{btm_info}"

    win, margin, final_score = generate_headline_data(
        get_value(game_data, key_paths.get("away_stats")),
        get_value(game_data, key_paths.get("home_stats")),
        home_away
        )

    return md_return, win, margin, final_score
