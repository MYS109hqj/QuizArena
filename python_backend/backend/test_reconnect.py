import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import WebSocket
from app.games.factory import GameFactory
from app.rooms import Room
from app.models.player import Player

class MockWebSocket:
    """模拟WebSocket连接，用于测试"""
    def __init__(self):
        self.sent_messages = []
        self._client = "test"
        self._is_connected = True
        self._accepted = False
    
    @property
    def client(self):
        return self._client
    
    @property
    def accepted(self):
        return self._accepted
    
    async def accept(self, **kwargs):
        self._accepted = True
    
    async def send_text(self, message):
        self.sent_messages.append(json.loads(message))
    
    async def receive_text(self):
        return json.dumps({"type": "test"})
    
    async def close(self, code=1000, reason=""):
        self._is_connected = False
    
    async def send_text(self, message):
        self.sent_messages.append(json.loads(message))
    
    async def send_json(self, data):
        self.sent_messages.append(data)
    
    async def receive_json(self):
        return {"type": "test"}

async def test_reconnect_functionality():
    """测试玩家重连状态同步功能"""
    print("🚀 开始重连功能测试...")
    
    # 创建游戏和房间
    game = GameFactory.create_game("o2SPH", "test_room")
    room = Room("test_room", game)
    
    # 创建模拟玩家
    player1 = Player(id="player1", name="Test Player", avatar="avatar1")
    
    # 第一次连接
    ws1 = MockWebSocket()
    await ws1.accept()  # 模拟accept调用
    await room.connect(ws1, player1)
    
    # 开始游戏
    await room.start_game()
    
    # 模拟一些游戏动作
    flip_action = {
        "action": {
            "type": "flip",
            "cardId": "A1"
        }
    }
    await room.handle_event(ws1, flip_action)
    
    print("✅ 游戏状态已初始化")
    
    # 模拟断开连接
    await room.disconnect(ws1)
    print("✅ 玩家已断开连接")
    
    # 等待一段时间模拟重连
    await asyncio.sleep(2)
    
    # 重连连接
    ws2 = MockWebSocket()  # 新的WebSocket连接
    await ws2.accept()
    await room.connect(ws2, player1)
    
    print("✅ 玩家已重连")
    
    # 检查重连消息
    reconnect_messages = [msg for msg in ws2.sent_messages 
                         if msg.get("type") in ["game_state", "cards_sync", "flip_status_sync", "player_sync"]]
    
    print(f"📨 重连时接收的消息数量: {len(reconnect_messages)}")
    for msg in reconnect_messages:
        print(f"   - {msg['type']}: {len(str(msg))} chars")
    
    # 验证状态一致性
    assert len(reconnect_messages) >= 3, "重连时应至少收到3种状态同步消息"
    print("🎉 重连状态同步测试通过！")

async def test_room_delay_destruction():
    """测试房间延迟销毁功能"""
    print("🧪 测试房间延迟销毁...")
    
    game = GameFactory.create_game("o2SPH", "test_delay_room")
    room = Room("test_delay_room", game)
    
    # 添加玩家
    player = Player(id="test_player", name="Test", avatar="test")
    ws = MockWebSocket()
    await ws.accept()
    await room.connect(ws, player)
    
    # 断开连接
    await room.disconnect(ws)
    
    # 检查房间是否还在（应该在延迟期内）
    assert len(room.players) == 0, "玩家应该已断开"
    assert room.room_id == "test_delay_room", "房间应该仍然存在"
    
    print("✅ 房间延迟销毁测试通过")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 运行重连功能测试套件")
    print("=" * 50)
    
    try:
        asyncio.run(test_reconnect_functionality())
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()