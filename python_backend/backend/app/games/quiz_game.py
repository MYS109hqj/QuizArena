import json
import time
from typing import Dict, Any, List
from fastapi import WebSocket
from .base import BaseGame
from models.player import Player

class QuizGame(BaseGame):
    """答题游戏实现"""
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.current_question: Dict[str, Any] = None
        self.current_question_id: str = None  # 新增：记录当前题目ID
        self.current_answers: Dict[str, str] = {}  # 玩家ID->答案
        self.judgement_pending: bool = False  # 是否等待判题
        self.current_round: int = 1  # 当前轮次
        self.total_rounds: int = 1  # 总轮次
        self.reconnect_timeout: int = 5  # 重连超时时间（秒）
        self.config: Dict[str, Any] = {
            "expose_answer": False  # 答案是否对其他答题者可见
        }

    async def handle_event(self, websocket: WebSocket, event: Dict[str, Any]) -> None:
        """处理答题游戏特有事件"""
        event_type = event.get("type")
        print(event_type,event)
        player_id = self.connections[websocket]

        if event_type == "mode_change":
            await self._handle_mode_change(event)
        elif event_type == "question":
            await self._handle_question(event)
        elif event_type == "answer":
            await self._handle_answer(websocket, event, player_id)
        elif event_type == "judgement":
            await self._handle_judgement(event)
        elif event_type == "get_latest_answers":
            await self._handle_get_latest_answers(websocket)
        elif event_type == "sync_time":
            await self._handle_sync_time(websocket, event)
            await self._handle_broadcast_playerlist()
        elif event_type == "timeout_change":
            await self._handle_timeout_change(event)
        elif event_type == "initialize_scores":
            await self._handle_initialize_scores(event)
        elif event_type == "initialize_lives":
            await self._handle_initialize_lives(event)
        elif event_type == "round_update":
            await self._handle_round_update(event)
        elif event_type == "set_expose_answer":
            await self._handle_set_expose_answer(event)
        elif event_type == "congratulations":
            await self._handle_congratulations()
            

    async def _handle_sync_time(self, websocket: WebSocket, event: Dict[str, Any]) -> None:
        # 1. 获取服务器当前毫秒级时间（time.time() 返回秒级，*1000 转为毫秒）
        server_current_time = int(time.time() * 1000)
        # 2. 构造响应：包含服务器时间 + 前端请求时的客户端时间（用于前端计算偏移量）
        sync_response = {
            "type": "time_sync_response",
            "serverTime": server_current_time,
            "clientRequestTime": event.get("clientRequestTime")  # 回传前端请求时的时间
        }
        # 3. 仅向发起同步的前端返回响应
        await websocket.send_text(json.dumps(sync_response))

    async def _handle_mode_change(self, event: Dict[str, Any]) -> None:
        self.mode = event["mode"]
        await self.broadcast({
            "type": "mode_change",
            "currentMode": self.mode
        })

    async def _handle_question(self, event: Dict[str, Any]) -> None:
        self.current_question = event["content"]
        self.current_question_id = event["questionId"]  # 记录题目ID
        self.current_answers.clear()
        self.judgement_pending = True
        await self.broadcast({
            "type": "question",
            "content": self.current_question,
            "questionId": self.current_question_id
        })

    async def _handle_answer(self, websocket: WebSocket, event: Dict[str, Any], player_id: str) -> None:
        if not self.judgement_pending:
            return

        # 记录答案
        player = self.players[player_id]
        player.submitted_answer = event["text"]
        
                # ===== 时间戳处理逻辑 =====
        # 1. 获取客户端提交的毫秒级时间戳（前端已同步校准）
        client_timestamp = event.get("timestamp")
        # 2. 获取服务器当前毫秒级时间（关键修复：将秒级转为毫秒级）
        server_current_time = time.time() * 1000  # 乘以1000转为毫秒
        # 3. 定义合理时间范围（±30秒 = 30000毫秒，单位统一）
        time_threshold = 30 * 1000  # 毫秒级阈值

        # 4. 校验并确定最终时间戳
        if client_timestamp is not None:
            try:
                # 确保时间戳为数字（兼容前端可能的字符串格式）
                client_timestamp = float(client_timestamp)
                # 打印调试信息（方便排查）
                time_diff = abs(client_timestamp - server_current_time)
                print(f"调试：玩家{player_id} 前端时间={client_timestamp}，服务器时间={server_current_time}，差值={time_diff}s")
                # 检查是否在合理范围内（允许一定网络延迟）
                if (server_current_time - time_threshold 
                    <= client_timestamp 
                    <= server_current_time + time_threshold):
                    # 有效时间戳，使用客户端同步后的时间
                    player.timestamp = client_timestamp
                else:
                    # 超出合理范围，使用服务器时间并记录警告
                    player.timestamp = server_current_time
                    print(f"玩家 {player_id} 提交的时间戳超出合理范围（差值{time_diff}s），已使用服务器时间")
            except (ValueError, TypeError):
                # 时间戳格式错误，使用服务器时间
                player.timestamp = server_current_time
                print(f"玩家 {player_id} 提交的时间戳格式无效（{client_timestamp}），已使用服务器时间")
        else:
            # 未提交时间戳，使用服务器时间
            player.timestamp = server_current_time
            print(f"玩家 {player_id} 未提交时间戳，已使用服务器时间")
        # =========================

        self.current_answers[player_id] = player.submitted_answer

        # 构造消息（区分提问者和答题者）
        questioner_msg = {
            "type": "answer",
            "playerId": player_id,
            "name": player.name,
            "avatar": player.avatar,
            "text": player.submitted_answer,
            "timestamp": player.timestamp
        }
        player_msg = questioner_msg.copy()
        if not self.config["expose_answer"]:
            player_msg["text"] = "[Hidden]"

        # 发送消息
        for conn, pid in self.connections.items():
            if pid.startswith("questioner-"):
                await conn.send_text(json.dumps(questioner_msg))
            elif pid == player_id:
                await conn.send_text(json.dumps(questioner_msg))
            else:
                await conn.send_text(json.dumps(player_msg))

    async def _handle_judgement(self, event: Dict[str, Any]) -> None:
        judgement_results = event.get("results", {})
        updated_results = {}

        # 处理判题结果
        for player_id, result in judgement_results.items():
            if player_id not in self.players:
                continue
            player = self.players[player_id]

            if self.mode == "scoring":
                player.content["scoring"]["score"] += result.get("score", 0)
            elif self.mode == "survival":
                player.content["survival"]["lives"] -= result.get("lostLives", 0)

            updated_results[player_id] = {
                "name": player.name,
                "avatar": player.avatar,
                "correct": result.get("correct", False),
                "score": result.get("score") if self.mode == "scoring" else None,
                "lostLives": result.get("lostLives") if self.mode == "survival" else None
            }

        self.judgement_pending = False
        await self.broadcast({
            "type": "judgement_complete",
            "results": updated_results,
            "correct_answer": event.get("correct_answer", ""),
            "explanation": event.get("explanation", ""),
            "round": event.get("currentRound", self.current_round)  # 补充轮次信息
        })

        # 广播玩家状态更新
        await self._handle_broadcast_playerlist()

    async def _handle_get_latest_answers(self, websocket: WebSocket) -> None:
        # 返回包含毫秒级时间戳的答案列表，供前端排序
        latest_answers = [
            {
                "id": p.id,
                "name": p.name,
                "avatar": p.avatar,
                "submitted_answer": p.submitted_answer,
                "timestamp": p.timestamp  # 毫秒级时间戳
            }
            for p in self.players.values()
            if not p.id.startswith("questioner-")
        ]
        await websocket.send_text(json.dumps({
            "type": "latest_answers",
            "latest_answers": latest_answers
        }))

    # 新增：处理重连超时时间变更
    async def _handle_timeout_change(self, event: Dict[str, Any]) -> None:
        self.reconnect_timeout = int(event["reconnect_timeout"])
        # 广播超时时间更新（仅向提问者）
        await self.broadcast_to_roles({
            "type": "timeout_updated",
            "timeout": self.reconnect_timeout
        }, roles=["questioner"])

    # 新增：初始化所有玩家分数
    async def _handle_initialize_scores(self, event: Dict[str, Any]) -> None:
        score = event["score"]
        for player in self.players.values():
            player.content["scoring"]["score"] = score
        # 广播更新后的玩家列表
        await self._handle_broadcast_playerlist()

    # 新增：初始化所有玩家生命值
    async def _handle_initialize_lives(self, event: Dict[str, Any]) -> None:
        lives = event["lives"]
        for player in self.players.values():
            player.content["survival"]["lives"] = lives
        # 广播更新后的玩家列表
        await self._handle_broadcast_playerlist()

    # 新增：处理轮次更新
    async def _handle_round_update(self, event: Dict[str, Any]) -> None:
        self.current_round = event["currentRound"]
        self.total_rounds = event["totalRounds"]
        await self.broadcast({
            "type": "round",
            "totalRounds": self.total_rounds,
            "currentRound": self.current_round
        })

    # 新增：设置答案可见性
    async def _handle_set_expose_answer(self, event: Dict[str, Any]) -> None:
        self.config["expose_answer"] = event["expose_answer"]
        await self.broadcast({
            "type": "expose_answer_update",
            "value": self.config["expose_answer"]
        })

    # 新增：处理结算信息
    async def _handle_congratulations(self) -> None:
        await self.broadcast({
            "type": "congratulations_complete",
            "results": [
                {
                    "id": p.id,
                    "name": p.name,
                    "avatar": p.avatar,
                    "score": p.content["scoring"]["score"],
                    "lives": p.content["survival"]["lives"]
                }
                for p in self.players.values()
                if not p.id.startswith("questioner-")  # 排除提问者
            ]
        })

    async def _handle_broadcast_playerlist(self) -> None:
        # 广播更新后的玩家列表
        await self.broadcast({
            "type": "player_list",
            "players": [self._format_player(p) for p in self.players.values()]
        })

    async def broadcast(self, data: Dict[str, Any], exclude: WebSocket = None) -> None:
        """广播消息给所有连接"""
        data_str = json.dumps(data)
        for websocket in self.connections:
            if websocket != exclude:
                await websocket.send_text(data_str)

    async def broadcast_to_roles(self, data: Dict[str, Any], roles: List[str] = ["questioner", "player"]) -> None:
        """向指定角色广播消息（提问者/答题者）"""
        data_str = json.dumps(data)
        for conn, pid in self.connections.items():
            if (
                ("questioner" in roles and pid.startswith("questioner-")) or
                ("player" in roles and pid.startswith("user-"))
            ):
                await conn.send_text(data_str)

    def _format_player(self, player: Player) -> Dict[str, Any]:
        """格式化玩家信息"""
        return {
            "id": player.id,
            "name": player.name,
            "avatar": player.avatar,
            "score": player.content["scoring"]["score"],
            "lives": player.content["survival"]["lives"],
            "timestamp": player.timestamp
        }
    