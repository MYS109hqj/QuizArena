#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移工具
用于按顺序执行migrations目录下的SQL迁移脚本
"""

import os
import re
import sys
import mysql.connector
from mysql.connector import Error
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': '',
    'user': '',
    'password': '',
    'database': ''
}

def load_env_config():
    """从.env文件加载数据库配置"""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    logger.info(f"尝试从.env文件加载配置: {env_file}")
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 跳过注释和空行
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith('#'):
                        continue
                    
                    if '=' in stripped_line:
                        key, value = stripped_line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 处理引号和注释
                        if value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # 移除行尾注释
                        if '#' in value:
                            value = value.split('#')[0].strip()
                    
                    # 支持DB_和MYSQL_前缀的环境变量
                    if key in ['DB_HOST', 'MYSQL_HOST']:
                        DB_CONFIG['host'] = value
                    elif key in ['DB_USER', 'MYSQL_USER']:
                        DB_CONFIG['user'] = value
                    elif key in ['DB_PASSWORD', 'MYSQL_PASSWORD']:
                        DB_CONFIG['password'] = value
                    elif key in ['DB_NAME', 'MYSQL_DATABASE']:
                        DB_CONFIG['database'] = value
            
            # 脱敏密码后的配置信息
            safe_config = DB_CONFIG.copy()
            if 'password' in safe_config and safe_config['password']:
                safe_config['password'] = '******'
            logger.info(f"已从.env文件加载数据库配置: {safe_config}")
        except Exception as e:
            logger.warning(f"加载.env文件失败: {e}")
    else:
        logger.warning(f".env文件不存在: {env_file}")

def get_migration_files():
    """获取按版本号排序的迁移脚本文件"""
    migrations_dir = os.path.dirname(__file__)
    
    # 匹配Vxxx__开头的SQL文件
    pattern = r'^V(\d+)__.*\.sql$'
    migration_files = []
    
    for file in os.listdir(migrations_dir):
        match = re.match(pattern, file)
        if match:
            version = int(match.group(1))
            migration_files.append((version, file))
    
    # 按版本号排序
    migration_files.sort(key=lambda x: x[0])
    return [file for _, file in migration_files]

def execute_migration_script(cursor, script_path):
    """执行单个SQL迁移脚本"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割SQL语句（处理分号，但忽略注释和字符串中的分号）
        statements = []
        current_statement = ''
        in_string = None
        in_comment_line = False
        in_comment_block = False
        
        for i, char in enumerate(sql_script):
            if in_comment_block:
                if char == '*' and i < len(sql_script) - 1 and sql_script[i+1] == '/':
                    in_comment_block = False
                continue
            
            if in_comment_line:
                if char == '\n':
                    in_comment_line = False
                continue
            
            if in_string:
                current_statement += char
                if char == in_string and (i == 0 or sql_script[i-1] != '\\'):
                    in_string = None
                continue
            
            if char == '\'':
                current_statement += char
                in_string = char
            elif char == '"':
                current_statement += char
                in_string = char
            elif char == '-' and i < len(sql_script) - 1 and sql_script[i+1] == '-':
                in_comment_line = True
                current_statement += char
            elif char == '/' and i < len(sql_script) - 1 and sql_script[i+1] == '*':
                in_comment_block = True
                current_statement += char
            elif char == ';':
                current_statement += char
                statements.append(current_statement.strip())
                current_statement = ''
            else:
                current_statement += char
        
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # 执行每个语句
        for stmt in statements:
            cursor.execute(stmt)
        
        logger.info(f"成功执行迁移脚本: {os.path.basename(script_path)}")
        return True
    except Exception as e:
        logger.error(f"执行迁移脚本失败 {os.path.basename(script_path)}: {e}")
        return False

def create_migrations_table(cursor):
    """创建迁移历史表"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(20) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_version (version)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        logger.info("迁移历史表已创建或已存在")
    except Exception as e:
        logger.error(f"创建迁移历史表失败: {e}")

def get_applied_migrations(cursor):
    """获取已应用的迁移版本"""
    applied = set()
    try:
        cursor.execute("SELECT version FROM migration_history")
        for row in cursor:
            applied.add(row[0])
    except Exception as e:
        logger.error(f"获取已应用迁移失败: {e}")
    return applied

def record_migration(cursor, version, filename):
    """记录迁移应用历史"""
    try:
        cursor.execute(
            "INSERT INTO migration_history (version, filename) VALUES (%s, %s)",
            (version, filename)
        )
        logger.info(f"已记录迁移版本: {version}")
    except Exception as e:
        logger.error(f"记录迁移失败: {e}")

def main():
    """主函数"""
    # 加载环境配置
    load_env_config()
    
    # 获取迁移文件
    migration_files = get_migration_files()
    if not migration_files:
        logger.info("没有找到迁移脚本")
        return
    
    logger.info(f"找到 {len(migration_files)} 个迁移脚本")
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建迁移历史表
        create_migrations_table(cursor)
        conn.commit()
        
        # 获取已应用的迁移
        applied_migrations = get_applied_migrations(cursor)
        
        # 执行未应用的迁移
        migrations_dir = os.path.dirname(__file__)
        applied_count = 0
        
        for filename in migration_files:
            # 提取版本号
            match = re.match(r'^V(\d+)__', filename)
            if match:
                version = match.group(1)
                
                if version in applied_migrations:
                    logger.info(f"迁移脚本已应用: {filename}")
                    continue
                
                logger.info(f"开始应用迁移: {filename}")
                script_path = os.path.join(migrations_dir, filename)
                
                if execute_migration_script(cursor, script_path):
                    # 记录迁移
                    record_migration(cursor, version, filename)
                    conn.commit()
                    applied_count += 1
                else:
                    logger.error("迁移失败，已停止执行")
                    conn.rollback()
                    break
        
        if applied_count > 0:
            logger.info(f"成功应用 {applied_count} 个迁移脚本")
        else:
            logger.info("没有需要应用的迁移脚本")
            
    except Error as e:
        logger.error(f"数据库错误: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()