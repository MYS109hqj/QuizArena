import asyncio
import json

from app.games.o3_MemorialBanquet.game import o3MBGame
from app.models.player import Player


class Socket:
    def __init__(self):
        self.messages = []

    async def send_text(self, data):
        self.messages.append(json.loads(data))


def test_waiting_room_reconnect_does_not_read_uninitialized_game_data():
    subject = o3MBGame("room")
    player = Player("1007", "Alice", "")
    subject.players[player.id] = player
    subject.disconnected_players.add(player.id)
    socket = Socket()
    asyncio.run(subject.connect(socket, player))
    assert player.id not in subject.disconnected_players
    assert any(message.get("type") == "game_state" for message in socket.messages)


def test_refresh_race_sends_full_started_game_state():
    subject = o3MBGame("room")
    subject.state = "player_turn"
    subject.player_order = ["1007"]
    subject.current_player = "1007"
    subject.scores = {"1007": -10}
    subject.error_counts = {"1007": 0}
    subject.cards = subject._init_cards()
    socket = Socket()
    asyncio.run(subject.connect(socket, Player("1007", "Alice", "")))
    message_types = {message.get("type") for message in socket.messages}
    assert "game_state" in message_types
    assert "cards_sync" in message_types
    assert "player_sync" in message_types

