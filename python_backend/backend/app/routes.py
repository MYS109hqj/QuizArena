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

# 房间销毁回调（带延迟重连支持）
async def create_room_destroy_callback(game_type: str):
    async def destroy(room: Room):
        # 等待重连超时时间（默认30秒）
        import asyncio
        reconnect_timeout = getattr(room, 'reconnect_timeout', 30)
        await asyncio.sleep(reconnect_timeout)
        
        # 再次检查房间是否仍然为空
        if len(room.players) == 0:
            if game_type in rooms and room.room_id in rooms[game_type]:
                del rooms[game_type][room.room_id]
                print(f"房间 {room.room_id} 已被自动销毁（无人，等待重连超时）")
    return destroy

# 时间同步
@router.get("/api/server-time")
async def get_server_time():
    return {"server_time": time.time()}

@router.websocket("/ws/{room_id}/{game_type}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, game_type: str):
    await websocket.accept()
    room = None
    player = None
    
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
        print(f"当前房间状态: {room.status}, 玩家数: {len(room.players)}")
        
        # 事件循环
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            await room.handle_event(websocket, event)

    except WebSocketDisconnect:
        print(f"WebSocket连接断开: {player.name if player else '未知玩家'}")
        if room and player:
            try:
                await room.disconnect(websocket)
            except Exception as disconnect_error:
                print(f"断开连接时出错: {disconnect_error}")
    except RuntimeError as e:
        # 处理"send"调用在连接关闭后的错误
        if "Cannot call \"send\" once a close message has been sent" in str(e):
            print(f"连接已关闭，忽略发送操作: {player.name if player else '未知玩家'}")
        else:
            print(f"运行时错误: {e}")
            if room and player:
                try:
                    await room.disconnect(websocket)
                except Exception as disconnect_error:
                    print(f"断开连接时出错: {disconnect_error}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        if room and player:
            try:
                await room.disconnect(websocket)
            except Exception as disconnect_error:
                print(f"断开连接时出错: {disconnect_error}")

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

@router.get("/api/room-exists/{game_type}/{room_id}")
async def check_room_exists(game_type: str, room_id: str):
    """检查房间是否存在"""
    game_rooms = rooms.get(game_type, {})
    exists = room_id in game_rooms
    return {"exists": exists}

@router.get("/api/room-info/{room_id}")
async def get_room_info(room_id: str):
    """获取房间基本信息（用于预加载）"""
    print(f"🔍 请求房间信息: {room_id}")
    
    # 在所有游戏类型中查找房间
    for game_type, game_rooms in rooms.items():
        if room_id in game_rooms:
            room = game_rooms[room_id]
            print(f"✅ 找到房间: {room_id}，游戏类型: {game_type}")
            
            # 返回房间基本信息（不包含敏感信息）
            return {
                "room_id": room_id,
                "game_type": game_type,
                "owner": room.owner["name"] if room.owner else "未知",
                "player_count": len(room.players),
                "max_players": room.game.config["max_players"],
                "status": room.status,
                "name": room.name,
                "exists": True
            }
    
    print(f"❌ 房间不存在: {room_id}")
    return {
        "room_id": room_id,
        "exists": False,
        "error": "房间不存在"
    }