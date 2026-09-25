from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

from app.games.base import BaseGame
from app.models.player import Player
from .source_adapter import generate_from_original


class MazeRaceGame(BaseGame):
    """Server-authoritative memory maze for classic racing and orienteering."""

    DIRECTIONS = {"up": (-1, 0, 0), "left": (0, -1, 1), "right": (0, 1, 2), "down": (1, 0, 3)}
    CORNERS = (0, 7, 63, 56)

    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.config = {"min_players": 2, "max_players": 2}
        self.game_rules = {"game_mode": "classic", "rows": 8, "cols": 8, "walls_hidden": True,
                           "reveal_hit_walls": True, "wall_hit_threshold": 2,
                           "movement_mode": "turns", "steps_per_turn": 3}
        self.persistent_players: Dict[str, Player] = {}
        self.player_order: List[str] = []
        self.walls: List[List[int]] = []
        self.positions: Dict[str, int] = {}
        self.targets: Dict[str, Any] = {}
        self.steps: Dict[str, int] = {}
        self.start_positions: Dict[str, int] = {}
        # The immutable first corner is used for victory; start_positions is the latest respawn point.
        self.home_positions: Dict[str, int] = {}
        self.visited_checkpoints: Dict[str, List[int]] = {}
        self.wall_hit_counts: Dict[str, Dict[str, int]] = {}
        self.current_player: Optional[str] = None
        self.turn_steps = 0
        self.turn_number = 1
        self.started_at: Optional[float] = None
        self.winner: Optional[str] = None
        self.finish_reason: Optional[str] = None
        self.seed: Optional[int] = None

    async def connect(self, websocket: WebSocket, player: Player) -> None:
        self.connections[websocket] = player.id
        self.persistent_players[player.id] = player
        self.disconnected_players.discard(player.id)
        if self.state != "waiting":
            await self.broadcast_game_state()

    async def handle_event(self, websocket, event, player_id):
        if event.get("type") == "action" and event.get("action") == "move":
            await self.move(player_id, str(event.get("direction", "")))

    async def update_rules(self, rules: Dict[str, Any]) -> None:
        requested = rules.get("rules", rules)
        if self.state != "waiting":
            return
        if "reveal_hit_walls" in requested:
            self.game_rules["reveal_hit_walls"] = bool(requested["reveal_hit_walls"])
        if "wall_hit_threshold" in requested:
            self.game_rules["wall_hit_threshold"] = max(1, min(10, int(requested["wall_hit_threshold"])))
        if requested.get("movement_mode") in {"turns", "free"}:
            self.game_rules["movement_mode"] = requested["movement_mode"]
        if requested.get("game_mode") in {"classic", "orienteering"}:
            game_mode = requested["game_mode"]
            self.game_rules["game_mode"] = game_mode
            self.config.update({"min_players": 1, "max_players": 4} if game_mode == "orienteering"
                               else {"min_players": 2, "max_players": 2})

    async def start_game(self, mode="multi") -> None:
        ids = [pid for pid in self.room.players if pid in self.persistent_players]
        game_mode = self.game_rules["game_mode"]
        valid_count = 1 <= len(ids) <= 4 if game_mode == "orienteering" else len(ids) == 2
        if not valid_count:
            message = "定向越野支持 1–4 名玩家" if game_mode == "orienteering" else "经典竞速需要两名玩家"
            await self.broadcast({"type": "error", "message": message})
            if self.room:
                self.room.status = "waiting"
                await self.room.broadcast_state(extra_message={"error": message})
            return
        self.player_order = ids
        self.seed = random.SystemRandom().randrange(1, 2**31)
        self.walls = generate_from_original(self.seed)
        self.start_positions = ({pid: self.CORNERS[index] for index, pid in enumerate(ids)}
                                if game_mode == "orienteering" else {ids[0]: 56, ids[1]: 63})
        self.home_positions = dict(self.start_positions)
        self.positions = dict(self.start_positions)
        self.targets = ({pid: list(self.CORNERS) for pid in ids} if game_mode == "orienteering"
                        else {ids[0]: 7, ids[1]: 0})
        self.visited_checkpoints = {pid: [] for pid in ids}
        self.steps = {pid: 0 for pid in ids}
        self.wall_hit_counts = {pid: {} for pid in ids}
        self.current_player = ids[0] if self.game_rules["movement_mode"] == "turns" else None
        self.turn_steps, self.turn_number = 0, 1
        self.winner = self.finish_reason = None
        self.started_at = time.time()
        self.state = "playing"
        await self.broadcast_game_state()

    async def move(self, player_id: str, direction: str) -> None:
        if self.state != "playing" or player_id not in self.positions:
            return
        if self.game_rules["movement_mode"] == "turns" and player_id != self.current_player:
            await self.broadcast_to_player(player_id, {"type": "error", "message": "现在不是你的回合"})
            return
        spec = self.DIRECTIONS.get(direction)
        if not spec:
            await self.broadcast_to_player(player_id, {"type": "error", "message": "未知移动方向"})
            return
        row_delta, col_delta, wall_index = spec
        current = self.positions[player_id]
        row, col = divmod(current, 8)
        next_row, next_col = row + row_delta, col + col_delta
        inside = 0 <= next_row < 8 and 0 <= next_col < 8
        if not inside or self.walls[current][wall_index]:
            hit_count, revealed = 0, False
            if inside:
                neighbor = next_row * 8 + next_col
                hit_count, revealed = self._record_wall_hit(player_id, current, neighbor)
                self.positions[player_id] = self.start_positions[player_id]
                if self.game_rules["movement_mode"] == "turns":
                    self._advance_turn()
            await self.broadcast_to_player(player_id, {"type": "move_rejected", "position": current,
                "direction": direction, "hit_count": hit_count, "wall_revealed": revealed})
            if inside:
                await self.broadcast_game_state()
            return
        self.positions[player_id] = next_row * 8 + next_col
        self.steps[player_id] += 1
        if self.game_rules["game_mode"] == "orienteering":
            self._update_orienteering_progress(player_id)
        elif self.positions[player_id] == self.targets[player_id]:
            self._finish(player_id, "reached_target")
        if self.state == "playing" and self.game_rules["movement_mode"] == "turns":
            self.turn_steps += 1
            if self.turn_steps >= self.game_rules["steps_per_turn"]:
                self._advance_turn()
        await self.broadcast_game_state()

    async def broadcast_game_state(self) -> None:
        common = {"type": "game_state", "state": self.state, "rows": 8, "cols": 8,
            "positions": self.positions, "targets": self.targets, "start_positions": self.start_positions,
            "home_positions": self.home_positions,
            "checkpoints": list(self.CORNERS) if self.game_rules["game_mode"] == "orienteering" else [],
            "visited_checkpoints": self.visited_checkpoints, "steps": self.steps,
            "current_player": self.current_player, "turn_steps": self.turn_steps,
            "turn_number": self.turn_number, "started_at": self.started_at,
            "winner": self.winner, "finish_reason": self.finish_reason, "rules": self.game_rules,
            "players": {pid: {"id": player.id, "name": player.name, "avatar": player.avatar,
                "connected": pid in self.connections.values(), "side": index}
                for index, pid in enumerate(self.player_order)
                if (player := self.persistent_players.get(pid)) is not None}}
        for player_id in set(self.connections.values()):
            payload = dict(common)
            payload["walls"] = self.walls if self.state == "finished" else []
            payload["visible_walls"] = self._visible_walls_for(player_id)
            await self.broadcast_to_player(player_id, payload)

    @staticmethod
    def _wall_key(first_cell: int, second_cell: int) -> str:
        low, high = sorted((first_cell, second_cell))
        return f"{low}:{high}"

    def _record_wall_hit(self, player_id: str, first_cell: int, second_cell: int) -> tuple[int, bool]:
        key = self._wall_key(first_cell, second_cell)
        counts = self.wall_hit_counts.setdefault(player_id, {})
        counts[key] = counts.get(key, 0) + 1
        revealed = bool(self.game_rules["reveal_hit_walls"] and counts[key] >= self.game_rules["wall_hit_threshold"])
        return counts[key], revealed

    def _visible_walls_for(self, player_id: str) -> List[List[int]]:
        if not self.game_rules["reveal_hit_walls"]:
            return []
        visible = []
        for key, count in self.wall_hit_counts.get(player_id, {}).items():
            if count < self.game_rules["wall_hit_threshold"]:
                continue
            first, second = (int(value) for value in key.split(":"))
            delta = second - first
            if delta == 1:
                visible.extend([[first, 2], [second, 1]])
            elif delta == 8:
                visible.extend([[first, 3], [second, 0]])
        return visible

    def _update_orienteering_progress(self, player_id: str) -> None:
        position = self.positions[player_id]
        home = self.home_positions.get(player_id, self.start_positions[player_id])
        visited = self.visited_checkpoints.setdefault(player_id, [])
        if position in self.CORNERS and position != home and position not in visited:
            visited.append(position)
            self.start_positions[player_id] = position
        if position == home and (set(self.CORNERS) - {home}).issubset(visited):
            self._finish(player_id, "orienteering_complete")

    def _finish(self, player_id: str, reason: str) -> None:
        self.winner, self.finish_reason, self.state = player_id, reason, "finished"
        if self.room:
            self.room.status = "ended"

    def _advance_turn(self) -> None:
        if not self.player_order or self.current_player not in self.player_order:
            return
        index = self.player_order.index(self.current_player)
        self.current_player = self.player_order[(index + 1) % len(self.player_order)]
        self.turn_steps = 0
        self.turn_number += 1
