"""
测试Same Pattern Hunt游戏的观察者模式实现
用于验证成就系统是否正确响应游戏事件
"""
import unittest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

# 导入被测试的类
from .observers import AchievementObserver, SPHGameObserver

class TestSPHGameObserver(unittest.TestCase):
    
    def setUp(self):
        # 创建游戏实例的模拟对象
        self.mock_game = MagicMock()
        self.mock_game.broadcast_to_player = AsyncMock()
        
        # 创建观察者实例
        self.observer = SPHGameObserver(self.mock_game)
    
    @patch('app.database.get_db')
    async def test_on_game_finished_with_winner(self, mock_get_db):
        """测试游戏结束事件，玩家获胜的情况"""
        # 准备模拟数据
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        # 模拟成就对象
        mock_achievement = MagicMock()
        mock_achievement.id = 1
        mock_achievement.name = "游戏新手"
        mock_achievement.description = "完成1局游戏"
        mock_achievement.icon = "test.svg"
        
        # 模拟查询结果
        mock_db.query().filter().first.return_value = None
        mock_db.query().filter().scalar.return_value = 0
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.close = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.func.now.return_value = datetime.utcnow()
        
        # 模拟_check_game_count_achievements方法
        self.observer._check_game_count_achievements = MagicMock(return_value=[mock_achievement])
        self.observer._check_winner_achievements = MagicMock(return_value=[])
        
        # 准备游戏数据
        game_data = {
            'user_id': '123',
            'is_winner': True,
            'total_games': 1
        }
        
        # 执行测试
        await self.observer.on_game_finished(game_data)
        
        # 验证方法调用
        self.observer._check_game_count_achievements.assert_called_once_with(mock_db, '123', 1)
        self.observer._check_winner_achievements.assert_called_once_with(mock_db, '123')
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
        
        # 验证成就解锁通知
        self.mock_game.broadcast_to_player.assert_called_once_with(
            '123', 
            {
                "type": "achievement_unlocked",
                "achievement": {
                    "id": 1,
                    "name": "游戏新手",
                    "description": "完成1局游戏",
                    "icon": "test.svg"
                }
            }
        )
    
    async def test_on_achievement_unlocked(self):
        """测试成就解锁通知"""
        # 准备模拟数据
        mock_achievement = MagicMock()
        mock_achievement.id = 1
        mock_achievement.name = "游戏新手"
        mock_achievement.description = "完成1局游戏"
        mock_achievement.icon = "test.svg"
        
        # 执行测试
        await self.observer.on_achievement_unlocked(mock_achievement, '123')
        
        # 验证广播调用
        self.mock_game.broadcast_to_player.assert_called_once_with(
            '123', 
            {
                "type": "achievement_unlocked",
                "achievement": {
                    "id": 1,
                    "name": "游戏新手",
                    "description": "完成1局游戏",
                    "icon": "test.svg"
                }
            }
        )

class AsyncMock:  # 简单的异步Mock实现
    def __init__(self):
        self.calls = []
    
    async def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))

# 运行测试
if __name__ == '__main__':
    unittest.main()