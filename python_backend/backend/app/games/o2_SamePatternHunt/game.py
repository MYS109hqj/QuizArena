import json
import time
import asyncio
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
        
        # 规则配置
        self.game_rules = {
            "allowSimultaneousActions": True,
            "flipRestrictions": {
                "preventFlipDuringAnimation": False,
                "waitForOthersToFlipBack": False,
                "actionLockEnabled": True
            },
            "animationDuration": 5000,
            "maxConcurrentFlips": 1,
            "turnTransitionDelay": 1000
        }
        
        # 全局翻转状态跟踪
        self.global_flipping_cards: Dict[str, List[str]] = {}  # playerId -> [cardIds]
        self.flip_start_times: Dict[str, float] = {}  # cardId -> start time

    async def handle_event(self, websocket, event, player_id):
        if event is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "无效事件"})
            return
        
        # 处理规则更新请求
        if event.get("type") == "update_rules":
            await self.update_rules(event)
            return
            
        # 处理观看终局页面请求
        if event.get("type") == "view_final_state":
            print("view_final_state处理观看终局页面请求")
            await self.send_final_state(player_id)
            return
            
        action = event.get("action")
        await self.process_action(player_id, action)


    async def update_rules(self, settings):
        """更新游戏规则"""
        if "rules" in settings:
            # 更新规则配置
            self.game_rules.update(settings["rules"])
            
            # 广播规则更新给所有玩家
            await self.broadcast({
                "type": "rules_updated",
                "rules": self.game_rules
            })

    async def start_game(self, mode="single", total_rounds=1):
        await super().start_game(mode, total_rounds)
        self.cards = self._init_cards()
        self.scores = {pid: 10 for pid in self.player_order}
        self.locked = False
        
        # 重置全局翻转状态
        self.global_flipping_cards = {}
        self.flip_start_times = {}

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
            
        # 检查行动锁定规则
        if self.game_rules["flipRestrictions"]["actionLockEnabled"] and self.locked:
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

        # 检查动画期间禁止翻牌规则
        if self.game_rules["flipRestrictions"]["preventFlipDuringAnimation"]:
            current_time = time.time()
            for flip_card_id, start_time in self.flip_start_times.items():
                elapsed = current_time - start_time
                if elapsed < self.game_rules["animationDuration"] / 1000:
                    await self.broadcast_to_player(player_id, {
                        "type": "error", 
                        "message": "牌未翻回，无法翻开新牌"
                    })
                    return

        # 检查等待他人翻回规则
        if (self.game_rules["flipRestrictions"]["waitForOthersToFlipBack"] and 
            player_id == self.current_player):
            current_time = time.time()
            for other_player_id, flipping_cards in self.global_flipping_cards.items():
                if other_player_id != player_id:
                    for flip_card_id in flipping_cards:
                        start_time = self.flip_start_times.get(flip_card_id, 0)
                        elapsed = current_time - start_time
                        if elapsed < self.game_rules["animationDuration"] / 1000:
                            await self.broadcast_to_player(player_id, {
                                "type": "error", 
                                "message": "其他玩家翻开的牌未翻回，无法立刻翻牌"
                            })
                            return

        self.locked = True
        # 记录翻牌开始时间
        self.flip_start_times[card_id] = time.time()
        # 添加到全局翻转卡片列表
        if player_id not in self.global_flipping_cards:
            self.global_flipping_cards[player_id] = []
        self.global_flipping_cards[player_id].append(card_id)
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
        
        # 清理翻转状态（在动画结束后）
        async def cleanup_flip_state():
            await asyncio.sleep(flip_back / 1000)
            # 从全局翻转状态中移除
            if player_id in self.global_flipping_cards:
                self.global_flipping_cards[player_id] = [
                    cid for cid in self.global_flipping_cards[player_id] 
                    if cid != card_id
                ]
                if not self.global_flipping_cards[player_id]:
                    del self.global_flipping_cards[player_id]
            if card_id in self.flip_start_times:
                del self.flip_start_times[card_id]
        
        # 异步执行清理任务
        asyncio.create_task(cleanup_flip_state())
        
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

    async def send_final_state(self, player_id: str):
        """发送终局状态数据给指定玩家"""
        if self.state != "finished":
            await self.broadcast_to_player(player_id, {
                "type": "error",
                "message": "游戏尚未结束，无法查看终局页面"
            })
            return
            
        # 构建终局数据：所有卡牌的图案信息
        final_state = {
            "type": "final_state",
            "cards": self.cards,  # 包含所有卡牌的patternId信息
            "scores": self.scores,
            "player_targets": self.player_targets,
            "player_target_index": self.player_target_index
        }
        
        print(f"📤 发送终局状态给玩家 {player_id}: {final_state}")
        await self.broadcast_to_player(player_id, final_state)

    def _get_player_flipping_card(self, card_id: str) -> str:
        """获取正在翻转某张卡片的玩家ID"""
        for player_id, flipping_cards in self.global_flipping_cards.items():
            if card_id in flipping_cards:
                return player_id
        return None

    async def get_card_flip_status(self):
        """获取当前所有卡牌的翻转状态"""
        flip_status = {}
        current_time = time.time()
        
        for card_id, start_time in self.flip_start_times.items():
            elapsed = current_time - start_time
            animation_duration = self.game_rules["animationDuration"] / 1000
            
            if elapsed < animation_duration:
                # 卡牌正在翻转中
                remaining = animation_duration - elapsed
                flip_status[card_id] = {
                    "flipping": True,
                    "remaining_time": remaining * 1000,  # 毫秒
                    "flipped_by": self._get_player_flipping_card(card_id)
                }
            else:
                # 卡牌已翻转完成或超时
                flip_status[card_id] = {"flipping": False}
        
        # 添加未在翻转中的卡牌状态
        for card_id in self.cards.keys():
            if card_id not in flip_status:
                flip_status[card_id] = {"flipping": False}
                
        return flip_status

    async def on_player_reconnect(self, player_id: str):
        """处理玩家重连，发送完整状态同步"""
        # 发送完整的游戏状态
        await self.broadcast_game_state()
        
        # 发送当前所有卡牌状态
        await self.broadcast_to_player(player_id, {
            "type": "cards_sync",
            "cards": self.cards
        })
        
        # 发送卡牌瞬态翻转状态
        flip_status = await self.get_card_flip_status()
        await self.broadcast_to_player(player_id, {
            "type": "flip_status_sync", 
            "flip_status": flip_status
        })
        
        # 发送玩家个人进度
        await self.broadcast_to_player(player_id, {
            "type": "player_sync",
            "targets": self.player_targets[player_id],
            "current_index": self.player_target_index[player_id],
            "score": self.scores[player_id]
        })
        
        print(f"玩家 {player_id} 重连状态同步完成")


