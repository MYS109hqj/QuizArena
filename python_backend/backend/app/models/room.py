from typing import Dict
from fastapi import WebSocket
from games.base import BaseGame

class Room:
    """房间模型，管理游戏实例和连接"""
    def __init__(self, room_id: str, game: BaseGame):
        self.room_id = room_id
        self.game = game  # 关联游戏实例

    async def connect(self, websocket: WebSocket, player) -> None:
        """玩家连接房间"""
        await self.game.connect(websocket, player)

    async def handle_event(self, websocket: WebSocket, event: Dict) -> None:
        """处理事件，转发给游戏实例"""
        await self.game.handle_event(websocket, event)

    async def disconnect(self, websocket: WebSocket) -> None:
        """玩家断开连接"""
        await self.game.disconnect(websocket)