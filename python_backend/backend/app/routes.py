import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
import time
from games.factory import GameFactory
from models.room import Room
from models.player import Player

router = APIRouter()
rooms: dict[str, Room] = {}  # 房间ID -> 房间实例

# 时间同步
@router.get("/api/server-time")
async def get_server_time():
    return {"server_time": time.now()}

@router.websocket("/ws/{room_id}/{game_type}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, game_type: str):
    await websocket.accept()

    try:
        # 接收玩家信息
        data = await websocket.receive_text()
        player_info = json.loads(data)
        player = Player(
            id=player_info["id"],
            name=player_info["name"],
            avatar=player_info.get("avatar", "")
        )

        # 初始化房间和游戏
        if room_id not in rooms:
            game = GameFactory.create_game(game_type, room_id)
            rooms[room_id] = Room(room_id, game)
        room = rooms[room_id]
        await room.connect(websocket, player)

        # 事件循环
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            await room.handle_event(websocket, event)

    except WebSocketDisconnect:
        await room.disconnect(websocket)
    except Exception as e:
        print(f"错误: {e}")
        await room.disconnect(websocket)