"""游戏记录服务 - 提供游戏记录相关的业务逻辑"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from .models.game_record import GameSession, GameRound, PlayerStats
from .models.user import User

class GameRecordService:
    """游戏记录服务类"""
    
    @staticmethod
    def create_game_session(
        db: Session, 
        user_id: int, 
        game_type: str, 
        room_id: Optional[str] = None
    ) -> GameSession:
        """创建新的游戏会话"""
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            room_id=room_id,
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def update_game_session(
        db: Session,
        session_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[GameSession]:
        """更新游戏会话信息"""
        session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user_id
        ).first()
        
        if not session:
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        
        session.end_time = session.end_time or datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        # 更新玩家统计
        GameRecordService.update_player_stats(db, user_id, session.game_type)
        
        return session
    
    @staticmethod
    def create_game_round(
        db: Session,
        session_id: int,
        round_number: int,
        target_pattern: Optional[str] = None,
        user_pattern: Optional[str] = None,
        is_correct: bool = False,
        response_time_ms: int = 0,
        round_score: int = 0
    ) -> GameRound:
        """创建游戏回合记录"""
        round_record = GameRound(
            session_id=session_id,
            round_number=round_number,
            target_pattern=target_pattern,
            user_pattern=user_pattern,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            round_score=round_score
        )
        db.add(round_record)
        db.commit()
        db.refresh(round_record)
        return round_record
    
    @staticmethod
    def update_player_stats(db: Session, user_id: int, game_type: str):
        """更新玩家统计信息"""
        try:
            # 查询游戏统计信息
            stats = db.query(
                func.count(GameSession.id).label('total_games'),
                func.sum(GameSession.score).label('total_score'),
                func.avg(GameSession.score).label('average_score'),
                func.max(GameSession.score).label('best_score'),
                func.avg(GameSession.accuracy).label('average_accuracy'),
                func.sum(GameSession.duration_seconds).label('total_play_time'),
                func.max(GameSession.end_time).label('last_played')
            ).filter(
                GameSession.user_id == user_id,
                GameSession.game_type == game_type,
                GameSession.status == 'completed'
            ).first()
            
            if not stats or not stats.total_games:
                return
            
            # 查找或创建玩家统计记录
            player_stats = db.query(PlayerStats).filter(
                PlayerStats.user_id == user_id,
                PlayerStats.game_type == game_type
            ).first()
            
            if player_stats:
                # 更新现有记录
                player_stats.total_games = stats.total_games
                player_stats.total_score = stats.total_score or 0
                player_stats.average_score = float(stats.average_score or 0)
                player_stats.best_score = stats.best_score or 0
                player_stats.average_accuracy = float(stats.average_accuracy or 0)
                player_stats.total_play_time_seconds = stats.total_play_time or 0
                player_stats.last_played = stats.last_played
            else:
                # 创建新记录
                player_stats = PlayerStats(
                    user_id=user_id,
                    game_type=game_type,
                    total_games=stats.total_games,
                    total_score=stats.total_score or 0,
                    average_score=float(stats.average_score or 0),
                    best_score=stats.best_score or 0,
                    average_accuracy=float(stats.average_accuracy or 0),
                    total_play_time_seconds=stats.total_play_time or 0,
                    last_played=stats.last_played
                )
                db.add(player_stats)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"更新玩家统计失败: {str(e)}")
    
    @staticmethod
    def get_user_game_sessions(
        db: Session,
        user_id: int,
        game_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> list:
        """获取用户的游戏会话记录"""
        query = db.query(GameSession).filter(GameSession.user_id == user_id)
        
        if game_type:
            query = query.filter(GameSession.game_type == game_type)
            
        return query.order_by(GameSession.start_time.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_player_stats(
        db: Session,
        user_id: int,
        game_type: Optional[str] = None
    ) -> list:
        """获取玩家统计信息"""
        query = db.query(PlayerStats).filter(PlayerStats.user_id == user_id)
        
        if game_type:
            query = query.filter(PlayerStats.game_type == game_type)
            
        return query.all()
    
    @staticmethod
    def get_session_rounds(db: Session, session_id: int) -> list:
        """获取游戏会话的回合记录"""
        return db.query(GameRound).filter(GameRound.session_id == session_id).order_by(GameRound.round_number).all()