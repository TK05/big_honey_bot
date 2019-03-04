# I stuck most templates in here to see if it's a big easier to manage


class PostGame(object):

    @staticmethod
    def top_links(espn_recap, espn_box, espn_gc, nba_box, nba_shot):
        top_links = (
                f"**ESPN:** [recap]({espn_recap}) -"
                f" [boxscore]({espn_box}) -"
                f" [gamecast]({espn_gc}) | "
                f"**NBA.com:** [boxscore]({nba_box}) -"
                f" [shotchart]({nba_shot})")

        return top_links

    @staticmethod
    def extra_g_info_head_and_fmt():
        header = f"||**PITP**|**2^^nd PTS**|**FB PTS**|**BIG LD**|**BEN PTS**|**TOT TOV**|**TOV PTS**||"
        fmt = "|:---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|"

        return f"{header}\n{fmt}\n"

    @staticmethod
    def extra_g_info_row(team, pitp, scp, fbpts, bigld, benpts, tottov, tovpts):
        row = f"**{team}**|{pitp}|{scp}|{fbpts}|{bigld}|{benpts}|{tottov}|{tovpts}|[](/{team})|\n"

        return row

    @staticmethod
    def qbq_head_and_fmt(quarters):
        header = "||"
        fmt = "|:---|"
        for quarter in range(1, quarters + 1):
            fmt += ":--:|"
            if quarter < 5:
                header += f"**Q{quarter}**|"
            else:
                header += f"**OT{quarter - 4}**|"
        header += "**Final**||"
        fmt += ":--:|:--:|"

        return f"{header}\n{fmt}\n"

    @staticmethod
    def qbq_row(team, final, *args):
        row = f"**{team}**|"
        for arg in args:
            row += f"**{arg}**|"
        row += f"**{final}**|[](/{team})|\n"

        return row

    @staticmethod
    def extra_game_string(lead_chng, time_tied, duration, attend, officials):
        ret_str = (f"**Lead Changes: {lead_chng}** | "
                   f"**Times Tied: {time_tied}** | "
                   f"**Gametime: {duration}** | "
                   f"**Attendance: {attend}**\n\n"
                   f"*Officials: {', '.join([official for official in officials])}*")

        return ret_str

    @staticmethod
    def player_head_and_fmt(team):
        header = (
            f"**[](/{team}){team}**|"
            f"**Min**|**FG**|**3PT**|**FT**|**OR**|**Reb**|**Ast**|**TO**|"
            f"**Stl**|**Blk**|**PF**|**Pts**|**+/-**|"
        )
        fmt = "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"

        return f"{header}\n{fmt}\n"

    @staticmethod
    def player_row(name, mp, fg, tp, ft, oreb, reb, ast, tov, stl, blk, pf, pts, pm, team=False):
        if not team:
            row = f"{name}|{mp}|{fg}|{tp}|{ft}|{oreb}|{reb}|{ast}|{tov}|{stl}|{blk}|{pf}|{pts}|{pm}|"
        else:
            row = (f"**Totals**||**{fg}**|**{tp}**|**{ft}**|**{oreb}**|"
                   f"**{reb}**|**{ast}**|**{tov}**|**{stl}**|**{blk}**|**{pf}**|**{pts}**||")

        return f"{row}\n"

    @staticmethod
    def team_head_and_fmt():
        header = (
            f"**Team**|**FG**|**3PT**|**FT**|**OR**|**Reb**|"
            f"**Ast**|**TO**|**Stl**|**Blk**|**PF**|**Pts**|"
        )

        fmt = "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"

        return f"{header}\n{fmt}\n"

    @staticmethod
    def team_row(team_abv, min, fg, tp, ft, oreb, reb, ast, tov, stl, blk, pf, pts, team=True):
        row = f"[](/{team_abv})**{team_abv}**|**{fg}**|**{tp}**|**{ft}**|**{oreb}**|" \
              f"**{reb}**|**{ast}**|**{tov}**|**{stl}**|**{blk}**|**{pf}**|**{pts}**|"

        return f"{row}\n"


