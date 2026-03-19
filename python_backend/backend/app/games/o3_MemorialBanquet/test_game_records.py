import asyncio
import httpx
import json
from datetime import datetime
import os

"""
SPH游戏记录功能测试脚本
此脚本用于测试SamePatternHunt游戏的游戏记录功能是否正常工作
"""

# 配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "test_sph_user"
TEST_PASSWORD = "test123456"
TEST_EMAIL = "test_sph_user@example.com"

async def create_test_user():
    """创建测试用户"""
    print("创建测试用户...")
    async with httpx.AsyncClient() as client:
        # 先检查用户是否已存在
        try:
            login_response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
            )
            if login_response.status_code == 200:
                print(f"测试用户 {TEST_USERNAME} 已存在，跳过创建")
                return login_response.json()['access_token']
        except Exception as e:
            print(f"检查用户存在性失败: {e}")
            
        # 创建新用户
        try:
            register_response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": TEST_USERNAME,
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            if register_response.status_code == 201:
                print(f"测试用户 {TEST_USERNAME} 创建成功")
                
                # 登录获取令牌
                login_response = await client.post(
                    f"{BASE_URL}/auth/login",
                    json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
                )
                if login_response.status_code == 200:
                    return login_response.json()['access_token']
        except Exception as e:
            print(f"创建测试用户失败: {e}")
    return None

async def test_game_records():
    """测试游戏记录功能"""
    # 1. 获取用户令牌
    token = await create_test_user()
    if not token:
        print("无法获取用户令牌，测试失败")
        return False
    print(f"获取用户令牌成功: {token[:10]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 创建游戏会话
    print("创建游戏会话...")
    async with httpx.AsyncClient() as client:
        # 创建游戏会话
        session_response = await client.post(
            f"{BASE_URL}/game-records/sessions",
            json={
                "game_type": "same_pattern_hunt",
                "room_id": "test_room_123",
                "start_time": datetime.utcnow().isoformat()
            },
            headers=headers
        )
        
        if session_response.status_code != 200:
            print(f"创建游戏会话失败: {session_response.status_code}, {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data["id"]
        print(f"游戏会话创建成功，ID: {session_id}")
        
        # 3. 模拟游戏结束，更新游戏会话
        print("更新游戏会话（模拟游戏结束）...")
        update_response = await client.put(
            f"{BASE_URL}/game-records/sessions/{session_id}",
            json={
                "end_time": datetime.utcnow().isoformat(),
                "duration_seconds": 300,  # 5分钟
                "score": 18,  # 得分
                "accuracy": 90.0,  # 准确率
                "rounds_played": 48,  # 完成回合数
                "rounds_total": 48,  # 总回合数
                "status": "completed"
            },
            headers=headers
        )
        
        if update_response.status_code != 200:
            print(f"更新游戏会话失败: {update_response.status_code}, {update_response.text}")
            return False
        
        updated_session = update_response.json()
        print(f"游戏会话更新成功: {json.dumps(updated_session, indent=2)}")
        
        # 4. 验证游戏记录是否存在
        print("验证游戏记录是否存在...")
        records_response = await client.get(
            f"{BASE_URL}/game-records/sessions?game_type=same_pattern_hunt",
            headers=headers
        )
        
        if records_response.status_code != 200:
            print(f"获取游戏记录失败: {records_response.status_code}, {records_response.text}")
            return False
        
        records = records_response.json()
        found = any(record["id"] == session_id for record in records)
        
        if found:
            print(f"验证成功: 游戏记录 {session_id} 已保存")
        else:
            print(f"验证失败: 未找到游戏记录 {session_id}")
            print(f"当前游戏记录列表: {json.dumps(records, indent=2)}")
            return False
        
        # 5. 验证玩家统计信息是否更新
        print("验证玩家统计信息是否更新...")
        stats_response = await client.get(
            f"{BASE_URL}/game-records/stats",
            headers=headers
        )
        
        if stats_response.status_code != 200:
            print(f"获取玩家统计失败: {stats_response.status_code}, {stats_response.text}")
            return False
        
        stats = stats_response.json()
        sph_stats = next((s for s in stats if s["game_type"] == "same_pattern_hunt"), None)
        
        if sph_stats:
            print(f"玩家统计信息更新成功: {json.dumps(sph_stats, indent=2)}")
            # 基本验证统计数据
            if sph_stats["total_games"] >= 1 and sph_stats["total_score"] >= 18:
                print("统计数据验证通过")
            else:
                print("统计数据异常")
                return False
        else:
            print("未找到Same Pattern Hunt游戏的统计信息")
            return False
    
    print("\n🎉 游戏记录功能测试成功！")
    return True

if __name__ == "__main__":
    print("=== SPH游戏记录功能测试开始 ===")
    
    # 检查服务器是否运行
    try:
        async def check_server():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{BASE_URL}/auth/verify-token")
                    return True
            except:
                return False
        
        if not asyncio.run(check_server()):
            print(f"警告: 无法连接到服务器 {BASE_URL}。请确保后端服务器已启动。")
            print("测试将继续，但可能会失败...")
    except Exception as e:
        print(f"检查服务器状态时出错: {e}")
    
    # 运行测试
    success = asyncio.run(test_game_records())
    
    print("\n=== SPH游戏记录功能测试结束 ===")
    print(f"测试结果: {'通过' if success else '失败'}")