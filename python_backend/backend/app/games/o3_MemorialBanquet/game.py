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
from .observers import SPHGameObserver

class o3MBGame(RoundBaseGame):
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.scores: Dict[str, int] = {}  # playerId -> score
        self.error_counts: Dict[str, int] = {}  # playerId -> 错误次数
        self.locked: bool = False
        self.config: Dict[str, Any] = {
            "max_players": 2,
            "min_players": 1,
            "difficulty": "normal"  # 添加难度设置：normal, hard, extreme
        }
        self.cards: Dict[str, Dict] = {}  # cardId -> {number, imgUrl}
        
        # 初始化成就观察者
        self.achievement_observer = SPHGameObserver(self)
        
        self.game_rules = {
            "allowSimultaneousActions": True,
            "flipRestrictions": {
                "preventFlipDuringAnimation": True,
                "waitForOthersToFlipBack": False,
                "actionLockEnabled": True
            },
            "animationDuration": 1000,
            "maxConcurrentFlips": 2,
            "turnTransitionDelay": 1000
        }
        
        # 全局翻转状态跟踪
        self.global_flipping_cards: Dict[str, List[str]] = {}  # playerId -> [cardIds]
        self.flip_start_times: Dict[str, float] = {}  # cardId -> start time
        self.current_flip_cards: List[str] = []  # 当前玩家翻开的卡牌列表
        self.start_time = None  # 游戏开始时间
        self.preview_duration = 10  # 预览时长30秒
        self.pending_upgrade = None  # 待升级的卡牌对

    async def handle_event(self, websocket, event, player_id):
        print(f"📥 收到事件: {event}, 玩家: {player_id}")
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
        print(f"🎯 处理动作: {action}")
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

        # 不需要重新初始化 player_order，因为 super().start_game 已经初始化了
        # self.player_order = self._init_player_order()
        
        if mode=="single":
            self.scores = {pid: -15 for pid in self.player_order}
        else:
            self.scores = {pid: -10 for pid in self.player_order}
        
        self.error_counts = {pid: 0 for pid in self.player_order}
        self.locked = False
        
        self.current_flip_cards = []
        
        self.start_time = datetime.utcnow()
        
        self.global_flipping_cards = {}
        self.flip_start_times = {}
        
        self.pending_upgrade = None

        await self.broadcast_game_state()
        
        # 发送卡牌信息
        await self.broadcast({
            "type": "cards_sync",
            "cards": self.cards
        })

    def _init_cards(self):
        import random
        difficulty = self.config.get("difficulty", "normal")
        
        if difficulty == "hard":
            numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8] * 2  # 生成两组0-8，共18个数字
            letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S']
        elif difficulty == "extreme":
            numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] * 2  # 生成两组0-11，共24个数字
            letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        else:  # normal (默认)
            numbers = [0, 1, 2, 3, 4, 5] * 2  # 生成两组0-5，共12个数字
            letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
        
        random.shuffle(numbers)
        cards = {}
        for idx, number in enumerate(numbers):
            letter = letters[idx]
            card_id = f"{letter}1"
            cards[card_id] = {
                "cardId": card_id,
                "number": number,
                "imgUrl": "empty"
            }
        return cards

    async def process_action(self, player_id, action):
        print(f"🔧 process_action: 玩家 {player_id}, 动作 {action}")
        if action is None:
            await self.broadcast_to_player(player_id, {"type": "error", "msg": "动作信息缺失"})
            return
        
        # 检查是否在预览期间
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            if elapsed < self.preview_duration:
                print(f"⏱️ 预览期间: 已经过 {elapsed:.2f} 秒, 预览时长 {self.preview_duration} 秒")
                await self.broadcast_to_player(player_id, {
                    "type": "error", 
                    "message": "预览期间无法翻牌"
                })
                return
            
        # 升级操作不受锁定限制
        if action.get("type") != "upgrade_card":
            # 检查行动锁定规则
            if self.game_rules["flipRestrictions"]["actionLockEnabled"] and self.locked:
                await self.broadcast_to_player(player_id, {"type": "error", "message": "有动作正在进行"})
                return
            
        if action.get("type") == "flip":
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
                        # 如果已经翻了一张牌，允许翻第二张
                        if len(self.current_flip_cards) == 0:
                            await self.broadcast_to_player(player_id, {
                                "type": "error", 
                                "message": "牌未翻回，无法翻开新牌"
                            })
                            return

            # 检查是否已经翻了两张牌
            if len(self.current_flip_cards) >= 2:
                await self.broadcast_to_player(player_id, {
                    "type": "error", 
                    "message": "已经翻了两张牌，请等待"
                })
                return

            # 检查是否重复翻开同一张牌
            if card_id in self.current_flip_cards:
                await self.broadcast_to_player(player_id, {
                    "type": "error", 
                    "message": "不能重复翻开同一张牌"
                })
                return

            # 翻第二张牌时才锁定
            if len(self.current_flip_cards) == 1:
                self.locked = True
            
            # 记录翻牌开始时间
            self.flip_start_times[card_id] = time.time()
            # 添加到全局翻转卡片列表
            if player_id not in self.global_flipping_cards:
                self.global_flipping_cards[player_id] = []
            self.global_flipping_cards[player_id].append(card_id)
            # 添加到当前翻牌列表
            self.current_flip_cards.append(card_id)
            
            flip_back = self.game_rules["animationDuration"]

            # 发送翻牌结果
            await self.broadcast({
                "type": "card_flipped",
                "roomId": self.room_id,
                "result": {
                    "cardId": card_id,
                    "number": card["number"],
                    "imgUrl": card["imgUrl"],
                    "flipBack": flip_back
                }
            })
            
            # 如果翻了两张牌，判断是否匹配
            if len(self.current_flip_cards) == 2:
                card1_id = self.current_flip_cards[0]
                card2_id = self.current_flip_cards[1]
                card1 = self.cards[card1_id]
                card2 = self.cards[card2_id]
                
                matched = card1["number"] == card2["number"]
                
                # 积分逻辑
                if matched:
                    self.scores[player_id] = self.scores.get(player_id, 0) + 1
                    # 匹配成功，等待玩家选择升级哪张卡牌
                    self.pending_upgrade = {
                        "player_id": player_id,
                        "card1_id": card1_id,
                        "card2_id": card2_id,
                        "number": card1["number"]
                    }
                else:
                    self.scores[player_id] = self.scores.get(player_id, 0) - 1
                    self.error_counts[player_id] = self.error_counts.get(player_id, 0) + 1
                
                # 无论是否匹配，都轮到下一位玩家
                self.current_player = self.next_player()
                
                # 发送匹配结果
                await self.broadcast({
                    "type": "flip_result",
                    "roomId": self.room_id,
                    "result": {
                        "matched": matched,
                        "card1Id": card1_id,
                        "card2Id": card2_id,
                        "number": card1["number"],
                        "score": self.scores[player_id],
                        "errorCount": self.error_counts[player_id],
                        "pendingUpgrade": self.pending_upgrade is not None
                    }
                })
                
                # 如果匹配失败，清空当前翻牌列表并解锁
                if not matched:
                    self.current_flip_cards = []
                    self.locked = False
                # 如果匹配成功，解锁游戏，让玩家能够选择升级
                elif matched:
                    self.locked = False
                
                # 发送最新游戏状态
                await self.broadcast_game_state()
                # 判断是否结束
                await self.check_end_condition()
        elif action.get("type") == "upgrade_card":
            # 处理卡牌升级选择
            if not self.pending_upgrade:
                await self.broadcast_to_player(player_id, {"type": "error", "msg": "没有待升级的卡牌"})
                return
            
            if player_id != self.pending_upgrade["player_id"]:
                await self.broadcast_to_player(player_id, {"type": "error", "msg": "只能升级自己匹配的卡牌"})
                return
            
            card_id = action.get("cardId")
            if card_id not in [self.pending_upgrade["card1_id"], self.pending_upgrade["card2_id"]]:
                await self.broadcast_to_player(player_id, {"type": "error", "msg": "只能升级匹配的两张卡牌之一"})
                return
            
            # 保存卡牌ID，用于后续翻回
            card1_id = self.pending_upgrade["card1_id"]
            card2_id = self.pending_upgrade["card2_id"]
            
            # 升级卡牌
            self.cards[card_id]["number"] += 1
            
            # 广播升级结果
            await self.broadcast({
                "type": "card_upgraded",
                "roomId": self.room_id,
                "result": {
                    "cardId": card_id,
                    "newNumber": self.cards[card_id]["number"],
                    "playerId": player_id
                }
            })
            
            # 清除待升级状态
            self.pending_upgrade = None
            
            # 等待2秒后翻回卡牌
            await asyncio.sleep(2)
            
            # 清空当前翻牌列表
            self.current_flip_cards = []
            self.locked = False
            
            # 发送最新游戏状态
            await self.broadcast_game_state()
            # 判断是否结束
            await self.check_end_condition()
        
        # 清理翻转状态（在动画结束后）
        async def cleanup_flip_state():
            await asyncio.sleep(self.game_rules["animationDuration"] / 1000)
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
            # 解锁
            if len(self.current_flip_cards) == 0:
                self.locked = False
        
        # 异步执行清理任务
        asyncio.create_task(cleanup_flip_state())

    async def broadcast_game_state(self):
        game_info = {}
        for pid in self.player_order:
            game_info[pid] = {
                "score": self.scores.get(pid, 0),
                "errorCount": self.error_counts.get(pid, 0)
            }
        
        # 计算是否在预览期内
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            is_preview = elapsed < self.preview_duration
        else:
            elapsed = 0
            is_preview = False
        
        await self.broadcast({
            "type": "game_state",
            "state": self.state,
            "current_player": self.current_player,
            "round": self.round,
            "gameInfo": game_info,
            "isPreview": is_preview,
            "previewRemaining": max(0, self.preview_duration - elapsed)
        })

    def is_game_finished(self) -> bool:
        # 累计错误次数到达17次或一位玩家的积分为0分则结束
        for pid, error_count in self.error_counts.items():
            if error_count >= 3:
                return True
        for pid, score in self.scores.items():
            if score >= 0:
                return True
        return False

    async def check_end_condition(self):
        if self.is_game_finished():
            self.state = "finished"
            
            # 判断胜负
            winner = None
            max_score = float('-inf')
            for pid, score in self.scores.items():
                if score > max_score:
                    max_score = score
                    winner = pid
            
            # 广播游戏结束和胜负结果
            await self.broadcast({
                "type": "game_finished",
                "winner": winner,
                "scores": self.scores,
                "errorCounts": self.error_counts
            })
            
            # 广播最新的卡牌数据
            await self.broadcast({
                "type": "cards_sync",
                "cards": self.cards
            })
            
            await self.broadcast_game_state()
            # 记录游戏结果
            await self.record_game_results(winner)
        else:
            # 继续游戏，轮次已在process_action里处理
            pass

    async def record_game_results(self, winner):
        """记录游戏结果到数据库"""
        print(f"🎮 开始记录游戏结果，房间ID: {self.room_id}")
        try:
            # 计算游戏统计信息
            total_rounds = sum(self.error_counts.values())  # 总错误次数
            total_flips = total_rounds * 2  # 每次错误翻两张牌
            total_matches = sum([score + 10 for score in self.scores.values()])  # 匹配次数（从初始分数恢复）
            total_actions = total_flips + total_matches  # 总行动次数
            
            print(f"游戏统计: 总错误次数 {total_rounds}, 总匹配次数 {total_matches}, 总行动次数 {total_actions}")
            print(f"玩家列表: {self.player_order}")
            print(f"玩家得分: {self.scores}")
            print(f"玩家错误次数: {self.error_counts}")
            print(f"获胜者: {winner}")
            
            # 为每个玩家记录游戏结果
            for player_id in self.player_order:
                player_score = self.scores.get(player_id, 0)
                player_error_count = self.error_counts.get(player_id, 0)
                is_winner = (player_id == winner)
                
                # 计算准确率：匹配次数 / (匹配次数 + 错误次数)
                player_matches = player_score + (10 if len(self.player_order) == 1 else 15)  # 从初始分数恢复
                player_total_actions = player_matches + player_error_count
                player_accuracy = (player_matches / player_total_actions * 100) if player_total_actions > 0 else 0
                
                print(f"🔄 处理玩家 {player_id} 的游戏记录: 得分 {player_score}, 错误次数 {player_error_count}, 准确率 {player_accuracy:.2f}%, 是否获胜 {is_winner}")
                
                # 直接与数据库交互记录游戏结果
                session_id = await self.create_game_record_direct(player_id, player_score, player_accuracy, player_error_count, is_winner)
                
                if session_id:
                    print(f"✅ 玩家 {player_id} 的游戏记录创建成功，会话ID: {session_id}")
                else:
                    print(f"❌ 玩家 {player_id} 的游戏记录创建失败")
            
            print(f"🎯 游戏结果记录完成，房间ID: {self.room_id}")
            
        except Exception as e:
            print(f"❌ 记录游戏结果失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    async def create_game_record_direct(self, player_id: str, score: int, accuracy: float, error_count: int, is_winner: bool):
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
            accuracy_decimal = round(accuracy, 2)
            print(f"准备数据: user_id={player_id}, game_type=memorial_banquet, score={score}, accuracy={accuracy_decimal}, duration={game_duration}")
            
            # 在异步环境中使用数据库会话
            db = None
            try:
                # 获取数据库会话
                db = next(get_db())
                print("数据库会话获取成功")
                
                # 创建游戏会话记录
                game_session = GameSession(
                    user_id=player_id,
                    game_type="memorial_banquet",
                    room_id=self.room_id,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    duration_seconds=game_duration,
                    score=score,
                    accuracy=accuracy_decimal,
                    rounds_played=error_count,
                    rounds_total=17,
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
                total_games = await self.update_player_stats_direct(player_id, "memorial_banquet", score, accuracy_decimal, game_duration)
                
                # 通知观察者游戏结束
                game_data = {
                    'user_id': player_id,
                    'is_winner': is_winner,
                    'total_games': total_games
                }
                await self.achievement_observer.on_game_finished(game_data)
                
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
        """更新玩家统计信息并返回总游戏数"""
        print(f"开始更新玩家统计: 用户ID {user_id}, 游戏类型 {game_type}, 最新得分 {score}, 最新准确率 {accuracy:.2f}%")
        total_games = 0
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
                
                total_games = db.query(func.count(GameSession.id)).filter(
                    GameSession.user_id == user_id,
                    GameSession.game_type == game_type
                ).scalar() or 0
                print(f"用户 {user_id} 的总游戏数: {total_games}")
                
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
        return total_games


    async def send_final_state(self, player_id: str):
        """发送终局状态数据给指定玩家"""
        if self.state != "finished":
            await self.broadcast_to_player(player_id, {
                "type": "error",
                "message": "游戏尚未结束，无法查看终局页面"
            })
            return
            
        # 构建终局数据：所有卡牌的数字信息
        final_state = {
            "type": "final_state",
            "cards": self.cards,  # 包含所有卡牌的数字信息
            "scores": self.scores,
            "error_counts": self.error_counts,
            "winner": self._get_winner()
        }
        
        print(f"📤 发送终局状态给玩家 {player_id}: {final_state}")
        await self.broadcast_to_player(player_id, final_state)
    
    def _get_winner(self):
        """获取获胜者"""
        if not self.scores:
            return None
        
        max_score = max(self.scores.values())
        winners = [pid for pid, score in self.scores.items() if score == max_score]
        
        if len(winners) == 1:
            return winners[0]
        else:
            return None  # 平局

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
            "score": self.scores[player_id],
            "errorCount": self.error_counts[player_id]
        })
        
        print(f"玩家 {player_id} 重连状态同步完成")


