from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from .database import SessionLocal
from .auth import (
    get_password_hash, create_access_token, authenticate_user,
    get_user_by_username, get_user_by_email, oauth2_scheme,
    get_current_user
)
from .models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])

# Pydantic模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str
    total_games: int
    total_score: int
    win_count: int
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# 注册用户
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    db = SessionLocal()
    try:
        # 检查用户名是否已存在
        existing_user = get_user_by_username(db, user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被注册"
            )
        
        # 检查邮箱是否已存在
        existing_email = get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    finally:
        db.close()

# 用户登出
@router.post("/logout")
async def logout(response: Response):
    # 清除cookie
    response.delete_cookie(
        key="access_token",
        path="/"  # 与设置cookie时的path保持一致
    )
    return {"message": "登出成功"}

# 用户登录
@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, response: Response):
    print("🔐🔐🔐 登录端点被调用 🔐🔐🔐")
    print(f"🔐 登录请求参数: username={user_login.username}")
    
    db = SessionLocal()
    try:
        # 验证用户
        user = authenticate_user(db, user_login.username, user_login.password)
        if not user:
            print("🔐 登录失败: 用户名或密码错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成令牌
        access_token = create_access_token(data={"sub": user.username})
        print(f"🔐 登录成功，为用户 {user.username} 生成token")
        print(f"🔐 生成的JWT令牌: {access_token[:30]}...{access_token[-10:]}")
        print(f"🔐 令牌长度: {len(access_token)}")
        
        # 设置cookie - 不设置secure字段因为没有HTTPS证书
        # 设置httpOnly和SameSite以增强安全性
        cookie_settings = {
            "key": "access_token",
            "value": access_token,
            "httponly": True,
            "samesite": "lax",  # 修改为none，确保跨域情况下也能发送cookie
            "max_age": 120 * 60,
            "path": "/",
            "secure": False  # 开发环境中设置为False
        }
        
        print(f"🔐 设置cookie: {cookie_settings}")
        response.set_cookie(**cookie_settings)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    finally:
        db.close()

# 获取当前用户信息
@router.get("/profile", response_model=UserResponse)
async def read_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

# 验证令牌
@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    return {"valid": True, "username": current_user.username}

# 更新用户资料
class UserUpdate(BaseModel):
    avatar: str = None

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        # 从当前会话中获取用户对象
        db_user = db.query(User).filter(User.id == current_user.id).first()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户头像
        if user_update.avatar:
            db_user.avatar = user_update.avatar
            
        db.commit()
        db.refresh(db_user)
        return db_user
    finally:
        db.close()