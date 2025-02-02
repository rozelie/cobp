import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping

import pandas as pd
from pyretrosheet.models.game import Game
from pyretrosheet.views import get_team_players

from cobp.models.team import Team
from cobp.stats.ba import BA, get_player_to_ba
from cobp.stats.basic import BasicStats, get_player_to_basic_stats
from cobp.stats.derived import COPS, LOOPS, OPS, SOPS
from cobp.stats.obp import OBP, get_player_to_cobp, get_player_to_loop, get_player_to_obp, get_player_to_sobp
from cobp.stats.runs import Runs, get_player_to_runs
from cobp.stats.sp import SP, get_player_to_csp, get_player_to_lsp, get_player_to_sp, get_player_to_ssp
from cobp.utils import build_team_player

logger = logging.getLogger(__name__)


@dataclass
class PlayerStats:
    obp: OBP
    cobp: OBP
    sobp: OBP
    loop: OBP
    sp: SP
    csp: SP
    lsp: SP
    ssp: SP
    ba: BA
    basic: BasicStats
    runs: Runs

    @property
    def ops(self) -> OPS:
        return OPS(obp=self.obp, sp=self.sp)

    @property
    def cops(self) -> COPS:
        return COPS(cobp=self.cobp, csp=self.csp)

    @property
    def loops(self) -> LOOPS:
        return LOOPS(loop=self.loop, lsp=self.lsp)

    @property
    def sops(self) -> SOPS:
        return SOPS(sobp=self.sobp, ssp=self.ssp)


PlayerToStats = dict[str, PlayerStats]


def get_player_to_stats(games: list[Game], team: Team, year: int) -> PlayerToStats:
    players = get_team_players(games, team.retrosheet_id)
    player_to_obp = get_player_to_obp(games, players)
    player_to_cobp = get_player_to_cobp(games, players)
    player_to_sobp = get_player_to_sobp(games, players)
    player_to_loop = get_player_to_loop(games, players)
    player_to_ba = get_player_to_ba(games, players)
    player_to_sp = get_player_to_sp(games, players)
    player_to_csp = get_player_to_csp(games, players)
    player_to_lsp = get_player_to_lsp(games, players)
    player_to_ssp = get_player_to_ssp(games, players)
    player_to_basic_stats = get_player_to_basic_stats(games, players)
    player_to_runs = get_player_to_runs(year, team, players, player_to_basic_stats)
    all_players = [build_team_player(), *players]
    return {
        player.id: PlayerStats(
            obp=player_to_obp.get(player.id) or OBP(),
            cobp=player_to_cobp.get(player.id) or OBP(),
            sobp=player_to_sobp.get(player.id) or OBP(),
            loop=player_to_loop.get(player.id) or OBP(),
            ba=player_to_ba.get(player.id) or BA(),
            sp=player_to_sp.get(player.id) or SP(),
            csp=player_to_csp.get(player.id) or SP(),
            lsp=player_to_lsp.get(player.id) or SP(),
            ssp=player_to_ssp.get(player.id) or SP(),
            basic=player_to_basic_stats.get(player.id) or BasicStats(),
            runs=player_to_runs.get(player.id) or Runs(),
        )
        for player in all_players
    }


def get_player_to_stats_df(
    games: list[Game],
    player_to_stats: PlayerToStats,
    team: Team,
    year: int,
) -> pd.DataFrame:
    players = [build_team_player(), *get_team_players(games, team.retrosheet_id)]
    player_id_to_player = {p.id: p for p in players}
    data: Mapping[str, list[str | float | int]] = defaultdict(list)
    for player_id, stats in player_to_stats.items():
        player = player_id_to_player[player_id]
        data["Team"].append(team.name)
        data["Year"].append(year)
        data["Player"].append(player.name)
        data["ID"].append(player.name)
        data["G"].append(stats.basic.games)
        data["AB"].append(stats.basic.at_bats)
        data["H"].append(stats.basic.hits)
        data["W"].append(stats.basic.walks)
        data["HBP"].append(stats.basic.hit_by_pitches)
        data["SF"].append(stats.basic.sacrifice_flys)
        data["S"].append(stats.basic.singles)
        data["D"].append(stats.basic.doubles)
        data["T"].append(stats.basic.triples)
        data["HR"].append(stats.basic.home_runs)
        data["R"].append(stats.runs.runs)
        data["RBI"].append(stats.runs.rbis)
        data["OBP"].append(stats.obp.value)
        data["COBP"].append(stats.cobp.value)
        data["LOOP"].append(stats.loop.value)
        data["SOBP"].append(stats.sobp.value)
        data["BA"].append(stats.ba.value)
        data["SP"].append(stats.sp.value)
        data["CSP"].append(stats.csp.value)
        data["LSP"].append(stats.lsp.value)
        data["SSP"].append(stats.ssp.value)
        data["OPS"].append(stats.ops.value)
        data["COPS"].append(stats.cops.value)
        data["LOOPS"].append(stats.loops.value)
        data["SOPS"].append(stats.sops.value)

    return pd.DataFrame(data=data)


def get_player_to_game_stat_df(
    games: list[Game], team: Team, player_to_stats: PlayerToStats, stat_name: str
) -> pd.DataFrame:
    players = [build_team_player(), get_team_players(games, team.retrosheet_id)]
    player_id_to_player = {p.id: p for p in players}
    data: Mapping[str, list[str | float]] = defaultdict(list)
    for game_id, player_game_stat in _get_game_to_player_stat(games, team, player_to_stats, stat_name).items():
        data["Game"].append(game_id)
        for player_id, game_stat in player_game_stat.items():
            player = player_id_to_player[player_id]
            data[player.name].append(game_stat)

    return pd.DataFrame(data=data)


def _get_game_to_player_stat(
    games: list[Game], team: Team, player_to_stats: PlayerToStats, stat_name: str
) -> Mapping[str, Mapping[str, float]]:
    players = get_team_players(games, team.retrosheet_id)
    player_id_to_player = {p.id for p in players}
    game_to_player_stat: Mapping[str, Mapping[str, float]] = defaultdict(dict)
    for player_id, _ in player_id_to_player.items():
        if player_to_stats[player_id].basic.at_bats == 0:
            continue

        player_stats = player_to_stats[player_id]
        player_stat = getattr(player_stats, stat_name)
        for game in games:
            player_game_stat = player_stat.game_to_stat.get(game.id)
            player_game_stat_value = player_game_stat.value if player_game_stat else None
            game_to_player_stat[game.id][player_id] = player_game_stat_value  # type: ignore

    return game_to_player_stat
