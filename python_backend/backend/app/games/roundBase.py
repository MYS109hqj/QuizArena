import json
import time
from typing import Dict, Any, List, override
from fastapi import WebSocket
from .base import BaseGame
from app.models.player import Player

class RoundBaseGame(BaseGame):
    """通用回合制游戏基类，包含回合状态机和轮次管理"""
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.state = "init"  # 游戏状态: init/player_turn/checking_end/finished
        self.current_player = None
        self.round = 1
        self.total_rounds = 1
        self.mode = "single"  # 或 "double"
        self.player_order: List[str] = []

    async def start_game(self, mode="single", total_rounds=1):
        self.state = "player_turn"
        self.mode = mode
        self.total_rounds = total_rounds
        self.round = 1
        self.player_order = self._init_player_order()
        self.current_player = self.player_order[0]
        # 广播游戏状态
        await self.broadcast_game_state()

    def _init_player_order(self) -> List[str]:
        # 单人模式：只有一个玩家；双人模式：随机排序
        ids = [pid for pid in self.players]
        if self.mode == "double" and len(ids) >= 2:
            import random
            random.shuffle(ids)
        return ids

    async def handle_event(self, websocket: WebSocket,event: Dict[str, Any], player_id: str) -> None:
        """处理游戏事件"""
        if event.get('type') == "action":
            action = event.get("action")
            await self.handle_player_action(player_id, action)

    async def handle_player_action(self, player_id, action):
        if self.state != "player_turn" or player_id != self.current_player:
            await self.broadcast_to_player(player_id, {"type": "error", "message": "未轮到你操作"})
            return
        # 处理玩家操作（具体游戏实现可重写此方法）
        await self.process_action(player_id, action)
        self.state = "checking_end"
        await self.check_end_condition()

    async def process_action(self, player_id, action):
        """处理玩家操作，子类可重写"""
        pass

    async def check_end_condition(self):
        """判断游戏是否结束，子类可重写"""
        if self.round >= self.total_rounds or self.is_game_finished():
            self.state = "finished"
            await self.broadcast_game_state()
        else:
            self.round += 1
            self.state = "player_turn"
            self.current_player = self.next_player()
            await self.broadcast_game_state()

    def next_player(self) -> str:
        idx = self.player_order.index(self.current_player)
        return self.player_order[(idx + 1) % len(self.player_order)]

    def is_game_finished(self) -> bool:
        """判断游戏是否结束，子类可重写"""
        return False

    async def broadcast_game_state(self):
        await self.broadcast({
            "type": "game_state",
            "state": self.state,
            "current_player": self.current_player,
            "round": self.round,
            "total_rounds": self.total_rounds
        })

    @override
    async def update_rules(self, rules: Dict[str, Any]) -> None:
        """更新游戏规则"""
        return None