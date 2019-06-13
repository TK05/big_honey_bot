from decimal import Decimal, ROUND_HALF_UP
import requests

from config import setup
from threads.static.templates import PostGame


SEASON = setup['season']
# TODO: This URL could change in the future.
URL_TEMPLATE = "http://data.nba.com/data/v2015/json/mobile_teams/nba/{}/scores/gamedetail/{}_gamedetail.json"


def team_boxscore(team_ident, team_data):
    """Generate markdown boxscore for each player and team"""

    # Isolate to specific team
    td = team_data['g'][team_ident]

    player_rows = ""
    dnp_list = []
    inactive_list = []

    # Create list of all column data needed for each row
    tm_total_data = [
        td['ta'], 0,
        f'{td["tstsg"]["fgm"]}-{td["tstsg"]["fga"]}'
        f' ({Decimal((td["tstsg"]["fgm"]/td["tstsg"]["fga"]*100) if td["tstsg"]["fga"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
        f'{td["tstsg"]["tpm"]}-{td["tstsg"]["tpa"]}'
        f' ({Decimal((td["tstsg"]["tpm"]/td["tstsg"]["tpa"]*100) if td["tstsg"]["tpa"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
        f'{td["tstsg"]["ftm"]}-{td["tstsg"]["fta"]}'
        f' ({Decimal((td["tstsg"]["ftm"]/td["tstsg"]["fta"]*100) if td["tstsg"]["fta"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
        td["tstsg"]["oreb"], td["tstsg"]["reb"], td["tstsg"]["ast"], td["tstsg"]["tov"], td["tstsg"]["stl"],
        td["tstsg"]["blk"], td["tstsg"]["pf"], td["s"], 0
    ]

    tm_total_row = PostGame.player_row(*tm_total_data, team=True)

    # Each item is 1 player
    for pd in td['pstsg']:

        # Create row for player that played
        if pd['totsec'] != 0:
            player_data = [
                f'{pd["fn"][0]}. {pd["ln"]}{("^^" + pd["pos"]) if pd["pos"] else ""}',
                f'{pd["min"]}:{pd["sec"]:02d}',
                f'{pd["fgm"]}-{pd["fga"]}'
                f' ({Decimal((pd["fgm"]/pd["fga"]*100) if pd["fga"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
                f'{pd["tpm"]}-{pd["tpa"]}'
                f' ({Decimal((pd["tpm"]/pd["tpa"]*100) if pd["tpa"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
                f'{pd["ftm"]}-{pd["fta"]}'
                f' ({Decimal((pd["ftm"]/pd["fta"]*100) if pd["fta"] != 0 else 0).quantize(Decimal(".1"), ROUND_HALF_UP)})',
                pd["oreb"], pd["reb"], pd["ast"], pd["tov"], pd["stl"], pd["blk"], pd["pf"], pd["pts"],
                f'{"+" if pd["pm"] > 0 else ""}{pd["pm"]}'
            ]

            player_rows += PostGame.player_row(*player_data)

        elif pd["status"] == 'A':   # Add DNPs to dnp_list
            dnp_list.append(f"{pd['fn']} {pd['ln']}")

        else:   # Add inactives to inactive_list
            inactive_list.append(f"{pd['fn']} {pd['ln']}")

    # player_rows = "\n".join([player for player in all_players_list])
    dnp_string = "**DNP:** " + ", ".join([("***" + player + "***") for player in dnp_list])
    inactive_string = "**Inactive:** " + ", ".join([("***" + player + "***") for player in inactive_list])

    tm_total_row_top = PostGame.team_row(*tm_total_data)

    # Return Team Table w/ Away team on top
    if team_ident == 'vls':
        return (f"{PostGame.player_head_and_fmt(td['ta'])}{player_rows}"
                f"{tm_total_row}\n{dnp_string}\n\n{inactive_string}"
                f"\n\n&nbsp;\n\n",
                f"{PostGame.team_head_and_fmt()}{tm_total_row_top}")
    else:
        return (f"{PostGame.player_head_and_fmt(td['ta'])}{player_rows}"
                f"{tm_total_row}\n{dnp_string}\n\n{inactive_string}"
                f"\n\n&nbsp;\n\n",
                f"{tm_total_row_top}\n")


