import json
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class Player:
    def __init__(self, player_id: str, name: str, avatar: str):
        self.id = player_id
        self.name = name
        self.avatar = avatar

class Room:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.players: Dict[str, Player] = {}
        self.current_question: Optional[Dict] = None  # 当前问题
        self.current_question_id: Optional[str] = None  # 当前问题的 ID

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    async def connect(self, room_id: str, websocket: WebSocket, player_info: dict):
        if room_id not in self.rooms:
            self.rooms[room_id] = Room()

        room = self.rooms[room_id]
        
        # 检查玩家是否已在房间中
        if player_info['id'] in room.players:
            print(f"玩家 {player_info['name']} 已在房间中，更新连接")
            room.connections.append(websocket)  # 直接添加 websocket
            return  # 结束连接处理

        # 新玩家加入
        room.connections.append(websocket)

        # 添加玩家信息
        player = Player(player_info['id'], player_info['name'], player_info['avatar'])
        room.players[player_info['id']] = player  
        print(f"用户加入: {player_info}")

        # 广播提问者上线
        await self.broadcast(room_id, {
            'type': 'notification',
            'message': f"{player_info['name']} has joined the room."
        })

        # 广播当前问题（如果存在）
        if room.current_question:
            await self.broadcast(room_id, {
                'type': 'current_question',
                'content': room.current_question,
                'question_id': room.current_question_id
            })

        # 广播更新后的玩家列表
        await self.broadcast(room_id, {
            'type': 'player_list',
            'players': [{'id': p.id, 'name': p.name, 'avatar': p.avatar} for p in room.players.values()]
        })

    def disconnect(self, room_id: str, websocket: WebSocket, user_id: str):
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if websocket in room.connections:
                room.connections.remove(websocket)
            # 删除玩家信息
            if user_id in room.players:
                del room.players[user_id]
                print(f"玩家 {user_id} 已离开，删除其信息")
            # 如果房间没有任何连接，删除房间
            if not room.connections:
                del self.rooms[room_id]
                print(f"房间 {room_id} 已空，删除房间")

    async def broadcast(self, room_id: str, message: dict):
        message_json = json.dumps(message)
        if room_id in self.rooms:
            room = self.rooms[room_id]
            for connection in room.connections:
                await connection.send_text(message_json)
            print("广播发送了信息：", message_json)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    try:
        # 这里接收玩家信息
        data = await websocket.receive_text()
        player_info = json.loads(data)

        # 使用接收到的玩家信息连接
        await manager.connect(room_id, websocket, player_info)

        while True:
            # 接收其他消息
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get('type') == 'question':
                # 更新房间当前问题
                room = manager.rooms[room_id]
                room.current_question = message['content']  # 直接保存整个内容
                room.current_question_id = message['questionId']  # 更新问题 ID
                await manager.broadcast(room_id, {
                    'type': 'question',
                    'content': message['content'],
                })
            elif message.get('type') == 'answer':
                await manager.broadcast(room_id, {
                    'type': 'answer',
                    'name': message.get('name', '').strip(),
                    'avatar': message.get('avatar', '').strip(),
                    'text': message.get('text', '').strip()
                })

    except WebSocketDisconnect:
        user_id = player_info['id']  # 根据客户端发送的用户信息获取用户ID
        manager.disconnect(room_id, websocket, user_id)  # 在断开连接时删除用户信息

        # 广播用户离开消息
        await manager.broadcast(room_id, {
            'type': 'notification',
            'message': f"{player_info['name']} has left the room."
        })

        # 广播更新后的玩家列表
        if room_id in manager.rooms:
            room = manager.rooms[room_id]
            await manager.broadcast(room_id, {
                'type': 'player_list',
                'players': [{'id': p.id, 'name': p.name, 'avatar': p.avatar} for p in room.players.values()]
            })
