import asyncio
import websockets
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def e2e_reconnect_test():
    """端到端重连测试"""
    print("🌐 开始端到端重连测试...")
    print("⚠️  注意：请确保后端服务器正在运行 (uvicorn app.main:app --reload)")
    print("=" * 60)
    
    test_passed = False
    websocket1 = None
    websocket2 = None
    
    try:
        # 测试配置
        test_room = f"test_room_{int(time.time())}"
        player_info = {
            "id": f"test_player_{int(time.time())}",
            "name": "E2E Test Player",
            "avatar": "test_avatar"
        }
        
        print(f"📋 测试房间: {test_room}")
        print(f"👤 测试玩家: {player_info['name']}")
        
        # 第一次连接
        print("1. 🔗 建立第一次连接...")
        uri = f"ws://localhost:8000/ws/{test_room}/o2SPH"
        websocket1 = await websockets.connect(uri)
        
        # 发送玩家信息
        await websocket1.send(json.dumps(player_info))
        print("   ✅ 玩家信息已发送")
        
        # 接收初始响应
        try:
            response = await asyncio.wait_for(websocket1.recv(), timeout=5.0)
            message = json.loads(response)
            print(f"   📨 收到响应: {message.get('type', 'unknown')}")
        except asyncio.TimeoutError:
            print("   ⚠️  未收到初始响应（可能正常）")
        
        # 等待游戏初始化
        await asyncio.sleep(2)
        
        # 关闭第一次连接
        print("2. 🔌 断开第一次连接...")
        await websocket1.close()
        websocket1 = None
        print("   ✅ 连接已断开")
        
        # 等待重连窗口
        print("3. ⏳ 等待重连窗口（2秒）...")
        await asyncio.sleep(2)
        
        # 重连连接
        print("4. 🔄 尝试重连...")
        websocket2 = await websockets.connect(uri)
        
        # 再次发送玩家信息（重连）
        await websocket2.send(json.dumps(player_info))
        print("   ✅ 重连玩家信息已发送")
        
        # 接收重连响应
        reconnect_messages = []
        start_time = time.time()
        
        print("5. 📡 接收重连状态同步消息...")
        try:
            while time.time() - start_time < 10:  # 10秒超时
                response = await asyncio.wait_for(websocket2.recv(), timeout=3.0)
                message = json.loads(response)
                reconnect_messages.append(message)
                print(f"   📨 收到: {message.get('type', 'unknown')}")
                
                # 如果收到游戏状态消息，认为重连成功
                if message.get('type') in ['game_state', 'room_state']:
                    break
                    
        except asyncio.TimeoutError:
            print("   ⏰ 接收消息超时")
        
        # 验证测试结果
        print("6. ✅ 验证测试结果...")
        print(f"   重连消息数量: {len(reconnect_messages)}")
        
        if len(reconnect_messages) > 0:
            print("   🎉 重连成功！收到状态同步消息")
            test_passed = True
        else:
            print("   ❌ 重连失败：未收到任何消息")
        
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"   ❌ 连接被关闭: {e}")
    except websockets.exceptions.WebSocketException as e:
        print(f"   ❌ WebSocket错误: {e}")
    except Exception as e:
        print(f"   ❌  unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理连接
        if websocket1:
            await websocket1.close()
        if websocket2:
            await websocket2.close()
        
        print("=" * 60)
        if test_passed:
            print("🎯 端到端测试: 通过!")
        else:
            print("💥 端到端测试: 失败!")
        print("=" * 60)
        
    return test_passed

async def test_server_availability():
    """测试服务器是否可用"""
    print("🔍 检查服务器可用性...")
    try:
        # 尝试连接服务器
        uri = "ws://localhost:8000/ws/health_check/o2SPH"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({
                "id": "health_check",
                "name": "Health Check",
                "avatar": ""
            }))
            print("   ✅ 服务器连接成功")
            return True
    except Exception as e:
        print(f"   ❌ 服务器连接失败: {e}")
        print("   💡 请运行: uvicorn app.main:app --reload")
        return False

if __name__ == "__main__":
    print("🚀 WebSocket重连功能端到端测试")
    print("=" * 60)
    
    # 首先检查服务器是否可用
    server_available = asyncio.run(test_server_availability())
    
    if server_available:
        # 运行端到端测试
        result = asyncio.run(e2e_reconnect_test())
        sys.exit(0 if result else 1)
    else:
        print("❌ 无法继续测试：服务器不可用")
        sys.exit(1)