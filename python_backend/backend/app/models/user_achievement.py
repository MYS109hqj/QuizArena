from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class UserAchievement(Base):
    """用户成就进度模型"""
    __tablename__ = "user_achievements"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    current_progress = Column(Integer, nullable=False, default=0)
    is_unlocked = Column(Boolean, nullable=False, default=False, index=True)
    unlocked_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp())
    
    # 暂时不定义关系，避免循环导入问题
    # 关系将在所有模型加载完成后定义
    
    def to_dict(self, include_achievement_detail=False, achievement_data=None):
        """转换为字典格式
        
        Args:
            include_achievement_detail: 是否包含成就详细信息
            achievement_data: 成就数据（从外部传入，避免使用关系）
            
        Returns:
            dict: 格式化后的字典数据
        """
        result = {
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "current_progress": self.current_progress,
            "is_unlocked": self.is_unlocked,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 如果需要包含成就详细信息，使用传入的数据
        if include_achievement_detail and achievement_data:
            result["achievement"] = achievement_data
        
        return result
    
    def to_frontend_dict(self, achievement_data=None):
        """转换为前端需要的格式，与WebSocket消息保持一致
        
        Args:
            achievement_data: 成就数据（从外部传入，避免使用关系）
            
        Returns:
            dict: 前端需要的成就格式
        """
        if achievement_data:
            return achievement_data
        # 如果没有传入成就数据，返回基本格式
        return {
            "id": self.achievement_id,
            "name": f"成就 {self.achievement_id}",
            "description": "成就描述",
            "icon": "default_icon.svg"
        }