from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class GameSession(Base):
    """游戏会话记录模型"""
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 暂时移除外键约束
    game_type = Column(String(50), nullable=False, index=True)  # 游戏类型
    room_id = Column(String(100), index=True)  # 房间ID
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)  # 游戏时长(秒)
    score = Column(Integer, default=0)  # 得分
    accuracy = Column(DECIMAL(5, 2), default=0.00)  # 准确率百分比
    rounds_played = Column(Integer, default=0)  # 完成的回合数
    rounds_total = Column(Integer, default=0)  # 总回合数
    status = Column(String(20), default="completed")  # 游戏状态
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式，确保时间戳包含UTC时区标识"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "game_type": self.game_type,
            "room_id": self.room_id,
            "start_time": self.start_time.isoformat() + 'Z' if self.start_time else None,
            "end_time": self.end_time.isoformat() + 'Z' if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "score": self.score,
            "accuracy": self.accuracy,
            "rounds_played": self.rounds_played,
            "rounds_total": self.rounds_total,
            "status": self.status,
            "created_at": self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class GameRound(Base):
    """游戏回合详细记录模型"""
    __tablename__ = "game_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)  # 暂时移除外键约束
    round_number = Column(Integer, nullable=False)  # 回合序号
    target_pattern = Column(String(255))  # 目标图案标识
    user_pattern = Column(String(255))  # 用户选择图案标识
    is_correct = Column(Boolean, default=False)  # 是否正确
    response_time_ms = Column(Integer, default=0)  # 响应时间(毫秒)
    round_score = Column(Integer, default=0)  # 回合得分
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式，确保时间戳包含UTC时区标识"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "round_number": self.round_number,
            "target_pattern": self.target_pattern,
            "user_pattern": self.user_pattern,
            "is_correct": self.is_correct,
            "response_time_ms": self.response_time_ms,
            "round_score": self.round_score,
            "created_at": self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class PlayerStats(Base):
    """玩家统计模型"""
    __tablename__ = "player_stats"
    
    user_id = Column(Integer, primary_key=True)  # 暂时移除外键约束
    game_type = Column(String(50), primary_key=True)
    total_games = Column(Integer, default=0)  # 总游戏次数
    total_score = Column(BigInteger, default=0)  # 总得分
    average_score = Column(DECIMAL(10, 2), default=0.00)  # 平均得分
    best_score = Column(Integer, default=0)  # 最高得分
    average_accuracy = Column(DECIMAL(5, 2), default=0.00)  # 平均准确率
    total_play_time_seconds = Column(BigInteger, default=0)  # 总游戏时长(秒)
    last_played = Column(DateTime, nullable=True)  # 最后游戏时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式，确保时间戳包含UTC时区标识"""
        return {
            "user_id": self.user_id,
            "game_type": self.game_type,
            "total_games": self.total_games,
            "total_score": self.total_score,
            "average_score": float(self.average_score) if self.average_score else 0.00,
            "best_score": self.best_score,
            "average_accuracy": float(self.average_accuracy) if self.average_accuracy else 0.00,
            "total_play_time_seconds": self.total_play_time_seconds,
            "last_played": self.last_played.isoformat() + 'Z' if self.last_played else None,
            "updated_at": self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }