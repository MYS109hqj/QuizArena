import json
from numbers import Number
import time
import asyncio
from typing import Dict, Any, List
from fastapi import WebSocket
from app.games.roundBase import RoundBaseGame  # 使用绝对导入
from app.models.player import Player  # 使用绝对导入
import random
import httpx
from datetime import datetime
from app.database import get_db
from app.models.user import User

class o2SPHGame(RoundBaseGame):
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.cards: Dict[str, Dict] = {}  # cardId -> {patternId, imgUrl}
        self.player_targets: Dict[str, List[str]] = {}  # playerId -> 48个目标patternId序列
        self.player_target_index: Dict[str, int] = {}   # playerId -> 当前目标序列索引
        self.scores: Dict[str, int] = {}  # playerId -> score
        self.locked: bool = False
        self.config: Dict[str, Any] = {
            "max_players": 2,
            "min_players": 1  # 新增最小玩家数配置
        }
        
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
            self.game_rules.update(settings["rules"])
            
            await self.broadcast({
                "type": "rules_updated",
                "rules": self.game_rules
            })

    async def start_game(self, mode="single", total_rounds=1):
        await super().start_game(mode, total_rounds)
        self.cards = self._init_cards()

        self.player_order = self._init_player_order()
        if mode=="single":
            self.scores = {pid: 15 for pid in self.player_order}
        else:
            self.scores = {pid: 10 for pid in self.player_order}
        self.locked = False
        
        # 记录游戏开始时间
        self.start_time = datetime.utcnow()
        
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
            # 记录游戏结果
            await self.record_game_results()
        else:
            # 继续游戏，轮次已在process_action里处理
            pass

    async def record_game_results(self):
        """记录游戏结果到数据库"""
        print(f"🎮 开始记录游戏结果，房间ID: {self.room_id}")
        try:
            # 计算游戏统计信息
            total_rounds = 48  # SPH游戏固定48个目标
            completed_rounds = sum(self.player_target_index.values())
            accuracy = completed_rounds / total_rounds * 100 if total_rounds > 0 else 0
            
            print(f"游戏统计: 总轮次 {total_rounds}, 已完成 {completed_rounds}, 总体准确率 {accuracy:.2f}%")
            print(f"玩家列表: {self.player_order}")
            print(f"玩家得分: {self.scores}")
            print(f"玩家进度: {self.player_target_index}")
            
            # 为每个玩家记录游戏结果
            for player_id in self.player_order:
                player_score = self.scores.get(player_id, 0)
                player_rounds = self.player_target_index.get(player_id, 0)
                player_accuracy = player_rounds / total_rounds * 100 if total_rounds > 0 else 0
                
                print(f"🔄 处理玩家 {player_id} 的游戏记录: 得分 {player_score}, 完成轮次 {player_rounds}, 准确率 {player_accuracy:.2f}%")
                
                # 直接与数据库交互记录游戏结果，避免HTTP请求和认证问题
                session_id = await self.create_game_record_direct(player_id, player_score, player_accuracy, player_rounds, total_rounds)
                
                if session_id:
                    print(f"✅ 玩家 {player_id} 的游戏记录创建成功，会话ID: {session_id}")
                else:
                    print(f"❌ 玩家 {player_id} 的游戏记录创建失败")
            
            print(f"🎯 游戏结果记录完成，房间ID: {self.room_id}")
            
        except Exception as e:
            print(f"❌ 记录游戏结果失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    async def create_game_record_direct(self, player_id: str, score: int, accuracy: float, rounds_played: int, rounds_total: int):
        """直接与数据库交互创建游戏记录，避免HTTP请求和认证问题"""
        print(f"开始创建游戏记录: 玩家 {player_id}, 得分 {score}, 准确率 {accuracy:.2f}%")
        session_id = None
        try:
            # if not player_id:
            #     print(f"错误: 未获取玩家 {player_id} 的用户ID")
            #     return None
            
            
            # 直接使用数据库会话创建游戏记录
            from app.database import get_db
            from app.models.game_record import GameSession
            
            # 确保start_time不为None
            if self.start_time is None:
                print("警告: start_time未初始化，使用当前时间")
                game_duration = 0
                start_time = datetime.utcnow()
            else:
                game_duration = int((datetime.utcnow() - self.start_time).total_seconds())
                start_time = self.start_time
            
            # 为MySQL DECIMAL类型做特殊处理
            # 将float转换为适合DECIMAL(5,2)的格式
            accuracy_decimal = round(accuracy, 2)
            print(f"准备数据: user_id={player_id}, game_type=same_pattern_hunt, score={score}, accuracy={accuracy_decimal}, duration={game_duration}")
            
            # 在异步环境中使用数据库会话
            db = None
            try:
                # 获取数据库会话
                db = next(get_db())
                print("数据库会话获取成功")
                
                # 创建游戏会话记录
                game_session = GameSession(
                    user_id=player_id,
                    game_type="same_pattern_hunt",
                    room_id=self.room_id,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    duration_seconds=game_duration,
                    score=score,
                    accuracy=accuracy_decimal,  # 使用四舍五入后的精度值
                    rounds_played=rounds_played,
                    rounds_total=rounds_total,
                    status="completed"
                )
                
                print(f"准备添加游戏会话记录: {game_session.to_dict()}")
                db.add(game_session)
                
                # 尝试提交事务
                print("尝试提交数据库事务...")
                db.commit()
                print("数据库事务提交成功")
                
                # 刷新获取ID
                db.refresh(game_session)
                session_id = game_session.id
                print(f"✓ 游戏记录直接创建成功: 玩家 {player_id}, 用户ID {player_id}, 得分 {score}, 会话ID: {session_id}")
                
                # 更新玩家统计信息
                await self.update_player_stats_direct(player_id, "same_pattern_hunt", score, accuracy_decimal, game_duration)
                
            except Exception as db_error:
                if db:
                    print(f"❌ 数据库操作失败，执行回滚: {str(db_error)}")
                    db.rollback()
                else:
                    print(f"❌ 数据库会话获取失败: {str(db_error)}")
                # 尝试获取更多错误详情
                import traceback
                error_trace = traceback.format_exc()
                print(f"错误详情: {error_trace}")
                # 检查是否是精度类型错误
                if "DECIMAL" in str(db_error) or "decimal" in str(db_error):
                    print("⚠️ 可能是DECIMAL类型转换错误，请检查精度值")
            finally:
                if db:
                    print("关闭数据库会话")
                    db.close()
                
            return session_id  # 返回创建的会话ID
                
        except Exception as e:
            print(f"❌ 创建游戏记录失败(外层异常): {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    async def update_player_stats_direct(self, user_id: int, game_type: str, score: int, accuracy: float, duration: int):
        """直接更新玩家统计信息"""
        print(f"开始更新玩家统计: 用户ID {user_id}, 游戏类型 {game_type}, 最新得分 {score}, 最新准确率 {accuracy:.2f}%")
        try:
            from app.database import get_db
            from app.models.game_record import PlayerStats, GameSession
            from sqlalchemy import func
            
            # 为MySQL DECIMAL类型做特殊处理
            accuracy_decimal = round(accuracy, 2)
            print(f"处理后的精度值: {accuracy_decimal}")
            
            # 在异步环境中使用数据库会话
            db = None
            try:
                # 获取数据库会话
                db = next(get_db())
                print("统计更新: 数据库会话获取成功")
                
                # 查询现有统计信息
                print(f"尝试查找现有统计记录: 用户ID={user_id}, 游戏类型={game_type}")
                existing_stats = db.query(PlayerStats).filter(
                    PlayerStats.user_id == user_id,
                    PlayerStats.game_type == game_type
                ).first()
                
                if existing_stats:
                    print(f"找到现有统计记录: {existing_stats.to_dict()}")
                else:
                    print("未找到现有统计记录，准备创建新记录")
                
                # 计算最新的统计数据
                print("计算最新统计数据...")
                stats_result = db.query(
                    func.count(GameSession.id).label('total_games'),
                    func.sum(GameSession.score).label('total_score'),
                    func.avg(GameSession.score).label('average_score'),
                    func.max(GameSession.score).label('best_score'),
                    func.avg(GameSession.accuracy).label('average_accuracy'),
                    func.sum(GameSession.duration_seconds).label('total_play_time'),
                    func.max(GameSession.end_time).label('last_played')
                ).filter(
                    GameSession.user_id == user_id,
                    GameSession.game_type == game_type
                ).first()
                
                # 准备统计数据，确保所有值都有默认值
                total_games = stats_result.total_games or 0
                total_score = stats_result.total_score or 0
                average_score = float(stats_result.average_score or 0)
                average_score_rounded = round(average_score, 2)
                best_score = stats_result.best_score or 0
                average_accuracy = float(stats_result.average_accuracy or 0)
                average_accuracy_rounded = round(average_accuracy, 2)
                total_play_time = stats_result.total_play_time or 0
                last_played = stats_result.last_played or datetime.utcnow()
                
                print(f"计算结果: 总游戏数={total_games}, 总得分={total_score}, 平均得分={average_score_rounded}, 最高得分={best_score}, 平均准确率={average_accuracy_rounded}%")
                
                if existing_stats:
                    # 更新现有统计
                    print("更新现有统计记录...")
                    existing_stats.total_games = total_games
                    existing_stats.total_score = total_score
                    existing_stats.average_score = average_score_rounded  # 四舍五入到2位小数
                    existing_stats.best_score = best_score
                    existing_stats.average_accuracy = average_accuracy_rounded  # 四舍五入到2位小数
                    existing_stats.total_play_time_seconds = total_play_time
                    existing_stats.last_played = last_played
                    existing_stats.updated_at = datetime.utcnow()
                else:
                    # 创建新的统计记录
                    print("创建新的统计记录...")
                    new_stats = PlayerStats(
                        user_id=user_id,
                        game_type=game_type,
                        total_games=total_games,
                        total_score=total_score,
                        average_score=average_score_rounded,  # 四舍五入到2位小数
                        best_score=best_score,
                        average_accuracy=average_accuracy_rounded,  # 四舍五入到2位小数
                        total_play_time_seconds=total_play_time,
                        last_played=last_played,
                        updated_at=datetime.utcnow()
                    )
                    print(f"新统计记录数据: {new_stats.to_dict()}")
                    db.add(new_stats)
                
                print("尝试提交统计更新事务...")
                db.commit()
                print(f"✅ 玩家统计信息更新成功: 用户ID {user_id}, 游戏类型 {game_type}")
                
            except Exception as db_error:
                if db:
                    print(f"❌ 更新玩家统计失败，执行回滚: {str(db_error)}")
                    db.rollback()
                else:
                    print(f"❌ 统计更新: 数据库会话获取失败: {str(db_error)}")
                # 尝试获取更多错误详情
                import traceback
                error_trace = traceback.format_exc()
                print(f"统计更新错误详情: {error_trace}")
                # 检查是否是精度类型错误
                if "DECIMAL" in str(db_error) or "decimal" in str(db_error):
                    print("⚠️ 统计更新: 可能是DECIMAL类型转换错误，请检查精度值")
            finally:
                if db:
                    print("统计更新: 关闭数据库会话")
                    db.close()
                
        except Exception as e:
            print(f"❌ 更新玩家统计失败(外层异常): {str(e)}")
            import traceback
            print(traceback.format_exc())


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


