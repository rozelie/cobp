from pyretrosheet.models.play.description import BatterEvent
from pyretrosheet.models.play.modifier import ModifierType

from cobp.stats import obp
from cobp.utils import TEAM_PLAYER_ID


class TestOBP:
    def test_obp__happy_path(self):
        obp_ = obp.OBP()
        obp_.hits = 1
        obp_.walks = 1
        obp_.hit_by_pitches = 1
        obp_.at_bats = 1
        obp_.sacrifice_flys = 1

        # numerator (1 + 1 + 1) == 3
        # denominator (1 + 1 + 1 + 1) == 4
        assert obp_.value == 0.75

    def test_obp__handles_zero_denominator(self):
        obp_ = obp.OBP()
        obp_.at_bats = 0
        obp_.walks = 0
        obp_.hit_by_pitches = 0
        obp_.sacrifice_flys = 0

        assert obp_.value == 0.0


def test_get_player_to_obp(
    mock_game,
    mock_player,
    mock_player_2,
    mock_play_builder,
    mock_event_builder,
    mock_modifier_builder,
    mock_batter_event_play_builder,
):
    mock_game.chronological_events = [
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player, 1),
        mock_batter_event_play_builder(BatterEvent.STRIKEOUT, mock_player_2, 1),
        mock_batter_event_play_builder(BatterEvent.WALK, mock_player, 2),
        mock_batter_event_play_builder(BatterEvent.NO_PLAY, mock_player_2, 2),
        mock_batter_event_play_builder(BatterEvent.HIT_BY_PITCH, mock_player, 3),
        mock_play_builder(
            mock_event_builder(
                BatterEvent.ASSISTED_FIELDED_OUT, modifiers=[mock_modifier_builder(ModifierType.SACRIFICE_FLY)]
            ),
            batter_id=mock_player.id,
            inning=4,
        ),
    ]
    games = [mock_game]
    players = [mock_player, mock_player_2]

    player_to_obp = obp.get_player_to_obp(games, players)

    assert len(player_to_obp) == 3
    assert player_to_obp[mock_player.id].value == 0.75
    assert player_to_obp[mock_player_2.id].value == 0.0
    assert player_to_obp[TEAM_PLAYER_ID].value == 0.6


def test_get_player_to_cobp__inning_has_on_base(mock_game, mock_player, mock_player_2, mock_batter_event_play_builder):
    mock_game.chronological_events = [
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player),
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player_2),
    ]
    games = [mock_game]
    players = [mock_player, mock_player_2]

    player_to_cobp = obp.get_player_to_cobp(games, players)

    assert len(player_to_cobp) == 3
    assert player_to_cobp[mock_player.id].value == 1.0
    assert player_to_cobp[mock_player_2.id].value == 1.0
    assert player_to_cobp[TEAM_PLAYER_ID].value == 1.0


def test_get_player_to_cobp__inning_has_no_on_base_skips_plays(
    mock_game, mock_player, mock_player_2, mock_batter_event_play_builder
):
    mock_game.chronological_events = [
        mock_batter_event_play_builder(BatterEvent.STRIKEOUT, mock_player),
        mock_batter_event_play_builder(BatterEvent.STRIKEOUT, mock_player_2),
    ]
    games = [mock_game]
    players = [mock_player, mock_player_2]

    player_to_cobp = obp.get_player_to_cobp(games, players)

    assert player_to_cobp[mock_player.id].value == 0.0
    assert player_to_cobp[mock_player.id].at_bats == 0
    assert player_to_cobp[mock_player_2.id].value == 0.0
    assert player_to_cobp[mock_player_2.id].at_bats == 0
    assert player_to_cobp[TEAM_PLAYER_ID].value == 0.0


def test_get_player_to_sobp__play_has_on_base_before_it_in_inning(
    mock_game, mock_player, mock_player_2, mock_batter_event_play_builder
):
    mock_game.chronological_events = [
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player),
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player_2),
    ]
    games = [mock_game]
    players = [mock_player, mock_player_2]

    player_to_sobp = obp.get_player_to_sobp(games, players)

    assert len(player_to_sobp) == 3
    assert player_to_sobp[mock_player.id].value == 0.0
    assert player_to_sobp[mock_player.id].at_bats == 0
    assert player_to_sobp[mock_player_2.id].value == 1.0
    assert player_to_sobp[TEAM_PLAYER_ID].value == 1.0


def test_get_player_to_sobp__play_has_no_on_base_before_it_in_inning_skips_play(
    mock_game, mock_player, mock_player_2, mock_batter_event_play_builder
):
    mock_game.chronological_events = [
        mock_batter_event_play_builder(BatterEvent.STRIKEOUT, mock_player),
        mock_batter_event_play_builder(BatterEvent.SINGLE, mock_player_2),
    ]

    games = [mock_game]
    players = [mock_player, mock_player_2]

    player_to_sobp = obp.get_player_to_sobp(games, players)

    assert player_to_sobp[mock_player.id].value == 0.0
    assert player_to_sobp[mock_player.id].at_bats == 0
    assert player_to_sobp[mock_player_2.id].value == 0.0
    assert player_to_sobp[mock_player_2.id].at_bats == 0
    assert player_to_sobp[TEAM_PLAYER_ID].value == 0.0
