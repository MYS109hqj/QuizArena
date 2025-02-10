import asyncio
import json
import time
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

router = APIRouter()

# 玩家类定义
class Player:
    def __init__(self, player_id: str, name: str, avatar: str):
        self.id = player_id
        self.name = name
        self.avatar = avatar
        # 初始化不同模式的数据
        self.content: Dict[str, Dict] = {
            'scoring': {
                'score': 0,  # 总得分
                'round_score': 0  # 当前轮次得分
            },
            'survival': {
                'lives': 3,  # 剩余生命
                'lost_lives_this_round': 0  # 本轮失去的生命数
            }
        }
        self.submitted_answer: Optional[str] = None  # 玩家提交的答案
        self.timestamp: Optional[float] = None  # 提交时间戳
        self.last_active_timestamp: float = time.time()

# 房间类定义
class Room:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.players: Dict[str, Player] = {}
        self.connection_to_player: Dict[WebSocket, str] = {}  # 新增：连接到玩家ID的映射
        self.current_question: Optional[Dict] = None  # 当前问题
        self.current_question_id: Optional[str] = None  # 当前问题 ID
        self.total_rounds: Optional[int] = 0  # 总轮次（计分模式特有字段）
        self.current_round: Optional[int] = 0  # 当前轮次
        self.current_answers: Dict[str, str] = {}  # 收集的答案，以玩家 ID 为键
        self.judgement_pending: bool = False  # 判题标志
        self.mode: str = 'none'  # 添加当前模式属性，默认无模式
        self.reconnect_timeout = 5  # 设置重连时间为 1 分钟
        self.expose_answer_to_player = False

    # 删除超时未重连的玩家
    async def remove_player_if_expired(self, player_id: str):
        player = self.players.get(player_id)
        if player:
            # print("功能：删除超时未重连的玩家")
            await asyncio.sleep(self.reconnect_timeout)  # 非阻塞的延迟
            current_time = time.time()
            # print(f"功能：删除超时未重连的玩家。目前reconnect_timeout为{self.reconnect_timeout}")
            # 判断是否超过重连时间
            # print(f"current_time:{current_time}; player.last_active_timestamp:{player.last_active_timestamp}")
            if current_time - player.last_active_timestamp >= self.reconnect_timeout - 0.1: # 由于调用time方法会有时间误差，因此
                print("Into delete information part")
                del self.players[player_id]  # 超时，移除玩家数据
                for websocket, pid in list(self.connection_to_player.items()):
                    if pid == player_id:
                        del self.connection_to_player[websocket]
                        print(f"玩家 {player_id} 的 WebSocket 连接已从 connection_to_player 中移除")
                        break
                print(f"玩家 {player_id} 超时未重连，已删除该玩家数据")

