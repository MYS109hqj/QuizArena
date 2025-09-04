# backend/app/rooms.py
from typing import Dict, List, Optional
from fastapi import WebSocket
from .games.factory import GameFactory
from .games.base import BaseGame

class Room:
    def __init__(self, room_id: str, game_type: str):
        self.room_id = room_id
        self.game: BaseGame = GameFactory.create_game(game_type, room_id)  # 关联具体游戏
        self.reconnect_timeout = 5  # 通用重连超时配置

    async def connect(self, websocket: WebSocket, player_info: Dict):
        """玩家连接房间，交给游戏实例处理"""
        await websocket.accept()
        self.game.connections.append(websocket)
        self.game.players[player_info["id"]] = player_info

    async def handle_message(self, message: Dict):
        """将消息转发给游戏实例处理"""
        result = self.game.handle_event(message)
        await self.game.broadcast_state()  # 广播更新后的状态

    async def disconnect(self, websocket: WebSocket, player_id: str):
        """玩家断开连接"""
        self.game.connections.remove(websocket)
        if player_id in self.game.players:
            del self.game.players[player_id]