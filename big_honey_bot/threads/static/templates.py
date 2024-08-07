from big_honey_bot.helpers import hidden_tags


class PostGame(object):

    @staticmethod
    def top_links(espn_id, nba_id):
        top_links = (
                f"**ESPN:** [recap](https://www.espn.com/nba/recap/_/gameId/{espn_id}) -"
                f" [boxscore](https://www.espn.com/nba/boxscore/_/gameId/{espn_id}) -"
                f" [gamecast](https://www.espn.com/nba/game/_/gameId/{espn_id}) | "
                f"**NBA.com:** [boxscore](https://www.nba.com/game/{nba_id}) -"
                f" [shotchart](https://www.nba.com/game/{nba_id}/game-charts)")

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
            f"{times[0]}|**NBA** [Boxscore]({nba_links[0]}) - [Shotchart]({nba_links[1]})|{arena}|\n"
            f"{times[1]}|**ESPN** [Boxscore]({espn_links[0]}) - [Gamecast]({espn_links[1]})|{city}|\n"
            f"{times[2]}|**TV:** {tv}|**Team Subreddits**|\n"
            f"{times[3]}|**Radio:** {radio}| r/{subreddits[0]}|\n"
            f"{times[4]}|**Streams:** [NBAbite](https://nbabite.com)| r/{subreddits[1]}\n"
        )

        return table

    @staticmethod
    def headline(thr_type, our_team, our_wins, our_loss, home_away, opp, opp_wins, opp_loss, date, time):

        if thr_type == 'pre':
            headline = "GDT: "
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
    def pre_game_body(time, tz, url, arena, city, tv, radio, previews):
        body = (
            f"**When:** [{time} {tz}]"
            f"({url}) *(click for local time)*\n\n"
            f"**Where:** {arena} - {city}\n\n"
            f"**TV:** {tv}\n\n"
            f"**Radio:** {radio}\n\n***\n\n"
            f"**Previews:** {previews}\n\n"
            f"**Podcasts:** \n\n***\n\n"
            f"**Daily Listening:** \n"
        )

        return body

    @staticmethod
    def lineup_head_and_fmt(away_abv, home_abv, lineup_list):
        lineup_header = (
            f"##Starters\n\n"
            f"**[](/{away_abv}){away_abv}** - {lineup_list[0]}|**[](/{home_abv}){home_abv}** - {lineup_list[0]}|\n"
            f"|:--|:--|\n")

        return lineup_header

    @staticmethod
    def lineup_rows(team_lineups):
        lineup_rows = ""

        for i in range(len(team_lineups[0])):
            lineup_rows += (
                f"**{team_lineups[0][i][0]}** {team_lineups[0][i][1]}|"
                f"**{team_lineups[1][i][0]}** {team_lineups[1][i][1]}|\n"
            )

        return lineup_rows

    @staticmethod
    def injuries_head_and_fmt(away_abv, home_abv):
        injuries_header = (
            f"##Injuries\n\n"
            f"**[](/{away_abv}){away_abv}**|**[](/{home_abv}){home_abv}**|\n"
            f"|:--|:--|\n")

        return injuries_header

    @staticmethod
    def injuries_rows(team_injuries):
        injuries_rows = ""

        for i in range(max(len(team_injuries[0]), len(team_injuries[1]))):

            try:
                away_row = f"{team_injuries[0][i][0]} - {team_injuries[0][i][1]}|"
            except IndexError:
                away_row = "||"

            try:
                home_row = f"{team_injuries[1][i][0]} - {team_injuries[1][i][1]}|"
            except IndexError:
                home_row = ""

            injuries_rows += f"{away_row}{home_row}\n"

        return injuries_rows

    @staticmethod
    def betting_head_and_fmt():
        betting_header = (
            f"##Betting Odds\n\n"
            f"|**Moneyline**|**Spread**|**Over/Under**|\n"
            f"|:--:|:--:|:--:|\n")

        return betting_header

    @staticmethod
    def betting_rows(betting_odds, time_now):
        betting_row = (
            f'|{betting_odds[0]}|{betting_odds[1]}|{betting_odds[2]}|\n' \
            f'{time_now}'
        )
        
        return betting_row


class ThreadStats(object):

    @staticmethod
    def format_post(d):
        """Formats submission given thread stats."""

        thread_type_map = {
            'off': "Off Day",
            'pre': "Pre-Game",
            'game': "Game",
            'post': "Post Game"
        }

        comment = f"##BHB's {thread_type_map[d['thread_type']]} Thread Stats\n\n&nbsp;\n\n" \
            f"**Posts:** {d['num_comments']}\n\n" \
            f"**Bees:** {d['len_all_authors']}\n\n" \
            f"**Honey Harvested:** +{d['total_karma']}\n\n"

        try:
            karma_per_comment = round((d['total_karma'] / d['num_comments']), 2)
        except ZeroDivisionError:
            karma_per_comment = 0

        comment += f"**Honey/Post Avg.:** {karma_per_comment}\n\n&nbsp;\n\n" \
            f"**BHB's POTT:** +{d['top_comment'][1]} Honey\n" \
            f">[{d['top_comment'][0]}]({d['top_comment'][3]})\n"

        for line in d['top_comment'][2].split("\n\n"):
            comment += f">>{line}\n\n"

        comment += f"&nbsp;\n\n" \
            f"**Busiest Bee:** {d['most_posts'][0]} w/ {d['most_posts'][1]} Posts\n\n" \
            f"**Most Honey:** {d['most_karma'][0]} +{d['most_karma'][1]} Honey\n\n&nbsp;\n\n" \
            f"**BHB's Top-Bees**\n\n" \
            f"Bee|Posts|Honey|H/P|\n" \
            f":-|:-:|:-:|:-:|\n"

        for poster in d['top_posters']:
            comment += f"**{poster[0]}**|{poster[1]}|+{poster[2]}|{poster[3]}|\n"

        return comment


class LineupInjuryOdds(object):

    @staticmethod
    def format_body(l_headers, l_rows, i_header, i_rows, b_header, b_rows):
        sep = "\n\n&nbsp;\n\n"
        body = (
            f"{hidden_tags['lio_start']}\n" \
            f"{l_headers}{l_rows}" \
            f"{sep}" \
            f"{i_header}{i_rows}" \
            f"{sep}" \
            f"{b_header}{b_rows}" \
            f"\n{hidden_tags['lio_end']}"
        )

        return body
