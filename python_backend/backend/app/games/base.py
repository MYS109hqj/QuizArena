from abc import ABC, abstractmethod
from typing import Dict, List, Any
from fastapi import WebSocket
from models.player import Player

class BaseGame(ABC):
    """游戏基类，定义通用接口"""
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, Player] = {}  # 玩家字典
        self.connections: Dict[WebSocket, str] = {}  # 连接->玩家ID映射
        self.mode: str = "none"  # 游戏模式
        self.config: Dict[str, Any] = {
            "expose_answer": True,
            "reconnect_timeout": 5,
            "total_rounds": 1,
            "current_round": 1
        }

    @abstractmethod
    async def handle_event(self, websocket: WebSocket, event: Dict[str, Any]) -> None:
        """处理游戏事件"""
        pass

    @abstractmethod
    async def broadcast(self, data: Dict[str, Any], exclude: WebSocket = None) -> None:
        """广播消息"""
        pass

    async def connect(self, websocket: WebSocket, player: Player) -> None:
        """玩家连接"""
        self.players[player.id] = player
        self.connections[websocket] = player.id

    async def disconnect(self, websocket: WebSocket) -> None:
        """玩家断开连接"""
        player_id = self.connections.pop(websocket, None)
        if player_id:
            self.players.pop(player_id, None)