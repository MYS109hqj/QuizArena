from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

from .database import get_db
from .auth import get_current_user
from .models.user import User
from .models.achievement import Achievement
from .models.user_achievement import UserAchievement
from .services.achievement_service import AchievementService
from .utils.achievement_utils import calculate_progress_percentage

router = APIRouter(prefix="/achievements", tags=["成就"])

# Pydantic模型
class AchievementResponse(BaseModel):
    """成就响应模型"""
    id: int
    name: str
    description: str
    achievement_type: str
    condition_type: str
    target_value: int
    game_type: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserAchievementResponse(BaseModel):
    """用户成就响应模型"""
    achievement: AchievementResponse
    current_progress: int
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    progress_percentage: float

class UserAchievementSummary(BaseModel):
    """用户成就摘要模型"""
    total_achievements: int
    unlocked_achievements: int
    completion_rate: float
    recent_unlocked: List[UserAchievementResponse]

# 获取当前用户的成就摘要
@router.get("/summary", response_model=UserAchievementSummary)
async def get_user_achievement_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的成就摘要信息，包括总成就数、已解锁成就数、完成率和最近解锁的成就
    """
    try:
        # 获取总成就数
        total_achievements = db.query(Achievement).count()
        
        # 获取已解锁成就数
        unlocked_achievements = db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == current_user.id,
                UserAchievement.is_unlocked == True
            )
        ).count()
        
        # 计算完成率
        completion_rate = (unlocked_achievements / total_achievements * 100) if total_achievements > 0 else 0
        
        # 获取最近解锁的成就（最多5个）
        recent_user_achievements = db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == current_user.id,
                UserAchievement.is_unlocked == True
            )
        ).order_by(UserAchievement.unlocked_at.desc()).limit(5).all()
        
        # 构建最近解锁的成就响应
        recent_unlocked = []
        for ua in recent_user_achievements:
            achievement = db.query(Achievement).filter(Achievement.id == ua.achievement_id).first()
            if achievement:
                progress_percentage = calculate_progress_percentage(ua.current_progress, achievement.target_value)
                recent_unlocked.append(UserAchievementResponse(
                    achievement=achievement,
                    current_progress=ua.current_progress,
                    is_unlocked=ua.is_unlocked,
                    unlocked_at=ua.unlocked_at,
                    progress_percentage=progress_percentage
                ))
        
        return UserAchievementSummary(
            total_achievements=total_achievements,
            unlocked_achievements=unlocked_achievements,
            completion_rate=completion_rate,
            recent_unlocked=recent_unlocked
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取成就摘要失败: {str(e)}"
        )

# 获取当前用户已解锁的成就
@router.get("/unlocked", response_model=List[UserAchievementResponse])
async def get_user_unlocked_achievements(
    game_type: Optional[str] = Query(None, description="游戏类型，为空表示所有游戏"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户已解锁的所有成就
    
    - **game_type**: 可选的游戏类型筛选
    """
    try:
        # 构建查询
        query = db.query(UserAchievement).join(Achievement).filter(
            and_(
                UserAchievement.user_id == current_user.id,
                UserAchievement.is_unlocked == True
            )
        )
        
        # 如果指定了游戏类型，则添加筛选条件
        if game_type:
            query = query.filter(Achievement.game_type == game_type)
        
        # 按解锁时间倒序排列
        user_achievements = query.order_by(UserAchievement.unlocked_at.desc()).all()
        
        # 构建响应
        result = []
        for ua in user_achievements:
            achievement = db.query(Achievement).filter(Achievement.id == ua.achievement_id).first()
            if achievement:
                progress_percentage = calculate_progress_percentage(ua.current_progress, achievement.target_value)
                result.append(UserAchievementResponse(
                    achievement=achievement,
                    current_progress=ua.current_progress,
                    is_unlocked=ua.is_unlocked,
                    unlocked_at=ua.unlocked_at,
                    progress_percentage=progress_percentage
                ))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取已解锁成就失败: {str(e)}"
        )

# 获取当前用户的所有成就（包括未解锁的，显示进度）
@router.get("/all", response_model=List[UserAchievementResponse])
async def get_user_all_achievements(
    game_type: Optional[str] = Query(None, description="游戏类型，为空表示所有游戏"),
    achievement_type: Optional[str] = Query(None, description="成就类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有成就，包括已解锁和未解锁的，显示每个成就的进度
    
    - **game_type**: 可选的游戏类型筛选
    - **achievement_type**: 可选的成就类型筛选
    """
    try:
        # 构建成就查询
        achievement_query = db.query(Achievement)
        
        # 如果指定了游戏类型，则添加筛选条件
        if game_type:
            achievement_query = achievement_query.filter(Achievement.game_type == game_type)
        
        # 如果指定了成就类型，则添加筛选条件
        if achievement_type:
            achievement_query = achievement_query.filter(Achievement.achievement_type == achievement_type)
        
        # 获取所有符合条件的成就
        achievements = achievement_query.all()
        
        # 构建响应
        result = []
        for achievement in achievements:
            # 查询用户的该成就进度
            user_achievement = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_id == current_user.id,
                    UserAchievement.achievement_id == achievement.id
                )
            ).first()
            
            # 如果用户没有该成就的记录，则创建一个默认记录
            if not user_achievement:
                progress = 0
                is_unlocked = False
                unlocked_at = None
            else:
                progress = user_achievement.current_progress
                is_unlocked = user_achievement.is_unlocked
                unlocked_at = user_achievement.unlocked_at
            
            progress_percentage = calculate_progress_percentage(progress, achievement.target_value)
            
            result.append(UserAchievementResponse(
                achievement=achievement,
                current_progress=progress,
                is_unlocked=is_unlocked,
                unlocked_at=unlocked_at,
                progress_percentage=progress_percentage
            ))
        
        # 按已解锁状态和进度百分比排序（已解锁的在前，未解锁的按进度倒序）
        result.sort(key=lambda x: (0 if x.is_unlocked else 1, -x.progress_percentage))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取成就列表失败: {str(e)}"
        )

# 获取成就详情
@router.get("/{achievement_id}", response_model=UserAchievementResponse)
async def get_achievement_detail(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定成就的详细信息和当前用户的进度
    """
    try:
        # 查询成就
        achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
        if not achievement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成就不存在"
            )
        
        # 查询用户的该成就进度
        user_achievement = db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == current_user.id,
                UserAchievement.achievement_id == achievement_id
            )
        ).first()
        
        # 如果用户没有该成就的记录，则创建一个默认记录
        if not user_achievement:
            progress = 0
            is_unlocked = False
            unlocked_at = None
        else:
            progress = user_achievement.current_progress
            is_unlocked = user_achievement.is_unlocked
            unlocked_at = user_achievement.unlocked_at
        
        progress_percentage = calculate_progress_percentage(progress, achievement.target_value)
        
        return UserAchievementResponse(
            achievement=achievement,
            current_progress=progress,
            is_unlocked=is_unlocked,
            unlocked_at=unlocked_at,
            progress_percentage=progress_percentage
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取成就详情失败: {str(e)}"
        )