def game_boxscore(game_data):
    """Generate quarter-by-quarter table, extra game info table and added info string"""

    atd = game_data['g']['vls']  # away team
    htd = game_data['g']['hls']  # home team
    game_info_rows = ""
    qbq_rows = ""

    for team in [atd, htd]:
        game_info_rows += PostGame.extra_g_info_row(
            team['ta'], team['tstsg']['pip'], team['tstsg']['scp'],
            team['tstsg']['fbpts'], team['tstsg']['ble'], team['tstsg']['bpts'],
            (team['tstsg']['tmtov'] + team['tstsg']['tov']), team['tstsg']['potov'])

    # Generate each team quarter-by-quarter scores
    for team in [atd, htd]:

        # Needed to properly handle games with OT
        q_1to4 = [team[f'q{q}'] for q in range(1, 5)]
        ot_quarters = []
        if game_data['g']['p'] > 4:
            ot_quarters = [team[f'ot{q}'] for q in range(1, game_data['g']['p'] - 3)]

        qbq_rows += PostGame.qbq_row(team['ta'], team['s'], *q_1to4, *ot_quarters)

    # Extra data; lead changes, times tied, gametime, attendance, officials
    officials = []
    for official in game_data['g']['offs']['off']:
        officials.append(f"{official['fn']} {official['ln']}")

    extra_string = PostGame.extra_game_string(game_data['g']['gsts']['lc'], game_data['g']['gsts']['tt'],
                                              game_data['g']['dur'], game_data['g']['at'], officials)

    return (f"{PostGame.qbq_head_and_fmt(game_data['g']['p'])}{qbq_rows}\n\n&nbsp;\n\n",
            f"{PostGame.extra_g_info_head_and_fmt()}{game_info_rows}\n\n&nbsp;\n\n",
            f"{extra_string}")


def generate_headline_data(game_data, home_away):
    """Determines win/loss, margin and final score for thread's subject.

    Arguments: game_data -> json object of game details
               home_away -> 'home' or 'away' as string; to determine win/loss
    Return: win -> win = 1, loss = 0
            margin -> abs(score difference); to determine which headline to use
            final_score -> string of final score
    """

    home_score = game_data['g']['lpla']['hs']
    away_score = game_data['g']['lpla']['vs']

    if home_away == 'home':
        win = 1 if home_score > away_score else 0
    else:
        win = 1 if away_score > home_score else 0

    margin = abs(home_score - away_score)
    final_score = f"{away_score}-{home_score}"

    return win, margin, final_score


def generate_markdown_tables(game_id, home_away):
    """Calls appropriate functions to generate a markdown boxscore.

    Arguments: game_id -> nba.com game_id
               home_away -> string of either 'home' or 'away', needed
               to determine win/loss result and which the order of player boxscores.
    Return: md_return -> body of text (string) in markdown language
            win -> win = 1, loss = 0
            margin -> abs(score difference); to determine which headline to use
            final_score -> string of final score
    """

    response = requests.get(URL_TEMPLATE.format(SEASON, game_id)).json()

    qtr_table, extra_info_table, btm_info = game_boxscore(response)
    away_box, top_tm_table = team_boxscore('vls', response)
    home_box, bot_tm_table = team_boxscore('hls', response)

    # Quarter by quarter table and team stats table
    md_return = f"{qtr_table}\n\n" \
                f"{top_tm_table}" \
                f"{bot_tm_table}\n\n&nbsp;\n\n"

    # Put TEAM_FOCUS team as top boxscore
    if home_away == 'home':
        md_return += f"{home_box}\n\n{away_box}\n\n{extra_info_table}\n\n{btm_info}"
    else:
        md_return += f"{away_box}\n\n{home_box}\n\n{extra_info_table}\n\n{btm_info}"

    win, margin, final_score = generate_headline_data(response, home_away)

    return md_return, win, margin, final_score
