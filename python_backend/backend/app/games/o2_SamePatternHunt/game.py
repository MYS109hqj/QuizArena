import json
import time
from typing import Dict, Any, List
from fastapi import WebSocket
from app.games.roundBase import RoundBaseGame
from app.models.player import Player
import random

class o2SPHGame(RoundBaseGame):
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.cards: Dict[str, Dict] = {}  # cardId -> {patternId, imgUrl}
        self.player_targets: Dict[str, List[str]] = {}  # playerId -> 48个目标patternId序列
        self.player_target_index: Dict[str, int] = {}   # playerId -> 当前目标序列索引
        self.scores: Dict[str, int] = {}  # playerId -> score
        self.locked: bool = False

    async def handle_event(self, websocket, event, player_id):
        if event is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "无效事件"})
            return
        action = event.get("action")
        await self.process_action(player_id, action)


    async def update_rules(self, settings):
        if "rules" in settings:

            await self.broadcast({

            })

    async def start_game(self, mode="single", total_rounds=1):
        await super().start_game(mode, total_rounds)
        self.cards = self._init_cards()
        self.scores = {pid: 10 for pid in self.player_order}
        self.locked = False

        # 为每位玩家生成目标序列
        pattern_ids = [f"{i}" for i in range(1, 17)]
        for pid in self.player_order:
            seq = []
            for _ in range(3):
                group = pattern_ids[:]
                random.shuffle(group)
                seq.extend(group)
            self.player_targets[pid] = seq  # 48个目标
            self.player_target_index[pid] = 0  # 初始目标为index:0

        # 广播每位玩家的目标序列（只发给自己）
        for pid in self.player_order:
            await self.broadcast_to_player(pid, {
                "type": "target_sequence",
                "targets": self.player_targets[pid]
            })

        await self.broadcast_game_state()

    def _init_cards(self):
        # 生成16张卡牌，每张有cardId和patternId
        import random
        pattern_ids = [f"{i}" for i in range(1, 17)]
        random.shuffle(pattern_ids)
        cards = {}
        for idx, pattern_id in enumerate(pattern_ids):
            card_id = f"A{idx+1}"
            cards[card_id] = {
                "cardId": card_id,
                "patternId": pattern_id,
                "imgUrl": "empty"
            }
        return cards

    async def process_action(self, player_id, action):
        if action is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "动作信息缺失"})
            return
        if self.locked:
            await self.broadcast_to_player(player_id, {"type": "error", "message": "有动作正在进行"})
            return
        if action.get("type") != "flip":
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "未知动作"})
            return
        card_id = action.get("cardId")
        card = self.cards.get(card_id)
        if not card:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "卡牌不存在"})
            return

        self.locked = True
        # 获取玩家当前目标
        target_idx = self.player_target_index[player_id]
        target_pattern = self.player_targets[player_id][target_idx]
        matched = card["patternId"] == target_pattern
        flip_back = 5000

        # 积分逻辑
        if matched:
            self.scores[player_id] = self.scores.get(player_id, 0) + 1
            # 目标序列前进
            self.player_target_index[player_id] += 1
            # 仍然是该玩家轮次
        else:
            self.scores[player_id] = self.scores.get(player_id, 0) - 1
            self.round += 1
            # 轮到下一位玩家
            self.current_player = self.next_player()

        # 发送翻牌结果
        await self.broadcast({
            "type": "card_flipped",
            "roomId": self.room_id,
            "result": {
                "cardId": card_id,
                "imgUrl": card["imgUrl"],
                "patternId": card["patternId"],
                "matched": matched,
                "flipBack": flip_back
            }
        })
        # 发送最新游戏状态
        await self.broadcast_game_state()
        # 判断是否结束
        await self.check_end_condition()
        # 解锁
        self.locked = False

    async def broadcast_game_state(self):
        # 构造每位玩家的得分和下一目标信息
        game_info = {}
        for pid in self.player_order:
            idx = self.player_target_index.get(pid, 0)
            seq = self.player_targets.get(pid, [])
            next_pattern = seq[idx] if idx < len(seq) else None
            game_info[pid] = {
                "score": self.scores.get(pid, 0),
                "next_pattern": next_pattern,
                "target_index": idx
            }
        await self.broadcast({
            "type": "game_state",
            "state": self.state,
            "current_player": self.current_player,
            "round": self.round,
            "gameInfo": game_info
        })

    def is_game_finished(self) -> bool:
        # 积分为0或>=20或目标序列完成则结束
        for pid, score in self.scores.items():
            if score <= 0 or score >= 20 or self.player_target_index[pid] >= 48:
                return True
        return False

    async def check_end_condition(self):
        if self.is_game_finished():
            self.state = "finished"
            await self.broadcast_game_state()
            # 可在此处广播结算信息
        else:
            # 继续游戏，轮次已在process_action里处理
            pass


