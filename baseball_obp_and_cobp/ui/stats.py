import streamlit as st

from baseball_obp_and_cobp.game import Game, get_players_in_games
from baseball_obp_and_cobp.player import TEAM_PLAYER_ID, Player
from baseball_obp_and_cobp.stats.aggregated import PlayerStats, PlayerToStats


def display_game(games: list[Game], player_to_stats: PlayerToStats) -> None:
    _display_legend()
    if len(games) == 1:
        _display_innings(games[0])
    _display_stats(games, player_to_stats)
    _display_footer()


def _display_legend():
    with st.expander("View Legend"):
        st.markdown(":green[GREEN]: On-Base | :orange[ORANGE]: At Bat | :red[RED]: N/A")


def _display_innings(game: Game) -> None:
    header = f"Inning Play-by-Play For {game.team.pretty_name}"
    with st.expander(f"View {header}"):
        st.header(header)
        for inning, plays in game.inning_to_plays.items():
            has_an_on_base = "Yes" if game.inning_has_an_on_base(inning) else "No"
            st.markdown(f"**Inning {inning}** (Has An On Base: {has_an_on_base})")
            for play in plays:
                player = game.get_player(play.batter_id)
                if player:
                    st.markdown(f"- {player.name}: {play.pretty_description} => :{play.color}[{play.id}]")

            st.divider()


def _display_stats(games: list[Game], player_to_stats: PlayerToStats) -> None:
    player_id_to_player = {p.id: p for p in get_players_in_games(games)}
    st.header(f"{games[0].team.pretty_name} Stats")
    _display_stats_row(
        games,
        player=Player.as_team(),
        stats=player_to_stats[TEAM_PLAYER_ID],
    )
    player_to_stats.pop(TEAM_PLAYER_ID)
    for player_id, stats in player_to_stats.items():
        player = player_id_to_player[player_id]
        if not player.plays:
            continue

        _display_stats_row(games, player, stats)


def _display_footer() -> None:
    retrosheet_notice = " ".join(
        """\
        The information used here was obtained free of
        charge from and is copyrighted by Retrosheet.  Interested
        parties may contact Retrosheet at 20 Sunset Rd.,
        Newark, DE 19711.
    """.split()
    )
    st.caption(retrosheet_notice)


def _display_stats_row(games: list[Game], player: Player, stats: PlayerStats) -> None:
    explanation_toggleable = len(games) > 1
    player_column, obp_column, cobp_column, sobp_column, ba_column, sp_column, ops_column, cops_column = st.columns(8)
    with player_column:
        st.markdown(f"**{player.name}**")
    with obp_column:
        _display_metric("OBP", stats.obp.obp, stats.obp.explanation, toggleable=explanation_toggleable)
    with cobp_column:
        _display_metric("COBP", stats.cobp.obp, stats.cobp.explanation, toggleable=explanation_toggleable)
    with sobp_column:
        _display_metric("SOBP", stats.sobp.obp, stats.sobp.explanation, toggleable=explanation_toggleable)
    with ba_column:
        _display_metric("BA", stats.ba.ba, stats.ba.explanation, toggleable=explanation_toggleable)
    with sp_column:
        _display_metric("SP", stats.sp.sp, stats.sp.explanation, toggleable=explanation_toggleable)
    with ops_column:
        _display_metric("OPS", stats.ops.ops, stats.ops.explanation, toggleable=explanation_toggleable)
    with cops_column:
        _display_metric("COPS", stats.cops.cops, stats.cops.explanation, toggleable=explanation_toggleable)
    st.divider()


def _display_metric(name: str, value: float, explanation_lines: list[str], toggleable: bool) -> None:
    metric_formatted = f"**{name} = {round(value, 3)}**"
    if not explanation_lines:
        st.markdown(metric_formatted)
        return

    if toggleable:
        with st.expander(metric_formatted):
            for line in explanation_lines:
                st.markdown(line)
    else:
        st.markdown(metric_formatted)
        for line in explanation_lines:
            st.markdown(line)
