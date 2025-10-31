from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    avatar = Column(Text, default='default_avatar.png')  # 在MySQL中对应LONGTEXT
    
    # 用户统计信息
    total_games = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "avatar": self.avatar,
            "total_games": self.total_games,
            "total_score": self.total_score,
            "win_count": self.win_count
        }