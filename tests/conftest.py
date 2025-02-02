from datetime import date

import pytest
from pyretrosheet.models.base import Base
from pyretrosheet.models.game import Game
from pyretrosheet.models.game_id import GameID
from pyretrosheet.models.play import Play
from pyretrosheet.models.play.advance import Advance
from pyretrosheet.models.play.description import BatterEvent, Description, RunnerEvent
from pyretrosheet.models.play.event import Event
from pyretrosheet.models.play.modifier import Modifier, ModifierType
from pyretrosheet.models.player import Player
from pyretrosheet.models.team import TeamLocation

from cobp.models.team import Team
from cobp.stats.obp import OBP
from cobp.stats.sp import SP


@pytest.fixture
def mock_team_location() -> TeamLocation:
    return TeamLocation.HOME


@pytest.fixture
def mock_player_builder(mock_team_location):
    def player_builder(
        id: str = "player",
        name: str = "player",
        team_location: TeamLocation = mock_team_location,
        batting_order_position: int = 1,
        fielding_position: int = 1,
        is_sub: bool = False,
        raw: str = "",
    ):
        return Player(
            id=id,
            name=name,
            team_location=team_location,
            batting_order_position=batting_order_position,
            fielding_position=fielding_position,
            is_sub=is_sub,
            raw=raw,
        )

    return player_builder


@pytest.fixture
def mock_player(mock_player_builder):
    return mock_player_builder()


@pytest.fixture
def mock_player_2(mock_player_builder):
    return mock_player_builder(id="player_2", name="player_1")


@pytest.fixture
def mock_modifier_builder():
    def modifier_builder(
        type: ModifierType,
        hit_location: str | None = None,
        fielder_positions: list[int] | None = None,
        base: Base | None = None,
        raw: str = "",
    ):
        return Modifier(
            type=type,
            hit_location=hit_location,
            fielder_positions=fielder_positions,
            base=base,
            raw=raw,
        )

    return modifier_builder


@pytest.fixture
def mock_event_builder():
    def event_builder(
        batter_event: BatterEvent | None = None,
        runner_event: RunnerEvent | None = None,
        modifiers: list[Modifier] | None = None,
        advances: list[Advance] | None = None,
    ):
        return Event(
            description=Description(
                batter_event=batter_event,
                runner_event=runner_event,
                fielder_assists={},
                fielder_put_outs={},
                fielder_handlers={},
                fielder_errors={},
                put_out_at_base=None,
                stolen_base=None,
                raw="",
            ),
            modifiers=modifiers or [],
            advances=advances or [],
            raw="",
        )

    return event_builder


@pytest.fixture
def mock_play_builder(mock_player, mock_event_builder, mock_team_location):
    def play_builder(
        event: Event = mock_event_builder(),
        inning: int = 1,
        team_location: TeamLocation = mock_team_location,
        batter_id: str = mock_player.id,
        count: str = "",
        pitches: str = "",
        comments: list[str] | None = None,
        raw: str = "",
    ):
        return Play(
            inning=inning,
            team_location=team_location,
            batter_id=batter_id,
            count=count,
            pitches=pitches,
            comments=comments or [],
            event=event,
            raw=raw,
        )

    return play_builder


@pytest.fixture
def mock_batter_event_play_builder(mock_play_builder, mock_player, mock_event_builder):
    def batter_event_play_builder(
        batter_event: BatterEvent,
        player: Player = mock_player,
        inning: int = 1,
    ):
        return mock_play_builder(mock_event_builder(batter_event), batter_id=player.id, inning=inning)

    return batter_event_play_builder


@pytest.fixture
def mock_runner_event_play_builder(mock_play_builder, mock_player, mock_event_builder):
    def runner_event_play_builder(
        runner_event: RunnerEvent,
        player: Player = mock_player,
        inning: int = 1,
    ):
        return mock_play_builder(mock_event_builder(runner_event=runner_event), batter_id=player.id, inning=inning)

    return runner_event_play_builder


@pytest.fixture
def mock_team():
    return Team(
        retrosheet_id="retrosheet_id",
        location="location",
        name="name",
        start_year=2022,
        end_year=2022,
        baseball_reference_id=None,
    )


@pytest.fixture
def mock_game(mock_team, mock_player, mock_player_2):
    return Game(
        id=GameID(
            home_team_id=mock_team.retrosheet_id,
            date=date(2024, 1, 1),
            game_number=0,
            raw="",
        ),
        info={"hometeam": mock_team.retrosheet_id, "visteam": ""},
        chronological_events=[mock_player, mock_player_2],
        earned_runs={},
    )
