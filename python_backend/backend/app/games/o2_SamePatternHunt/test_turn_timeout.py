import asyncio
import json
import time

from app.games.o2_SamePatternHunt.game import o2SPHGame
from app.models.player import Player


async def _noop(*args, **kwargs):
    return None


def prepared_game():
    subject = o2SPHGame("test")
    subject.state = "player_turn"
    subject.player_order = ["a", "b"]
    subject.current_player = "a"
    subject.scores = {"a": 10, "b": 10}
    subject.player_targets = {
        "a": [str((i % 16) + 1) for i in range(48)],
        "b": [str(((i + 3) % 16) + 1) for i in range(48)],
    }
    subject.player_target_index = {"a": 0, "b": 0}
    return subject


def test_timeout_counts_as_wrong_pattern_without_revealing_card():
    subject = prepared_game()
    events = []

    async def capture(payload):
        events.append(payload)

    subject.broadcast = capture
    subject.decision = {"id": 1, "player_id": "a", "kind": "primary"}
    asyncio.run(subject._decision_timeout(1, "a", 0))
    assert subject.scores["a"] == 9
    assert subject.current_player == "b"
    assert subject.timeout_counts["a"] == 1
    assert not any(event.get("type") == "card_flipped" for event in events)


def test_correct_pattern_refreshes_full_ninety_second_timer():
    subject = prepared_game()
    subject.cards = subject._init_cards()
    matching = next(card for card in subject.cards.values()
                    if card["patternId"] == subject.player_targets["a"][0])
    subject.broadcast = _noop
    subject.broadcast_to_player = _noop
    asyncio.run(subject.broadcast_game_state())
    first_id = subject.decision["id"]
    asyncio.run(subject.process_action("a", {"type": "flip", "cardId": matching["cardId"]}))
    assert subject.current_player == "a"
    assert subject.decision["id"] != first_id
    assert subject.decision["timeout_seconds"] == 90
    assert subject.decision["deadline"] > time.time() + 89


def test_second_consecutive_timeout_enables_managed_default_action():
    subject = prepared_game()
    subject.timeout_counts["a"] = 1
    subject.broadcast = _noop
    subject.decision = {"id": 2, "player_id": "a", "kind": "primary"}
    asyncio.run(subject._decision_timeout(2, "a", 0))
    assert subject.timeout_counts["a"] == 2
    assert "a" in subject.managed_players


def test_target_window_contains_previous_three_current_and_next_six():
    subject = prepared_game()
    subject.player_target_index["a"] = 8
    payloads = []

    async def capture(payload):
        payloads.append(payload)

    subject.broadcast = capture
    asyncio.run(subject.broadcast_game_state())
    window = payloads[-1]["gameInfo"]["a"]["target_window"]
    assert [item["offset"] for item in window] == list(range(-3, 7))


def test_refresh_race_still_sends_started_game_state():
    subject = prepared_game()

    class Socket:
        def __init__(self):
            self.messages = []

        async def send_text(self, data):
            self.messages.append(json.loads(data))

    socket = Socket()
    asyncio.run(subject.connect(socket, Player("a", "Alice", "")))
    assert any(message.get("type") == "game_state" for message in socket.messages)
    assert any(message.get("type") == "player_sync" for message in socket.messages)
