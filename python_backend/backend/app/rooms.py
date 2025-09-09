from __future__ import annotations
from typing import Dict, List, Optional, Callable
from fastapi import WebSocket
from app.games.base import BaseGame
from app.models.player import Player

class Room:
    def __init__(self, room_id: str, game: BaseGame, owner_info: Dict = None, name: str = ""):
        self.room_id = room_id
        self.game = game
        self.reconnect_timeout = 5
        self.owner = owner_info if owner_info and "id" in owner_info and "name" in owner_info else None
        self.name = name or room_id
        self.status = "waiting"  # waiting, playing, ended
        
        # 准备状态管理，房主默认准备
        self.ready_players: set[str] = set()
        
        # 玩家和连接管理
        self.players: Dict[str, Player] = {}  # 玩家ID -> Player对象
        self.connections: Dict[WebSocket, str] = {}  # 连接 -> 玩家ID
        
        self._on_empty_callback: Optional[Callable] = None
        
        # 设置游戏对房间的引用
        self.game.set_room_reference(self)

    async def connect(self, websocket: WebSocket, player: Player):
        # 存储连接和玩家信息
        self.connections[websocket] = player.id
        self.players[player.id] = player
        
        # 如果没有房主，则第一个连接的玩家为房主，并默认准备
        if not self.owner:
            self.owner = {
                "id": player.id,
                "name": player.name,
                "avatar": player.avatar
            }
            self.ready_players.add(player.id)  # 房主默认准备
        
        # 同时在游戏中注册连接
        await self.game.connect(websocket, player)
        
        # 广播房间状态更新
        await self.broadcast_state()

    async def handle_event(self, websocket: WebSocket, message: Dict, ):
        """处理来自客户端的消息"""
        message_type = message.get("type")
        player_id = self.connections.get(websocket)
        
        if not player_id:
            return
        
        if self.status == "waiting":
            # 处理准备状态切换
            if message_type == "toggle_ready":
                # 房主不能取消准备
                if player_id == self.owner["id"]:
                    return await self.broadcast_state(
                        extra_message={"error": "房主不能取消准备"}
                    )
                
                # 切换普通玩家的准备状态
                if player_id in self.ready_players:
                    self.ready_players.remove(player_id)
                else:
                    self.ready_players.add(player_id)
                
                await self.broadcast_state()
            
            # 处理开始游戏请求（只有房主可以发起）
            elif message_type == "start_game" and player_id == self.owner["id"]:
                if self.can_start_game():

                    await self.start_game()
                else:
                    await self.broadcast_state(
                        extra_message={"error": "无法开始游戏，还有玩家未准备或玩家数量不足"}
                    )
        
        elif self.status == "playing":
            # 转发游戏内消息给游戏实例处理
            await self.game.handle_event(websocket, message, player_id)

    def can_start_game(self) -> bool:
        """检查是否可以开始游戏：所有非房主玩家都已准备且满足最小玩家数"""
        if not self.owner:
            return False
            
        # 获取所有非房主玩家
        non_owner_players = [p_id for p_id in self.players.keys() if p_id != self.owner["id"]]
        
        # 检查是否有足够的玩家
        if len(self.players) < self.game.config.get("min_players", 2):
            return False
            
        # 检查所有非房主玩家是否都已准备
        return all(p_id in self.ready_players for p_id in non_owner_players)

    async def start_game(self):
        """开始游戏"""
        self.status = "playing"
        await self.broadcast_state()
        await self.game.start_game()  # 通知游戏开始
        

    async def disconnect(self, websocket: WebSocket):
        player_id = self.connections.get(websocket)
        if not player_id:
            return
            
        # 移除连接和玩家
        if websocket in self.connections:
            del self.connections[websocket]
        if player_id in self.players:
            del self.players[player_id]
        if player_id in self.ready_players:
            self.ready_players.remove(player_id)
        
        # 通知游戏玩家已断开连接
        await self.game.disconnect(websocket)
        
        # 处理房主离开的情况
        if self.owner and self.owner["id"] == player_id:
            # 转移房主权限
            if self.players:
                new_owner = next(iter(self.players.values()))
                self.owner = {
                    "id": new_owner.id,
                    "name": new_owner.name,
                    "avatar": new_owner.avatar or ""
                }
                # 新房主默认准备
                self.ready_players.add(new_owner.id)
            else:
                self.owner = None
        
        # 处理房间为空的情况
        if len(self.players) == 0 and self._on_empty_callback:
            await self._on_empty_callback(self)
        else:
            await self.broadcast_state()

    async def broadcast_state(self, extra_message: Dict = None):
        """广播当前房间和游戏状态给所有连接的玩家"""
        # 构建房间状态信息
        room_state = {
            "type": "room_state",
            "room_id": self.room_id,
            "name": self.name,
            "status": self.status,
            "owner": self.owner,
            "players": {
                p_id: {
                    "id": p.id,
                    "name": p.name,
                    "avatar": p.avatar,
                    "ready": p_id in self.ready_players
                } for p_id, p in self.players.items()
            },
            "player_count": len(self.players),
            "max_players": self.game.config.get("max_players", 2),
            "min_players": self.game.config.get("min_players", 2)
        }
        
        
        # 发送给所有连接
        for websocket in self.connections:
            await websocket.send_json(room_state)

    def on_empty(self, callback):
        """注册房间为空时的回调（用于销毁）"""
        self._on_empty_callback = callback
        return self

    def can_modify_settings(self, player_id: str) -> bool:
        """检查玩家是否有权限修改设置（仅限房主）"""
        return self.owner and self.owner["id"] == player_id

    async def update_settings(self, player_id: str, settings: Dict):
        """更新游戏设置"""
        if not self.can_modify_settings(player_id):
            return {"error": "无权限，只有房主可以修改设置"}

        if "rules" in settings:
            await self.game.update_rules(settings["rules"])
        if "max_players" in settings:
            self.game.config["max_players"] = settings["max_players"]
        if "min_players" in settings:
            self.game.config["min_players"] = settings["min_players"]
            
        await self.broadcast_state({"message": "游戏设置已更新"})
        return {"success": True}

    async def end_game(self):
        """结束当前游戏"""
        if self.status == "playing":
            await self.game.end_game()
            self.status = "ended"
            await self.broadcast_state()

    async def reset_game(self):
        """重置游戏，回到等待状态"""
        if self.status == "ended":
            # 调用游戏的重置方法（如果有）
            if hasattr(self.game, 'reset_game'):
                await self.game.reset_game()
            
            self.status = "waiting"
            # 重置准备状态，房主仍然保持准备
            self.ready_players = {self.owner["id"]} if self.owner else set()
            await self.broadcast_state()
