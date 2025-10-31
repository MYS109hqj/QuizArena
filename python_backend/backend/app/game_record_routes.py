from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from .database import get_db
from .auth import get_current_user
from .models.user import User
from .models.game_record import GameSession, GameRound, PlayerStats

router = APIRouter(prefix="/game-records", tags=["游戏记录"])

# Pydantic模型
class GameSessionCreate(BaseModel):
    game_type: str
    room_id: Optional[str] = None
    start_time: Optional[datetime] = None

class GameSessionUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    score: Optional[int] = None
    accuracy: Optional[float] = None
    rounds_played: Optional[int] = None
    rounds_total: Optional[int] = None
    status: Optional[str] = "completed"

class GameRoundCreate(BaseModel):
    session_id: int
    round_number: int
    target_pattern: Optional[str] = None
    user_pattern: Optional[str] = None
    is_correct: bool = False
    response_time_ms: int = 0
    round_score: int = 0

class GameSessionResponse(BaseModel):
    id: int
    user_id: int
    game_type: str
    room_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    score: int = 0
    accuracy: float = 0.0
    rounds_played: int = 0
    rounds_total: int = 0
    status: str = "completed"
    created_at: datetime
    
    class Config:
        from_attributes = True

class PlayerStatsResponse(BaseModel):
    user_id: int
    game_type: str
    total_games: int = 0
    total_score: int = 0
    average_score: float = 0.0
    best_score: int = 0
    average_accuracy: float = 0.0
    total_play_time_seconds: int = 0
    last_played: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 创建游戏会话
@router.post("/sessions", response_model=GameSessionResponse)
async def create_game_session(
    session_data: GameSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的游戏会话记录"""
    try:
        db_session = GameSession(
            user_id=current_user.id,
            game_type=session_data.game_type,
            room_id=session_data.room_id,
            start_time=session_data.start_time or datetime.utcnow()
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建游戏会话失败: {str(e)}"
        )

# 更新游戏会话
@router.put("/sessions/{session_id}", response_model=GameSessionResponse)
async def update_game_session(
    session_id: int,
    update_data: GameSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新游戏会话记录（游戏结束时调用）"""
    try:
        db_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == current_user.id
        ).first()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="游戏会话不存在"
            )
        
        # 更新字段
        if update_data.end_time:
            db_session.end_time = update_data.end_time
        if update_data.duration_seconds is not None:
            db_session.duration_seconds = update_data.duration_seconds
        if update_data.score is not None:
            db_session.score = update_data.score
        if update_data.accuracy is not None:
            db_session.accuracy = update_data.accuracy
        if update_data.rounds_played is not None:
            db_session.rounds_played = update_data.rounds_played
        if update_data.rounds_total is not None:
            db_session.rounds_total = update_data.rounds_total
        if update_data.status:
            db_session.status = update_data.status
            
        db.commit()
        db.refresh(db_session)
        
        # 更新玩家统计
        await update_player_stats(db_session.user_id, db_session.game_type, db)
        
        return db_session
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新游戏会话失败: {str(e)}"
        )

# 添加游戏回合记录
@router.post("/rounds", response_model=dict)
async def create_game_round(
    round_data: GameRoundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建游戏回合记录"""
    try:
        # 验证会话属于当前用户
        session = db.query(GameSession).filter(
            GameSession.id == round_data.session_id,
            GameSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="游戏会话不存在"
            )
        
        db_round = GameRound(
            session_id=round_data.session_id,
            round_number=round_data.round_number,
            target_pattern=round_data.target_pattern,
            user_pattern=round_data.user_pattern,
            is_correct=round_data.is_correct,
            response_time_ms=round_data.response_time_ms,
            round_score=round_data.round_score
        )
        db.add(db_round)
        db.commit()
        db.refresh(db_round)
        
        return {"message": "回合记录创建成功", "round_id": db_round.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建回合记录失败: {str(e)}"
        )

# 管理测试接口 - 查询所有游戏记录（用于调试）
@router.get("/admin/sessions", response_model=List[GameSessionResponse])
async def get_all_game_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取所有游戏记录（仅用于调试）"""
    print("🔍 管理接口: 查询所有游戏记录")
    try:
        # 查询所有游戏记录，不限制用户
        sessions = db.query(GameSession).order_by(
            GameSession.start_time.desc()
        ).offset(offset).limit(limit).all()
        
        print(f"📊 找到 {len(sessions)} 条游戏记录")
        # 输出每条记录的关键信息用于调试
        for session in sessions:
            print(f"  - 会话ID: {session.id}, 用户ID: {session.user_id}, 游戏类型: {session.game_type}, 得分: {session.score}")
            
        return sessions
    except Exception as e:
        print(f"❌ 查询所有游戏记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询游戏记录失败: {str(e)}"
        )

# 获取用户游戏记录
@router.get("/sessions", response_model=List[GameSessionResponse])
async def get_user_game_sessions(
    game_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的游戏记录"""
    try:
        query = db.query(GameSession).filter(GameSession.user_id == current_user.id)
        if game_type:
            query = query.filter(GameSession.game_type == game_type)
            
        sessions = query.order_by(GameSession.start_time.desc()).offset(offset).limit(limit).all()
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取游戏记录失败: {str(e)}"
        )

# 获取玩家统计信息
@router.get("/stats", response_model=List[PlayerStatsResponse])
async def get_player_stats(
    game_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取玩家的游戏统计信息"""
    print(f"/stats:获取用户 {current_user.username} id: {current_user.id} 的游戏统计信息")
    # 示例
    for attr in dir(current_user):
        # 过滤掉内置方法（以双下划线开头的）
        if not attr.startswith('__'):
            try:
                print(f"{attr}: {getattr(current_user, attr)}")
            except AttributeError:
                pass
    try:
        query = db.query(PlayerStats).filter(PlayerStats.user_id == current_user.id)
        
        if game_type:
            query = query.filter(PlayerStats.game_type == game_type)
            
        stats = query.all()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )

async def update_player_stats(user_id: int, game_type: str, db: Session):
    """更新玩家统计信息"""
    try:
        # 计算统计信息
        stats_query = db.query(
            GameSession.user_id,
            GameSession.game_type,
            func.count().label('total_games'),
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
        ).group_by(GameSession.user_id, GameSession.game_type)
        
        stats_result = stats_query.first()
        
        if stats_result:
            # 更新或插入统计记录
            existing_stats = db.query(PlayerStats).filter(
                PlayerStats.user_id == user_id,
                PlayerStats.game_type == game_type
            ).first()
            
            if existing_stats:
                existing_stats.total_games = stats_result.total_games or 0
                existing_stats.total_score = stats_result.total_score or 0
                existing_stats.average_score = float(stats_result.average_score or 0)
                existing_stats.best_score = stats_result.best_score or 0
                existing_stats.average_accuracy = float(stats_result.average_accuracy or 0)
                existing_stats.total_play_time_seconds = stats_result.total_play_time or 0
                existing_stats.last_played = stats_result.last_played
            else:
                new_stats = PlayerStats(
                    user_id=user_id,
                    game_type=game_type,
                    total_games=stats_result.total_games or 0,
                    total_score=stats_result.total_score or 0,
                    average_score=float(stats_result.average_score or 0),
                    best_score=stats_result.best_score or 0,
                    average_accuracy=float(stats_result.average_accuracy or 0),
                    total_play_time_seconds=stats_result.total_play_time or 0,
                    last_played=stats_result.last_played
                )
                db.add(new_stats)
            
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"更新玩家统计失败: {str(e)}")