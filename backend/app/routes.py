import json
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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

# 房间类定义
class Room:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.players: Dict[str, Player] = {}
        self.current_question: Optional[Dict] = None  # 当前问题
        self.current_question_id: Optional[str] = None  # 当前问题 ID
        self.total_rounds: Optional[int] = None  # 总轮次（计分模式特有字段）
        self.current_round: Optional[int] = None  # 当前轮次
        self.current_answers: Dict[str, str] = {}  # 收集的答案，以玩家 ID 为键
        self.judgement_pending: bool = False  # 判题标志
        self.mode: str = 'none'  # 添加当前模式属性，默认无模式

# 管理所有房间的连接
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    async def connect(self, room_id: str, websocket: WebSocket, player_info: dict):
        # 如果房间不存在，创建房间
        if room_id not in self.rooms:
            self.rooms[room_id] = Room()

        room = self.rooms[room_id]
        
        # 检查玩家是否已在房间中
        if player_info['id'] in room.players:
            print(f"玩家 {player_info['name']} 已在房间中，更新连接")
            room.connections.append(websocket)  # 直接添加 websocket
            return

        # 新玩家加入
        room.connections.append(websocket)

        # 创建并添加玩家信息
        player = Player(player_info['id'], player_info['name'], player_info['avatar'])
        room.players[player_info['id']] = player  
        print(f"用户加入: {player_info}")

        # 广播玩家加入
        await self.broadcast(room_id, {
            'type': 'notification',
            'message': f"{player_info['name']} has joined the room."
        })

        # 广播当前问题（如果存在）
        if room.current_question:
            await self.broadcast(room_id, {
                'type': 'question',
                'content': room.current_question,
                'question_id': room.current_question_id
            })

        # 暂时：广播模式、当前轮次
        await self.broadcast(room_id, {
            'type': 'mode_change',
            'currentMode': room.mode  # 广播当前模式
        })

        await manager.broadcast(room_id, {
            'type': 'round',
            'totalRounds': room.total_rounds,
            'currentRound': room.current_round
        })

        # 广播更新后的玩家列表
        await self.broadcast(room_id, {
            'type': 'player_list',
            'players': [
                {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'score': p.content['scoring']['score'], 'lives':p.content['survival']['lives']}
                for p in room.players.values()
            ]
        })

    # 断开连接时的处理
    def disconnect(self, room_id: str, websocket: WebSocket, user_id: str):
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if websocket in room.connections:
                room.connections.remove(websocket)
            if user_id in room.players:
                del room.players[user_id]
                print(f"玩家 {user_id} 已离开，删除其信息")
            if not room.connections:
                del self.rooms[room_id]
                print(f"房间 {room_id} 已空，删除房间")

    # 广播消息给房间所有人
    async def broadcast(self, room_id: str, message: dict):
        message_json = json.dumps(message)
        if room_id in self.rooms:
            room = self.rooms[room_id]
            for connection in room.connections:
                await connection.send_text(message_json)
            print("广播发送了信息：", message_json)

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
                room.mode = message['mode']  # 更新房间的模式
                await manager.broadcast(room_id, {
                    'type': 'mode_change',
                    'currentMode': room.mode  # 广播更新后的模式
                })

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
                await manager.broadcast(room_id, {
                    'type': 'round',
                    'totalRounds': room.total_rounds,
                    'currentRound': room.current_round
                })

            # 提问逻辑
            elif message.get('type') == 'question':
                room.current_question = message['content']
                room.current_question_id = message['questionId']
                room.judgement_pending = True  # 设置等待判题标志
                await manager.broadcast(room_id, {
                    'type': 'question',
                    'content': message['content'],
                    'questionId': message['questionId']
                })

            # 答案逻辑
            elif message.get('type') == 'answer':
                player_id = player_info['id']
                if room.judgement_pending:
                    player = room.players[player_id]
                    player.submitted_answer = message['text']
                    player.timestamp = message.get('timestamp')
                    room.current_answers[player_id] = player.submitted_answer
                    # 广播玩家提交的答案
                    await manager.broadcast(room_id, {
                        'type': 'answer',
                        'playerId': player_id,
                        'name': player.name,
                        'avatar': player.avatar,
                        'text': player.submitted_answer
                    })

            # 判题逻辑
            elif message.get('type') == 'judgement':
                # 提问者手动判题，获取结果
                judgement_results = message.get('results', {})

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

                room.judgement_pending = False  # 判题完成，关闭判题状态
                # 向所有玩家广播判题结果
                await manager.broadcast(room_id, {
                    'type': 'judgement_complete',
                    'results': judgement_results
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



    except WebSocketDisconnect:
        user_id = player_info['id']
        manager.disconnect(room_id, websocket, user_id)
        await manager.broadcast(room_id, {
            'type': 'notification',
            'message': f"{player_info['name']} has left the room."
        })
        if room_id in manager.rooms:
            room = manager.rooms[room_id]
            await manager.broadcast(room_id, {
                'type': 'player_list',
                'players': [
                    {'id': p.id, 'name': p.name, 'avatar': p.avatar, 'score': p.content['scoring']['score'], 'lives':p.content['survival']['lives']}
                    for p in room.players.values()
                ]
            })
