from fastapi import HTTPException, status, Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from .database import SessionLocal, get_db
from .models.user import User
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# JWT配置
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-keep-it-safe-and-long-enough-for-production-use')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '120'))

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 直接使用bcrypt验证密码
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except (TypeError, ValueError):
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # 直接使用bcrypt生成哈希
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: Dict[str, Any]):
    """创建JWT令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str):
    """验证用户身份"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(
    token: str = None,  # 不再强制依赖oauth2_scheme，改为可选参数
    cookie_token: str = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    print("get_current_user被执行了")
    """获取当前用户 - 支持从Authorization头或cookie中获取token"""
    # 优先使用cookie中的token，如果没有则使用Authorization头中的token
    token_to_use = cookie_token if cookie_token else token
    
    # 记录token来源，便于调试
    token_source = "cookie" if cookie_token else "header" if token else "none"
    print(f"🔐 认证请求 - Token来源: {token_source}")
    print(f"🔐 Cookie token存在: {cookie_token is not None}")
    print(f"🔐 Header token存在: {token is not None}")
    
    if not token_to_use:
        print("🔐 错误: 未提供任何认证令牌 (Cookie和Header都为空)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的令牌或令牌已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"🔐 正在验证token，长度: {len(token_to_use) if token_to_use else 0}")
        payload = jwt.decode(token_to_use, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"🔐 Token解析成功，用户名: {username}")
        if username is None:
            print("🔐 错误: Token中没有用户名(sub)字段")
            raise credentials_exception
    except JWTError as e:
        print(f"🔐 JWT错误: {str(e)}")
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    print(f"🔐 根据用户名查询用户: {username}, 结果: {user is not None}")
    if user is None:
        print(f"🔐 错误: 找不到用户 {username}")
        raise credentials_exception
    print(f"🔐 用户认证成功: {username}")
    return user
