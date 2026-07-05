import json
import time
import asyncio
from typing import Dict, Any, List
from fastapi import WebSocket
from app.games.roundBase import RoundBaseGame
from app.models.player import Player
import random
from datetime import datetime
from app.database import get_db
from app.models.user import User

class o999TemplateGame(RoundBaseGame):
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.total_score: int = 0
        self.target_score: int = 100
        self.scores: Dict[str, int] = {}
        self.locked: bool = False

        self.config: Dict[str, Any] = {
            "max_players": 5,
            "min_players": 1
        }

        self.game_rules = {
            "allowSimultaneousActions": False,
            "actionLockEnabled": True
        }

    async def handle_event(self, websocket, event, player_id):
        if event is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "无效事件"})
            return

        if event.get("type") == "update_rules":
            await self.update_rules(event)
            return

        if event.get("type") == "action":
            action = event.get("action")
            await self.handle_player_action(player_id, action)

    async def update_rules(self, settings):
        if "rules" in settings:
            self.game_rules.update(settings["rules"])
            await self.broadcast({
                "type": "rules_updated",
                "rules": self.game_rules
            })

    async def start_game(self, mode="single", total_rounds=1):
        await super().start_game(mode, self.target_score)
        self.total_score = 0
        self.scores = {pid: 0 for pid in self.player_order}
        self.locked = False
        

    async def process_action(self, player_id, action):
        if action is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "动作信息缺失"})
            return

        if action == "increment":
            self.total_score += 1
            self.scores[player_id] += 1

    async def check_end_condition(self):
        if self.is_game_finished():
            self.state = "finished"
            await self.broadcast_game_state()
        else:
            self.round += 1
            self.state = "player_turn"
            self.current_player = self.next_player()
            await self.broadcast_game_state()

    def is_game_finished(self) -> bool:
        return self.total_score >= self.target_score

    async def broadcast_game_state(self):
        await self.broadcast({
            "type": "game_state",
            "state": self.state,
            "current_player": self.current_player,
            "round": self.round,
            "total_rounds": self.total_rounds,
            "total_score": self.total_score,
            "target_score": self.target_score,
            "player_scores": self.scores
        })
