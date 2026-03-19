from sqlalchemy import Column, Integer, String, Text, DateTime, func
from datetime import datetime
from . import Base

class Achievement(Base):
    """成就定义模型"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    achievement_type = Column(String(50), nullable=False, index=True)  # basic, game_stat, game_process, game_end
    condition_type = Column(String(50), nullable=False, index=True)    # total_games, win_count, score_threshold, action_count, etc.
    target_value = Column(Integer, nullable=False, default=0)
    game_type = Column(String(50), nullable=True, index=True)  # NULL表示适用于所有游戏
    icon = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.current_timestamp())
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "achievement_type": self.achievement_type,
            "condition_type": self.condition_type,
            "target_value": self.target_value,
            "game_type": self.game_type,
            "icon": self.icon,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }