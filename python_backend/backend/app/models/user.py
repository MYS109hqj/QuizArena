from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
from . import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # 头像以 base64 字符串存储（cropperjs toDataURL），300x300 PNG 约 100-500KB，
    # MySQL 的 TEXT 仅 64KB 不够，必须用 LONGTEXT（4GB）
    avatar = Column(Text().with_variant(LONGTEXT, 'mysql'), default='default_avatar.png')
    
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