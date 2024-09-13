from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json

# 创建路由器
router = APIRouter()

# 管理每个房间的连接
class ConnectionManager:
    def __init__(self):
        # 每个房间的连接列表
        self.rooms: Dict[str, List[WebSocket]] = {}  

    async def connect(self, room_id: str, websocket: WebSocket):
        # 如果房间不存在，则创建一个新的房间
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        await websocket.accept()
        # 将 WebSocket 连接添加到指定房间
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        # 从房间中移除 WebSocket 连接
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            # 如果房间中的连接为空，则删除房间
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict):
        # 将消息转换为 JSON 格式
        message_json = json.dumps(message)
        if room_id in self.rooms:
            # 向房间中的所有连接广播消息
            for connection in self.rooms[room_id]:
                await connection.send_text(message_json)

manager = ConnectionManager()

# WebSocket 路由装饰器
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # 将 WebSocket 连接添加到指定房间
    await manager.connect(room_id, websocket)
    try:
        while True:
            # 接收客户端发送的消息
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get('type') == 'question':
                # 处理问题消息
                print(f"Question received for room {room_id}: {message['content']}")
                await manager.broadcast(room_id, {
                    'type': 'question',
                    'content': message['content'],
                })
            elif message.get('type') == 'answer':
                # 广播答案到所有连接的客户端
                await manager.broadcast(room_id, {
                    'type': 'answer',
                    'name': message.get('name', '').strip(),
                    'avatar': message.get('avatar', '').strip(),
                    'text': message.get('text', '').strip()
                })
    except WebSocketDisconnect:
        # 处理 WebSocket 断开连接
        manager.disconnect(room_id, websocket)
        # 通知所有客户端用户已经离开房间
        await manager.broadcast(room_id, {
            'type': 'notification',
            'message': f"A user has left the room {room_id}."
        })
