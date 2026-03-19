from sqlalchemy.ext.declarative import declarative_base

# 创建一个共享的Base实例
Base = declarative_base()

# 导入模型（确保在Base定义后导入）
from .user import User
from .game_record import GameSession, GameRound, PlayerStats
from .achievement import Achievement
from .user_achievement import UserAchievement

__all__ = [
    "Base",
    "User",
    "GameSession",
    "GameRound",
    "PlayerStats",
    "Achievement",
    "UserAchievement"
]