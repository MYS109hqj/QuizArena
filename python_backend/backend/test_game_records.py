import unittest
import asyncio
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.games.o2_SamePatternHunt.game import o2SPHGame
from app.database import get_db, create_tables, engine
from app.models.game_record import GameSession, PlayerStats
from sqlalchemy.orm import Session

class TestGameRecordStorage(unittest.TestCase):
    """测试游戏记录存储功能"""
    
    @classmethod
    def setUpClass(cls):
        """在所有测试前准备数据库"""
        # 创建数据库表（如果不存在）
        create_tables()
        print("✅ 数据库表准备完成")
    
    def setUp(self):
        """每个测试前清空相关表的数据"""
        db = next(get_db())
        try:
            # 清空测试数据
            db.query(GameSession).delete()
            db.query(PlayerStats).delete()
            db.commit()
            print("✅ 测试数据已清空")
        except Exception as e:
            db.rollback()
            print(f"❌ 清空测试数据失败: {e}")
        finally:
            db.close()
    
    async def test_record_game_results(self):
        """测试游戏结果记录功能"""
        # 创建游戏实例
        game = o2SPHGame(room_id="test_room_123")
        game.start_time = datetime.utcnow()
        
        # 模拟游戏数据
        game.player_order = ["test_user_1", "test_user_2"]
        game.scores = {"test_user_1": 15, "test_user_2": 12}
        game.player_target_index = {"test_user_1": 40, "test_user_2": 35}
        
        # 使用mock替代get_user_id_from_player_id方法，避免创建真实用户
        with patch.object(game, 'get_user_id_from_player_id', side_effect=lambda pid: 101 if pid == "test_user_1" else 102):
            # 执行记录游戏结果
            await game.record_game_results()
            
            # 验证数据是否正确写入数据库
            db = next(get_db())
            try:
                # 检查游戏会话记录
                sessions = db.query(GameSession).all()
                self.assertEqual(len(sessions), 2, "应该创建两条游戏会话记录")
                
                # 验证第一条记录
                session1 = db.query(GameSession).filter(GameSession.user_id == 101).first()
                self.assertIsNotNone(session1, "找不到用户101的游戏会话记录")
                self.assertEqual(session1.score, 15, "分数应该是15")
                self.assertEqual(session1.rounds_played, 40, "已玩回合数应该是40")
                self.assertEqual(session1.rounds_total, 48, "总回合数应该是48")
                self.assertEqual(session1.game_type, "same_pattern_hunt", "游戏类型应该是same_pattern_hunt")
                
                # 验证第二条记录
                session2 = db.query(GameSession).filter(GameSession.user_id == 102).first()
                self.assertIsNotNone(session2, "找不到用户102的游戏会话记录")
                self.assertEqual(session2.score, 12, "分数应该是12")
                
                # 检查玩家统计信息
                stats = db.query(PlayerStats).all()
                self.assertEqual(len(stats), 2, "应该创建两条玩家统计记录")
                
                stat1 = db.query(PlayerStats).filter(
                    PlayerStats.user_id == 101,
                    PlayerStats.game_type == "same_pattern_hunt"
                ).first()
                self.assertIsNotNone(stat1, "找不到用户101的统计记录")
                self.assertEqual(stat1.total_games, 1, "游戏次数应该是1")
                self.assertEqual(stat1.best_score, 15, "最高分应该是15")
                
                print("✅ 游戏记录存储测试通过")
                
            except AssertionError as e:
                print(f"❌ 断言失败: {e}")
                # 打印数据库中的实际记录用于调试
                all_sessions = db.query(GameSession).all()
                print(f"数据库中的游戏会话记录数量: {len(all_sessions)}")
                for s in all_sessions:
                    print(f"  - ID: {s.id}, 用户ID: {s.user_id}, 分数: {s.score}, 游戏类型: {s.game_type}")
                
                all_stats = db.query(PlayerStats).all()
                print(f"数据库中的玩家统计记录数量: {len(all_stats)}")
                for s in all_stats:
                    print(f"  - 用户ID: {s.user_id}, 游戏类型: {s.game_type}, 游戏次数: {s.total_games}")
                
                raise
            except Exception as e:
                print(f"❌ 数据库查询失败: {e}")
                raise
            finally:
                db.close()
    
    async def test_create_game_record_direct(self):
        """直接测试create_game_record_direct方法"""
        game = o2SPHGame(room_id="test_room_direct")
        game.start_time = datetime.utcnow()
        
        # 使用mock替代get_user_id_from_player_id
        with patch.object(game, 'get_user_id_from_player_id', return_value=201):
            # 直接调用方法
            await game.create_game_record_direct(
                player_id="test_direct_user",
                score=20,
                accuracy=85.5,
                rounds_played=41,
                rounds_total=48
            )
            
            # 验证数据
            db = next(get_db())
            try:
                session = db.query(GameSession).filter(GameSession.user_id == 201).first()
                self.assertIsNotNone(session, "游戏会话记录未创建")
                self.assertEqual(session.score, 20)
                self.assertEqual(session.accuracy, 85.5)
                self.assertEqual(session.rounds_played, 41)
                print("✅ 直接创建游戏记录测试通过")
            finally:
                db.close()
    
    async def test_error_handling(self):
        """测试错误处理机制"""
        game = o2SPHGame(room_id="test_error_room")
        
        # 模拟数据库操作失败
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.add.side_effect = Exception("模拟数据库错误")
            
            # 调用方法并检查是否正确处理异常
            try:
                result = await game.create_game_record_direct(
                    player_id="error_user",
                    score=0,
                    accuracy=0,
                    rounds_played=0,
                    rounds_total=48
                )
                # 不应该抛出异常，因为内部已捕获
                print("✅ 错误处理测试通过")
            except Exception as e:
                self.fail(f"create_game_record_direct方法应该处理数据库异常，但抛出了: {e}")
    
    def run_async_test(self, coro):
        """运行异步测试"""
        return asyncio.run(coro)
    
    def test_record_game_results_sync(self):
        """同步测试游戏结果记录"""
        self.run_async_test(self.test_record_game_results())
    
    def test_create_game_record_direct_sync(self):
        """同步测试直接创建游戏记录"""
        self.run_async_test(self.test_create_game_record_direct())
    
    def test_error_handling_sync(self):
        """同步测试错误处理"""
        self.run_async_test(self.test_error_handling())

# 添加直接运行测试的功能
if __name__ == "__main__":
    print("开始测试游戏记录存储功能...")
    unittest.main()