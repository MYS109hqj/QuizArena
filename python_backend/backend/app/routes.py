import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
import time
from app.games.factory import GameFactory
from .rooms import Room
from app.models.player import Player
import secrets
import string

router = APIRouter()
rooms: dict[str, dict[str, Room]] = {}  # {game_type: {room_id: Room}}

# 房间销毁回调
async def create_room_destroy_callback(game_type: str):
    async def destroy(room: Room):
        if game_type in rooms and room.room_id in rooms[game_type]:
            del rooms[game_type][room.room_id]
            print(f"房间 {room.room_id} 已被自动销毁（无人）")
    return destroy

# 时间同步
@router.get("/api/server-time")
async def get_server_time():
    return {"server_time": time.now()}

@router.websocket("/ws/{room_id}/{game_type}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, game_type: str):
    await websocket.accept()
    # 理论上后端得给前端开一个独特的roonId
    try:
        # 接收玩家信息
        data = await websocket.receive_text()
        player_info = json.loads(data)
        player = Player(
            id=player_info["id"],
            name=player_info["name"],
            avatar=player_info.get("avatar", "")
        )
        print(f"玩家 {player.name} 连接到房间 {room_id}，游戏类型 {game_type}")
        # 初始化房间和游戏
        if game_type not in rooms:
            rooms[game_type] = {}
        if room_id not in rooms[game_type]:
            game = GameFactory.create_game(game_type, room_id)
            room = Room(room_id, game)
            # 注册销毁房间的回调函数
            destroy_cb = await create_room_destroy_callback(game_type)
            room.on_empty(destroy_cb)
            rooms[game_type][room_id] = room
        else:
            room = rooms[game_type][room_id]
        await room.connect(websocket, player)
        print(rooms)
        print(f"当前房间状态: {room.status}, 玩家数: {len(room.game.players)}")
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

@router.get("/api/room-list/{game_type}")
async def get_rooms(game_type: str):
    print(f"获取房间列表: {game_type}")
    print(rooms)
    game_rooms = rooms.get(game_type, {})
    result = []
    for room_id, room in game_rooms.items():
        result.append({
            "id": room_id,
            "owner": room.owner["name"] if room.owner else "",
            "players": list(room.game.players.values()),
            "maxPlayers": room.game.config["max_players"],
            "status": room.status,
            "name": room.name
        })
    return {"rooms": result}

def generate_short_id(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

@router.get("/api/new-room-id-short/{game_type}")
async def get_new_room_id_short(game_type: str):
    while True:
        room_id = generate_short_id()
        if room_id not in rooms.get(game_type, {}):
            return {"room_id": room_id}