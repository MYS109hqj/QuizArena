import asyncio

from app.games.o3_MemorialBanquet.game import o3MBGame
from app.models.player import Player


async def _noop(*args, **kwargs):
    return None


def manual_game():
    subject = o3MBGame("test")
    subject.players = {
        "a": Player("a", "Alice", ""),
        "b": Player("b", "Bob", ""),
    }
    subject.game_rules["manual_placement"] = True
    subject.broadcast = _noop
    subject.broadcast_to_player = _noop
    asyncio.run(subject.start_game(mode="multi"))
    return subject


def test_manual_placement_starts_with_zero_cells_and_one_to_n_hands():
    subject = manual_game()
    assert subject.phase == "placement"
    assert all(card["number"] == 0 for card in subject.cards.values())
    assert sorted(subject.placement_hands["a"]) == list(range(1, 7))
    assert sorted(subject.placement_hands["b"]) == list(range(1, 7))
    assert subject.action_timeout_seconds == 60


def test_players_can_finish_alternating_manual_placement():
    subject = manual_game()

    async def place_all():
        while subject.phase == "placement":
            player_id = subject.current_player
            card_id = next(card for card in subject.cards if card not in subject.placement_placed)
            await subject._place_number(player_id, card_id, min(subject.placement_hands[player_id]))

    asyncio.run(place_all())
    assert subject.phase == "flipping"
    assert sorted(card["number"] for card in subject.cards.values()) == [
        number for number in range(1, 7) for _ in range(2)
    ]


def test_placement_timeout_uses_smallest_number_and_smallest_cell():
    subject = manual_game()
    player_id = subject.current_player
    first_card = next(iter(subject.cards))
    subject.decision = {"id": 1, "player_id": player_id, "kind": "placement"}
    asyncio.run(subject._decision_timeout(1, player_id, 0))
    assert subject.cards[first_card]["number"] == 1
    assert first_card in subject.placement_placed
    assert subject.timeout_counts[player_id] == 1


def test_flip_timeout_skips_without_flip_and_counts_as_error():
    subject = manual_game()
    subject.phase = "flipping"
    subject.scores = {"a": -10, "b": -10}
    subject.error_counts = {"a": 0, "b": 0}
    subject.current_player = "a"
    subject.decision = {"id": 2, "player_id": "a", "kind": "flip"}
    asyncio.run(subject._decision_timeout(2, "a", 0))
    assert subject.scores["a"] == -11
    assert subject.error_counts["a"] == 1
    assert subject.current_player == "b"
    assert subject.current_flip_cards == []


def test_second_timeout_enables_managed_default_behavior():
    subject = manual_game()
    player_id = subject.current_player
    subject.timeout_counts[player_id] = 1
    subject.decision = {"id": 3, "player_id": player_id, "kind": "placement"}
    asyncio.run(subject._decision_timeout(3, player_id, 0))
    assert subject.timeout_counts[player_id] == 2
    assert player_id in subject.managed_players
