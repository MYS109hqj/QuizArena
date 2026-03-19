from abc import ABC, abstractmethod
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement

# 观察者接口
class AchievementObserver(ABC):
    @abstractmethod
    async def on_game_finished(self, game_data: Dict[str, Any]):
        """当游戏结束时调用"""
        pass
    
    @abstractmethod
    async def on_achievement_unlocked(self, achievement: Achievement, user_id: str):
        """当成就解锁时调用"""
        pass

# SamePatternHunt游戏的具体观察者
class SPHGameObserver(AchievementObserver):
    def __init__(self, game_instance):
        self.game_instance = game_instance
    
    async def on_game_finished(self, game_data: Dict[str, Any]):
        """处理游戏结束事件，检查并更新成就"""
        user_id = game_data.get('user_id')
        is_winner = game_data.get('is_winner', False)
        total_games = game_data.get('total_games', 0)
        
        if not user_id:
            return
        
        # 获取数据库会话
        db = next(get_db())
        try:
            # 检查游戏次数成就
            game_count_achievements = self._check_game_count_achievements(db, user_id, total_games)
            
            # 检查胜利相关成就
            winner_achievements = []
            if is_winner:
                winner_achievements = self._check_winner_achievements(db, user_id)
            
            # 合并所有新解锁的成就
            all_new_achievements = game_count_achievements + winner_achievements
            
            # 通知成就解锁
            for achievement in all_new_achievements:
                await self.on_achievement_unlocked(achievement, user_id)
            
            db.commit()
            
        except Exception as e:
            print(f"❌ 检查成就时出错: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _check_game_count_achievements(self, db: Session, user_id: str, total_games: int) -> List[Achievement]:
        """检查游戏次数相关成就"""
        unlocked_achievements = []
        
        # 定义游戏次数成就配置
        game_count_thresholds = {
            1: "游戏新手",
            5: "游戏爱好者",
            10: "游戏达人",
            50: "游戏大师"
        }
        
        for threshold, achievement_name in game_count_thresholds.items():
            if total_games >= threshold:
                # 查找或创建成就
                achievement = db.query(Achievement).filter(
                    Achievement.name == achievement_name,
                    Achievement.game_type == "same_pattern_hunt"
                ).first()
                
                if not achievement:
                    achievement = Achievement(
                        name=achievement_name,
                        description=f"完成{threshold}局Same Pattern Hunt游戏",
                        icon=f"achievement_{threshold}.svg",
                        game_type="same_pattern_hunt",
                        achievement_type="game_count",
                        condition_type="total_games",
                        target_value=threshold
                    )
                    db.add(achievement)
                    db.flush()  # 获取ID但不提交事务
                
                # 检查用户是否已解锁该成就
                user_achievement = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not user_achievement:
                    try:
                        # 解锁新成就 - 尝试创建记录，捕获可能的外键错误
                        from datetime import datetime
                        user_achievement = UserAchievement(
                            user_id=user_id,
                            achievement_id=achievement.id,
                            current_progress=total_games,
                            is_unlocked=True,
                            unlocked_at=datetime.utcnow()  # 使用UTC时间，与游戏记录时间保持一致
                        )
                        db.add(user_achievement)
                        unlocked_achievements.append(achievement)
                    except Exception as inner_e:
                        print(f"⚠️ 创建用户成就记录时出错: {str(inner_e)}")
                        # 继续执行，不中断主流程
        
        return unlocked_achievements
    
    def _check_winner_achievements(self, db: Session, user_id: str) -> List[Achievement]:
        """检查胜利相关成就"""
        unlocked_achievements = []
        
        # 查询用户获胜次数（胜利定义为score > 0）
        from app.models.game_record import GameSession
        win_count = db.query(func.count(GameSession.id)).filter(
            GameSession.user_id == user_id,
            GameSession.game_type == "same_pattern_hunt",
            GameSession.status == "completed",
            GameSession.score > 0  # 添加胜利条件筛选
        ).scalar() or 0
        
        # 定义胜利次数成就配置
        win_count_thresholds = {
            1: "初次胜利",
            3: "常胜将军",
            10: "无敌战神"
        }
        
        for threshold, achievement_name in win_count_thresholds.items():
            if win_count >= threshold:
                # 查找或创建成就
                achievement = db.query(Achievement).filter(
                    Achievement.name == achievement_name,
                    Achievement.game_type == "same_pattern_hunt"
                ).first()
                
                if not achievement:
                    achievement = Achievement(
                        name=achievement_name,
                        description=f"获得{threshold}次Same Pattern Hunt游戏胜利",
                        icon=f"winner_{threshold}.svg",
                        game_type="same_pattern_hunt",
                        achievement_type="victory",
                        condition_type="win_count",
                        target_value=threshold
                    )
                    db.add(achievement)
                    db.flush()
                
                # 检查用户是否已解锁该成就
                user_achievement = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not user_achievement:
                    try:
                        # 解锁新成就 - 尝试创建记录，捕获可能的外键错误
                        from datetime import datetime
                        user_achievement = UserAchievement(
                            user_id=user_id,
                            achievement_id=achievement.id,
                            current_progress=win_count,
                            is_unlocked=True,
                            unlocked_at=datetime.utcnow()  # 使用UTC时间，与游戏记录时间保持一致
                        )
                        db.add(user_achievement)
                        unlocked_achievements.append(achievement)
                    except Exception as inner_e:
                        print(f"⚠️ 创建用户成就记录时出错: {str(inner_e)}")
                        # 继续执行，不中断主流程
        
        return unlocked_achievements
    
    async def on_achievement_unlocked(self, achievement: Achievement, user_id: str):
        """通知玩家成就解锁"""
        print(f"🎉 用户 {user_id} 解锁了成就: {achievement.name}")
        
        # 构建成就数据字典，直接使用Achievement对象的属性
        achievement_data = {
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "icon": achievement.icon
        }
        
        # 通过游戏实例向玩家发送成就解锁通知
        if self.game_instance:
            await self.game_instance.broadcast_to_player(user_id, {
                "type": "achievement_unlocked",
                "achievement": achievement_data
            })

# 导入已移至文件顶部