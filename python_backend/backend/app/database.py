from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.user import Base as UserBase
from .models.game_record import Base as GameRecordBase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 数据库配置 - 使用MySQL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'quizarena')

# 创建MySQL数据库连接URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# 创建数据库引擎 - 去除check_same_thread参数，这是SQLite特有的
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 检查是否成功连接到MySQL数据库
try:
    connection = engine.connect()
    connection.close()
    print(f"✅ 成功连接到MySQL数据库: {MYSQL_DATABASE}@{MYSQL_HOST}:{MYSQL_PORT}")
except Exception as e:
    print(f"❌ 无法连接到MySQL数据库: {str(e)}")
    print("⚠️ 请确保MySQL服务已启动，且.env文件中的配置正确")

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
def create_tables():
    """创建所有数据库表"""
    try:
        # 创建用户相关表
        UserBase.metadata.create_all(bind=engine)
        print("用户表创建成功")
        
        # 创建游戏记录相关表
        GameRecordBase.metadata.create_all(bind=engine)
        print("游戏记录表创建成功")
        
        print("所有数据库表创建完成")
    except Exception as e:
        print(f"数据库表创建失败: {e}")

# 数据库依赖
def get_db():
    """获取数据库会话"""
    print("正在获取数据库会话：From database.py/get_db()")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()