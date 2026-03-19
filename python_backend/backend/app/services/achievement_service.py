from sqlalchemy.orm import Session
from ..models import Achievement, UserAchievement
from datetime import datetime

class AchievementService:
    """成就服务类，处理成就相关的业务逻辑"""
    
    @staticmethod
    def get_all_achievements(db: Session):
        """获取所有成就定义"""
        return db.query(Achievement).all()
    
    @staticmethod
    def get_achievements_by_type(db: Session, achievement_type: str = None, game_type: str = None):
        """根据成就类型获取成就列表"""
        query = db.query(Achievement)
        
        if achievement_type:
            query = query.filter(Achievement.achievement_type == achievement_type)
        
        if game_type:
            query = query.filter((Achievement.game_type == game_type) | (Achievement.game_type.is_(None)))
        
        return query.all()
    
    @staticmethod
    def get_user_achievements(db: Session, user_id: int, unlocked_only: bool = False):
        """获取用户的成就进度列表"""
        query = db.query(UserAchievement).filter(UserAchievement.user_id == user_id)
        
        if unlocked_only:
            query = query.filter(UserAchievement.is_unlocked == True)
        
        return query.all()
    
    @staticmethod
    def check_and_update_achievement(db: Session, user_id: int, condition_type: str, progress_value: int, game_type: str = None):
        """检查并更新用户成就进度
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            condition_type: 条件类型（如total_games, win_count等）
            progress_value: 当前进度值
            game_type: 游戏类型（可选）
            
        Returns:
            list: 新解锁的成就列表
        """
        # 获取相关的成就定义
        achievements = db.query(Achievement).filter(
            Achievement.condition_type == condition_type,
            (Achievement.game_type == game_type) | (Achievement.game_type.is_(None))
        ).all()
        
        newly_unlocked = []
        
        for achievement in achievements:
            # 获取或创建用户成就记录
            user_achievement = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            ).first()
            
            if not user_achievement:
                # 创建新的用户成就记录
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    current_progress=progress_value,
                    is_unlocked=progress_value >= achievement.target_value,
                    unlocked_at=datetime.utcnow() if progress_value >= achievement.target_value else None
                )
                db.add(user_achievement)
            else:
                # 更新现有记录
                was_unlocked = user_achievement.is_unlocked
                user_achievement.current_progress = progress_value
                
                # 检查是否解锁新成就
                if not was_unlocked and progress_value >= achievement.target_value:
                    user_achievement.is_unlocked = True
                    user_achievement.unlocked_at = datetime.utcnow()
                    newly_unlocked.append(achievement)
        
        return newly_unlocked
    
    @staticmethod
    def get_user_achievement_stats(db: Session, user_id: int):
        """获取用户的成就统计信息"""
        total_achievements = db.query(Achievement).count()
        unlocked_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.is_unlocked == True
        ).count()
        
        return {
            "total_achievements": total_achievements,
            "unlocked_achievements": unlocked_achievements,
            "unlock_percentage": (unlocked_achievements / total_achievements * 100) if total_achievements > 0 else 0
        }