# 管理所有房间的连接
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    async def connect(self, room_id: str, websocket: WebSocket, player_info: dict):
        """玩家连接房间"""
        if room_id not in self.rooms:
            self.rooms[room_id] = Room()
        room = self.rooms[room_id]
        player_id = player_info['id']
        # 判断玩家角色，区分提问者和答题者
        is_questioner = player_id.startswith("questioner-")

        if player_id in room.players:
            room.players[player_id].last_active_timestamp = time.time()
            print(f"玩家 {player_info['name']} 在{room.reconnect_timeout}秒内重连")
        else:
            room.players[player_id] = Player(player_id, player_info['name'], player_info['avatar'])
            print(f"新玩家加入: {player_info}")

        room.connections.append(websocket)
        room.connection_to_player[websocket] = player_id

        await self.broadcast_player_list(room_id)  # 广播玩家列表
        await self.broadcast_expose_answer(room_id, room.expose_answer_to_player)  # 广播是否曝光答案，放在这的原因是答题端的expose_answer只要改选项就自动广播修改
        # 如果是提问者，广播所有人；如果是答题者，为了防止覆盖掉提问端最新改动，下面信息只广播给所有答题者
        if is_questioner:
            # 提问者连接时，广播给所有玩家
            await self.broadcast_mode_change(room_id, room.mode)  # 广播模式
            await self.broadcast_round_info(room_id, room.total_rounds, room.current_round)  # 广播轮次   
            if room.current_question:
                await self.broadcast_question(room_id, room.current_question, room.current_question_id)
            # 另外广播给答题者超时时长
            await self.broadcast_timeout_change(room_id, room.reconnect_timeout)
        else:
            # 答题者连接时，仅广播给答题者
            await self.broadcast_mode_change(room_id, room.mode, roles=["player"])  # 只广播给答题者
            await self.broadcast_round_info(room_id, room.total_rounds, room.current_round, roles=["player"])  # 只广播给答题者
            if room.current_question:
                await self.broadcast_question(room_id, room.current_question, room.current_question_id, roles=["player"])  # 只广播给答题者

    async def disconnect(self, room_id: str, websocket: WebSocket, user_id: str):
        """玩家断开连接"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if websocket in room.connections:
                room.connections.remove(websocket)
                del room.connection_to_player[websocket]

            if user_id in room.players:
                room.players[user_id].last_active_timestamp = time.time()
                print(f"玩家 {user_id} 断开连接，等待重连")
                await room.remove_player_if_expired(user_id)

            if not room.connections:
                del self.rooms[room_id]
                print(f"房间 {room_id} 已空，删除房间")

    async def broadcast(self, room_id: str, message: dict):
        """通用的广播函数"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            message_json = json.dumps(message)
            for connection in room.connections:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_text(message_json)
                except Exception as e:
                    print(f"发送消息失败: {e}")
            print(f"广播发送：{message_json}")

    async def broadcast_to_roles(self, room_id: str, message: dict, roles: List[str] = ["questioner", "player"]):
        """
        仅广播给指定角色的玩家：
        - `roles` 可以包含 "questioner" (提问者) 和/或 "player" (答题者)。
        """
        message_json = json.dumps(message)
        if room_id in self.rooms:
            room = self.rooms[room_id]
            for connection in room.connections:
                player_id = room.connection_to_player.get(connection)
                if player_id:
                    if "questioner" in roles and player_id.startswith("questioner-"):
                        await connection.send_text(message_json)
                    elif "player" in roles and player_id.startswith("user-"):  # 修正对答题者的判断
                        await connection.send_text(message_json)

    # ✅ **封装不同类型的广播**

    async def broadcast_question(self, room_id: str, content: dict, question_id: str, roles: List[str] = ["questioner", "player"]):
        await self.broadcast_to_roles(room_id, {
            'type': 'question',
            'content': content,
            'questionId': question_id,
        }, roles)

    async def broadcast_mode_change(self, room_id: str, mode: str, roles: List[str] = ["questioner", "player"]):
        await self.broadcast_to_roles(room_id, {
            'type': 'mode_change',
            'currentMode': mode
        }, roles)

    async def broadcast_round_info(self, room_id: str, total_rounds: int, current_round: int, roles: List[str] = ["questioner", "player"]):
        await self.broadcast_to_roles(room_id, {
            'type': 'round',
            'totalRounds': total_rounds,
            'currentRound': current_round
        }, roles)

    async def broadcast_player_list(self, room_id: str):
        room = self.rooms[room_id]
        await self.broadcast(room_id, {
            'type': 'player_list',
            'players': [
                {'id': p.id, 'name': p.name, 'avatar': p.avatar, 
                 'score': p.content['scoring']['score'], 'lives': p.content['survival']['lives']}
                for p in room.players.values()
            ]
        })

    async def broadcast_expose_answer(self, room_id: str, expose_answer: bool):
        await self.broadcast(room_id, {
            'type': 'expose_answer_update',
            'value': expose_answer
        })

    async def broadcast_notification(self, room_id: str, message: str):
        await self.broadcast(room_id, {
            'type': 'notification',
            'message': message
        })

    async def broadcast_timeout_change(self, room_id: str, reconnect_timeout):
        await self.broadcast_to_roles(room_id, {
            'type': 'timeout_change',
            'reconnect_timeout': reconnect_timeout
        },['questioner'])


