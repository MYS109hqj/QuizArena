import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from jose import JWTError, jwt
import time
from .games.factory import GameFactory
from .rooms import Room
from .models.player import Player
from .models.user import User
from .auth import get_current_user, SECRET_KEY, ALGORITHM
from .database import SessionLocal
import secrets
import string

router = APIRouter()
rooms: dict[str, dict[str, Room]] = {}  # {game_type: {room_id: Room}}

def player_from_user(user: User) -> Player:
    return Player(str(user.id), user.username, user.avatar or "")

def find_room(game_type: str, room_id: str) -> Room:
    room = rooms.get(game_type, {}).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room

def websocket_user(websocket: WebSocket) -> User | None:
    token = websocket.cookies.get("access_token")
    if not token:
        return None
    db = SessionLocal()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        return db.query(User).filter(User.username == username).first() if username else None
    except JWTError:
        return None
    finally:
        db.close()

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

@router.post("/api/rooms/{game_type}")
async def create_authenticated_room(game_type: str, user: User = Depends(get_current_user)):
    room_id = generate_short_id()
    while room_id in rooms.get(game_type, {}):
        room_id = generate_short_id()
    game = GameFactory.create_game(game_type, room_id)
    player = player_from_user(user)
    room = Room(room_id, game,
                owner_info={"id": player.id, "name": player.name, "avatar": player.avatar},
                gameType=game_type)
    room.players[player.id] = player
    room.ready_players.add(player.id)
    if hasattr(game, "persistent_players"):
        game.persistent_players[player.id] = player
    rooms.setdefault(game_type, {})[room_id] = room
    room.on_empty(await create_room_destroy_callback(game_type))
    return {"room_id": room_id, "membership": True}

@router.post("/api/rooms/{game_type}/{room_id}/join")
async def join_authenticated_room(game_type: str, room_id: str,
                                  user: User = Depends(get_current_user)):
    room = find_room(game_type, room_id)
    player = player_from_user(user)
    if player.id not in room.players:
        if room.status != "waiting":
            raise HTTPException(status_code=409, detail="游戏已经开始")
        if len(room.players) >= room.game.config.get("max_players", 2):
            raise HTTPException(status_code=409, detail="房间人数已满")
        room.players[player.id] = player
        if hasattr(room.game, "persistent_players"):
            room.game.persistent_players[player.id] = player
    else:
        room.players[player.id].name = player.name
        room.players[player.id].avatar = player.avatar
    await room.broadcast_state()
    return {"room_id": room_id, "membership": True}

@router.get("/api/rooms/{game_type}/{room_id}/membership")
async def get_membership(game_type: str, room_id: str,
                         user: User = Depends(get_current_user)):
    room = find_room(game_type, room_id)
    player_id = str(user.id)
    return {"membership": player_id in room.players, "player_id": player_id,
            "status": room.status}

@router.delete("/api/rooms/{game_type}/{room_id}/membership")
async def leave_authenticated_room(game_type: str, room_id: str,
                                   user: User = Depends(get_current_user)):
    room = find_room(game_type, room_id)
    await room.remove_member(str(user.id), "left")
    return {"success": True}

@router.delete("/api/rooms/{game_type}/{room_id}/members/{player_id}")
async def kick_room_member(game_type: str, room_id: str, player_id: str,
                           user: User = Depends(get_current_user)):
    room = find_room(game_type, room_id)
    actor_id = str(user.id)
    if not room.owner or room.owner["id"] != actor_id:
        raise HTTPException(status_code=403, detail="只有房主可以移除成员")
    if player_id == actor_id:
        raise HTTPException(status_code=400, detail="房主不能踢出自己")
    if room.status != "waiting":
        raise HTTPException(status_code=409, detail="游戏进行中不能移除成员")
    await room.remove_member(player_id, "kicked")
    return {"success": True}

@router.websocket("/ws/{room_id}/{game_type}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, game_type: str):
    user = websocket_user(websocket)
    room = rooms.get(game_type, {}).get(room_id)
    player_id = str(user.id) if user else ""
    if not user:
        return await websocket.close(code=4401, reason="login required")
    if not room or player_id not in room.players:
        return await websocket.close(code=4403, reason="join room first")
    await websocket.accept()
    player = room.players[player_id]
    try:
        print(f"玩家 {player.name} 连接到房间 {room_id}，游戏类型 {game_type}")
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
        import traceback
        print(f"WebSocket错误: {e}")
        print("完整堆栈:")
        traceback.print_exc() 
        if room and player:
            try:
                await room.disconnect(websocket)
            except Exception as disconnect_error:
                print(f"断开连接时出错: {disconnect_error}")

@router.get("/api/room-list/{game_type}")
async def get_rooms(game_type: str, user: User = Depends(get_current_user)):
    print(f"获取房间列表: {game_type}")
    print(rooms)
    game_rooms = rooms.get(game_type, {})
    result = []
    for room_id, room in game_rooms.items():
        result.append({
            "id": room_id,
            "owner": room.owner["name"] if room.owner else "",
            "players": [{"id": p.id, "name": p.name, "avatar": p.avatar,
                         "online": pid in room.online_players or pid.startswith("bot-")}
                        for pid, p in room.players.items()],
            "maxPlayers": room.game.config["max_players"],
            "status": room.status,
            "name": room.name,
            "deckPreset": getattr(room.game, "game_rules", {}).get("deck_preset", "base"),
            "deckSpec": getattr(room.game, "game_rules", {}).get("deck_spec", {}),
            "deckSummary": (room.game.deck_spec.summary()
                            if hasattr(room.game, "deck_spec") else "")
        })
    return {"rooms": result}

def generate_short_id(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

@router.get("/api/new-room-id-short/{game_type}")
async def get_new_room_id_short(game_type: str, user: User = Depends(get_current_user)):
    while True:
        room_id = generate_short_id()
        if room_id not in rooms.get(game_type, {}):
            game = GameFactory.create_game(game_type, room_id)
            player = player_from_user(user)
            room = Room(room_id, game,
                        owner_info={"id": player.id, "name": player.name,
                                    "avatar": player.avatar}, gameType=game_type)
            room.players[player.id] = player
            room.ready_players.add(player.id)
            if hasattr(game, "persistent_players"):
                game.persistent_players[player.id] = player
            rooms.setdefault(game_type, {})[room_id] = room
            room.on_empty(await create_room_destroy_callback(game_type))
            return {"room_id": room_id, "membership": True}

@router.get("/api/room-exists/{game_type}/{room_id}")
async def check_room_exists(game_type: str, room_id: str,
                            user: User = Depends(get_current_user)):
    """检查房间是否存在"""
    game_rooms = rooms.get(game_type, {})
    exists = room_id in game_rooms
    return {"exists": exists}

@router.get("/api/room-info/{room_id}")
async def get_room_info(room_id: str, user: User = Depends(get_current_user)):
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