class Game(object):

    @staticmethod
    def gen_info_table(times, tv, radio, nba_links, espn_links, arena, city, subreddits):
        table = (
            f"##General Information\n\n"
            f"**TIME**|**MEDIA**|**LOCATION**|\n"
            f"|:--|:--|:--|\n"
            f"{times[0]}|**TV:** {tv}|{arena}|\n"
            f"{times[1]}|**Radio:** {radio}|{city}|\n"
            f"{times[2]}|**Streams:** r/nbastreams|**Team Subreddits**|\n"
            f"{times[3]}|**NBA** [Boxscore]({nba_links[0]}) - "
            f"[Shotchart]({nba_links[1]})| r/{subreddits[0]}|\n"
            f"{times[4]}|**ESPN** [Boxscore]({espn_links[0]}) - "
            f"[Gamecast]({espn_links[1]})| r/{subreddits[1]}\n"
        )

        return table

    @staticmethod
    def headline(thr_type, our_team, our_wins, our_loss, home_away, opp, opp_wins, opp_loss, date, time):

        if thr_type == 'pre':
            headline = "GAME DAY THREAD: "
        else:
            headline = "GAME THREAD: "

        if home_away == '@':
            headline += (
                f"{our_team} ({our_wins}-{our_loss}) "
                f"{home_away} {opp} ({opp_wins}-{opp_loss}) | "
                f"{date} - {time}"
            )
        else:
            headline += (
                f"{opp} ({opp_wins}-{opp_loss}) "
                f"{home_away} {our_team} ({our_wins}-{our_loss}) | "
                f"{date} - {time}"
            )

        return headline

    @staticmethod
    def pre_game_body(time, tz, url, arena, city, tv, radio):
        body = (
            f"**When:** [{time} {tz}]"
            f"({url}) *(click for local time)*\n\n"
            f"**Where:** {arena} - {city}\n\n"
            f"**TV:** {tv}\n\n"
            f"**Radio:** {radio}\n\n***\n\n"
            f"**Previews:** \n\n"
            f"**Podcasts:** \n\n***\n\n"
            f"**Daily Listening:** \n"
        )

        return body

    @staticmethod
    def lineup_head_and_fmt(away_abv, home_abv):
        lineup_header = (
            f"##Probable Starters\n\n"
            f"**[](/{away_abv}){away_abv}**|**AST/G**|**REB/G**|**PTS/G**|"
            f"**[](/{home_abv}){home_abv}**|**AST/G**|**REB/G**|**PTS/G**|\n"
            f"|:--|:--:|:--:|:--:|:--|:--:|:--:|:--:|\n")

        return lineup_header

    @staticmethod
    def lineup_rows(team_lineups):
        lineup_rows = ""

        for i in range(len(team_lineups[0])):
            lineup_rows += (
                f"**{team_lineups[0][i][1]}** {team_lineups[0][i][0]}|"
                f"{team_lineups[0][i][2]}|{team_lineups[0][i][3]}|{team_lineups[0][i][4]}|"
                f"**{team_lineups[1][i][1]}** {team_lineups[1][i][0]}|"
                f"{team_lineups[1][i][2]}|{team_lineups[1][i][3]}|{team_lineups[1][i][4]}|\n"
            )

        return lineup_rows

    @staticmethod
    def injuries_head_and_fmt(away_abv, home_abv):
        injuries_header = (
            f"##Injuries\n\n"
            f"**[](/{away_abv}){away_abv}**|"
            f"**[](/{home_abv}){home_abv}**|\n"
            f"|:--|:--|\n")

        return injuries_header

    @staticmethod
    def injuries_rows(team_injuries):
        injuries_rows = ""

        for i in range(max(len(team_injuries[0]), len(team_injuries[1]))):

            try:
                away_row = f"{team_injuries[0][i][0]} ({team_injuries[0][i][1]})|"
            except IndexError:
                away_row = ""

            try:
                home_row = f"{team_injuries[1][i][0]} ({team_injuries[1][i][1]})|"
            except IndexError:
                home_row = ""

            injuries_rows += f"{away_row}{home_row}\n"

        return injuries_rows

    @staticmethod
    def betting_head_and_fmt():
        betting_header = (
            f"##Betting Odds\n\n"
            f"||**Moneyline**|**Spread**|**Over/Under**|**Implied Totals**|\n"
            f"|:--:|:--:|:--:|:--:|:--:|\n")

        return betting_header

    @staticmethod
    def betting_rows(betting_odds, team_abv):
        betting_rows = ""

        for i, row in enumerate(betting_odds):
            betting_rows += f"[](/{team_abv[i]})|"
            for odd in row:
                betting_rows += f"{odd}|"
            betting_rows += "\n"

        return betting_rows