# WebSocket 连接处理
manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    try:
        # 接收玩家信息并连接房间
        data = await websocket.receive_text()
        player_info = json.loads(data)
        await manager.connect(room_id, websocket, player_info)

        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            room = manager.rooms[room_id]

            # 处理模式变化消息
            if message.get('type') == 'mode_change':
                room.mode = message['mode']
                await manager.broadcast_mode_change(room_id, room.mode)

            elif message.get('type') == 'timeout_change':
                room.reconnect_timeout = int(message['reconnect_timeout'])
                print(f"Now the reconnect_timeout in {room_id} is {room.reconnect_timeout}")

            # 在 websocket_endpoint 中添加以下处理逻辑
            elif message.get('type') == 'initialize_scores':
                score = message['score']
                for player in room.players.values():
                    player.content['scoring']['score'] = score  # 设置所有玩家的分数
                # 广播更新后的玩家列表
                await manager.broadcast(room_id, {
                    'type': 'player_list',
                    'players': [
                        {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'score': p.content['scoring']['score'], 'lives':p.content['survival']['lives']}
                        for p in room.players.values()
                    ]
                })

            elif message.get('type') == 'initialize_lives':
                lives = message['lives']
                for player in room.players.values():
                    player.content['survival']['lives'] = lives  # 设置所有玩家的生命值
                # 广播更新后的玩家列表
                await manager.broadcast(room_id, {
                    'type': 'player_list',
                    'players': [
                        {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'score': p.content['scoring']['score'], 'lives':p.content['survival']['lives']}
                        for p in room.players.values()
                    ]
                })

            elif message.get('type') == 'round_update':
                room.current_round = message['currentRound']
                room.total_rounds = message['totalRounds']
                await manager.broadcast_round_info(room_id, room.total_rounds, room.current_round)


            elif message.get('type') == 'get_latest_answers':
                latest_answers = [
                    {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'submitted_answer': p.submitted_answer, 'timestamp': p.timestamp}
                    for p in room.players.values()
                    if not p.id.startswith("questioner-")  # 排除提问者
                ]
                await manager.broadcast(room_id, {
                    'type': 'latest_answers',
                    'latest_answers': latest_answers
                })

            # 提问逻辑
            elif message.get('type') == 'question':
                room.current_question = message['content']
                room.current_question_id = message['questionId']
                room.judgement_pending = True
                await manager.broadcast_question(room_id, message['content'], message['questionId'])


            # 答案逻辑
            elif message.get('type') == 'answer':
                player_id = player_info['id']
                if room.judgement_pending:
                    player = room.players[player_id]
                    player.submitted_answer = message['text']
                    player.timestamp = message.get('timestamp')
                    room.current_answers[player_id] = player.submitted_answer
                    
                    # 构造发送给提问端的答案信息（完整可见）
                    questioner_message = {
                        'type': 'answer',
                        'playerId': player_id,
                        'name': player.name,
                        'avatar': player.avatar,
                        'timestamp': player.timestamp,
                        'text': player.submitted_answer  # 提问者可以看到完整答案
                    }

                    # 判断expose_answer_to_player的值，构造给其他答题玩家的答案信息
                    if room.expose_answer_to_player:
                        player_message = questioner_message  # 所有人都能看到答案
                    else:
                        # 如果是 False，答题端只看到"[Hidden]"
                        player_message = {
                            'type': 'answer',
                            'playerId': player_id,
                            'name': player.name,
                            'avatar': player.avatar,
                            'timestamp': player.timestamp,
                            'text': "[Hidden]"  # 其它玩家只能看到玩家提交了答案
                        }

                    # 遍历所有连接，发送对应消息
                    for connection in room.connections:
                        player_id_for_connection = room.connection_to_player.get(connection)
                        if player_id_for_connection and (player_id_for_connection.startswith("questioner-") or player_id_for_connection == player_id):
                            await connection.send_text(json.dumps(questioner_message))  # 提问者
                        else:
                            await connection.send_text(json.dumps(player_message))  # 答题者

            # 判题逻辑
            elif message.get('type') == 'judgement':
                # 提问者手动判题，获取结果
                judgement_results = message.get('results', {})

                # 初始化一个新的字典来存储带有名称和头像的结果
                updated_results = {}

                # 遍历每个玩家的判题结果
                for player_id, result in judgement_results.items():
                    player = room.players.get(player_id)  # 使用 .get() 方法避免 KeyError
                    if player is None:
                        print(f"无法找到玩家 {player_id}，跳过该判题")
                        continue  # 如果玩家不存在，跳过当前判题逻辑

                    # 根据房间模式来处理不同的判题逻辑
                    if room.mode == "scoring":
                        # 计分模式下，更新玩家的得分
                        score = result.get('score', 0)  # 从前端获取得分，默认为0
                        player.content['scoring']['round_score'] = score  # 设置当前轮次得分
                        player.content['scoring']['score'] += score  # 累积总得分

                    elif room.mode == "survival":
                        # 生存模式下，更新玩家的生命状态
                        lost_lives = result.get('lostLives', 0)  # 从前端获取丢失的生命数，默认为0
                        player.content['survival']['lives'] -= lost_lives  # 减去玩家的生命值
                        player.content['survival']['lost_lives_this_round'] = lost_lives  # 记录本轮失去的生命数

                    # 可选的判题正确与否（如果需要跟踪正误）
                    player.content['judgement_correct'] = result.get('correct', False)

                    # 将名称和头像添加到结果中
                    updated_results[player_id] = {
                        'name': player.name,  # 假设名称存储在 player.content 中
                        'avatar': player.avatar,  # 假设头像存储在 player.content 中
                        'correct': result.get('correct', False),
                        'score': result.get('score', 0) if room.mode == 'scoring' else None,
                        'lostLives': result.get('lostLives', 0) if room.mode == 'survival' else None,
                    }

                room.judgement_pending = False  # 判题完成，关闭判题状态
                # 向所有玩家广播判题结果
                await manager.broadcast(room_id, {
                    'type': 'judgement_complete',
                    'results': updated_results,
                    'round': message.get('currentRound', 0),
                    'correct_answer': message.get('correct_answer', ''),
                    'explanation': message.get('explanation', '')
                })

                # 广播更新后的玩家列表
                await manager.broadcast(room_id, {
                    'type': 'player_list',
                    'players': [
                        {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'score': p.content['scoring']['score'], 'lives':p.content['survival']['lives']}
                        for p in room.players.values()
                    ]
                })
                
                # 判题后是否需要执行一些额外的逻辑，例如重置当前轮次得分
                if room.mode == "scoring":
                    for player in room.players.values():
                        player.content['scoring']['round_score'] = 0  # 判题后，重置当前轮次得分
            
            elif message.get('type') == 'congratulations':
                await manager.broadcast(room_id, {
                    'type': 'congratulations_complete',
                    'results': [
                        {
                            'id': p.id,
                            'name': p.name,
                            'avatar': p.avatar,
                            'score': p.content['scoring']['score'],
                            'lives': p.content['survival']['lives']
                        }
                        for p in room.players.values() if not p.id.startswith("questioner-")  # 排除提问者
                    ]
                })

            elif message.get('type') == 'set_expose_answer':
                room.expose_answer_to_player = message['expose_answer']
                await manager.broadcast_expose_answer(room_id, room.expose_answer_to_player)



    except WebSocketDisconnect:
        user_id = player_info['id']
        await manager.disconnect(room_id, websocket, user_id)
        print(f"已删除一个源于{user_id}的websocket连接")
