from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket
from app.models.player import Player
import json

class BaseGame(ABC):
    """游戏基类，定义通用接口"""
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, Player] = {}  # 玩家字典
        self.connections: Dict[WebSocket, str] = {}  # 连接->玩家ID映射
        self.disconnected_players: Set[str] = set()  # 已断开连接的玩家ID
        self.mode: str = "none"  # 游戏模式
        self.config: Dict[str, Any] = {
            "max_players": 2,
            "min_players": 1  # 新增最小玩家数配置
        }
        self.state: str = "waiting"  # 游戏状态：waiting/playing/finished
        self.room: Optional["Room"] = None  # 关联的房间引用
        
    def set_room_reference(self, room: "Room") -> None:
        """设置房间引用，建立双向关联"""
        self.room = room
        
    @abstractmethod
    async def handle_event(self, websocket: WebSocket, event: Dict[str, Any], player_id: str) -> None:
        """处理游戏事件"""
        pass

    @abstractmethod
    async def update_rules(self, rules: Dict[str, Any]) -> None:
        """更新游戏规则"""
        pass

    async def broadcast(self, data: Dict[str, Any], exclude: WebSocket = None) -> None:
        """广播消息给所有连接"""
        data_str = json.dumps(data)
        # 使用字典键的副本进行遍历，避免并发修改问题
        disconnected_websockets = []
        for websocket in list(self.connections.keys()):
            if websocket != exclude:
                try:
                    await websocket.send_text(data_str)
                except (RuntimeError, Exception) as e:
                    # 记录断开连接的websocket，稍后清理
                    disconnected_websockets.append(websocket)
                    print(f"广播消息失败: {e}")
        
        # 清理断开连接的websocket
        for websocket in disconnected_websockets:
            if websocket in self.connections:
                player_id = self.connections[websocket]
                del self.connections[websocket]
                print(f"清理断开连接的WebSocket: 玩家 {player_id}")

    async def broadcast_state(self, extraMessage: Dict[str, Any] = None) -> None:
        """广播当前游戏状态"""
        state = {
            "type": "game_state",
            "room_id": self.room_id,
            "mode": self.mode,
            "state": self.state,  # 新增游戏状态
            "config": self.config,
            "players": [self.format_player(p) for p in self.players.values()],
        }
        if extraMessage:
            state["extra"] = extraMessage
        await self.broadcast(state)

    async def connect(self, websocket: WebSocket, player: Player) -> None:
        """玩家连接"""
        is_reconnect = player.id in self.disconnected_players
        
        self.players[player.id] = player
        self.connections[websocket] = player.id
        
        # 如果是重连，从断开连接集合中移除
        if is_reconnect:
            self.disconnected_players.remove(player.id)
        
        if is_reconnect:
            # 如果是重连，调用重连同步方法
            if hasattr(self, 'on_player_reconnect'):
                await self.on_player_reconnect(player.id)
            else:
                # 如果没有重连方法，至少发送当前游戏状态
                await self.broadcast_state()
        else:
            # 新玩家加入
            await self.on_player_join(player)

    async def disconnect(self, websocket: WebSocket) -> None:
        """玩家断开连接"""
        player_id = self.connections.pop(websocket, None)
        if player_id and player_id in self.players:
            player = self.players.pop(player_id)
            # 添加到断开连接集合，用于重连检测
            self.disconnected_players.add(player_id)
            # 通知游戏有玩家离开
            await self.on_player_leave(player)

    async def broadcast_playerlist(self) -> None:
        """广播当前玩家列表"""
        await self.broadcast({
            "type": "player_list",
            "players": [self.format_player(p) for p in self.players.values()]
        })

    def format_player(self, player: Player) -> Dict[str, Any]:
        """格式化玩家信息"""
        return {
            "id": player.id,
            "name": player.name,
            "avatar": player.avatar,
        }

    async def broadcast_to_player(self, player_id: str, data: Dict[str, Any]) -> None:
        """只向指定玩家广播消息"""
        for websocket, pid in self.connections.items():
            if pid == player_id:
                await websocket.send_text(json.dumps(data))
                break
                
    async def start_game(self) -> None:
        """开始游戏（默认实现，可在子类中重写）"""
        self.state = "playing"
        await self.broadcast_state({"message": "游戏开始！"})
        
    async def end_game(self) -> None:
        """结束游戏（默认实现，可在子类中重写）"""
        self.state = "finished"
        await self.broadcast_state({"message": "游戏结束！"})
        
    async def on_player_join(self, player: Player) -> None:
        """玩家加入时的回调（可在子类中重写）"""
        pass
        
    async def on_player_leave(self, player: Player) -> None:
        """玩家离开时的回调（可在子类中重写）"""
        pass
