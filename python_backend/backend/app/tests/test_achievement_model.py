import unittest
from ..database import SessionLocal, create_tables
from ..models import Achievement, UserAchievement, User
from ..services.achievement_service import AchievementService

class TestAchievementModel(unittest.TestCase):
    """成就模型测试类"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建数据库表
        create_tables()
        # 创建数据库会话
        self.db = SessionLocal()
        
        # 创建测试用户
        self.test_user = User(
            username="test_user",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)
        
        # 创建测试成就
        self.test_achievement = Achievement(
            name="测试成就",
            description="这是一个测试成就",
            achievement_type="basic",
            condition_type="total_games",
            target_value=5,
            game_type=None,
            icon="test_icon.png"
        )
        self.db.add(self.test_achievement)
        self.db.commit()
        self.db.refresh(self.test_achievement)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 删除测试数据
        self.db.query(UserAchievement).delete()
        self.db.query(Achievement).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()
    
    def test_get_all_achievements(self):
        """测试获取所有成就"""
        achievements = AchievementService.get_all_achievements(self.db)
        self.assertEqual(len(achievements), 1)
        self.assertEqual(achievements[0].name, "测试成就")
    
    def test_check_and_update_achievement(self):
        """测试检查并更新成就进度"""
        # 更新进度，但未达到目标
        newly_unlocked = AchievementService.check_and_update_achievement(
            self.db, self.test_user.id, "total_games", 3
        )
        self.assertEqual(len(newly_unlocked), 0)
        
        # 查询用户成就记录
        user_achievement = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == self.test_user.id,
            UserAchievement.achievement_id == self.test_achievement.id
        ).first()
        
        self.assertIsNotNone(user_achievement)
        self.assertEqual(user_achievement.current_progress, 3)
        self.assertFalse(user_achievement.is_unlocked)
        
        # 更新进度，达到目标
        newly_unlocked = AchievementService.check_and_update_achievement(
            self.db, self.test_user.id, "total_games", 5
        )
        self.assertEqual(len(newly_unlocked), 1)
        self.assertEqual(newly_unlocked[0].name, "测试成就")
        
        # 重新查询用户成就记录
        self.db.refresh(user_achievement)
        self.assertTrue(user_achievement.is_unlocked)
        self.assertIsNotNone(user_achievement.unlocked_at)
    
    def test_get_user_achievement_stats(self):
        """测试获取用户成就统计"""
        stats = AchievementService.get_user_achievement_stats(self.db, self.test_user.id)
        self.assertEqual(stats["total_achievements"], 1)
        self.assertEqual(stats["unlocked_achievements"], 0)
        self.assertEqual(stats["unlock_percentage"], 0.0)
        
        # 解锁成就后再次检查
        AchievementService.check_and_update_achievement(
            self.db, self.test_user.id, "total_games", 5
        )
        
        stats = AchievementService.get_user_achievement_stats(self.db, self.test_user.id)
        self.assertEqual(stats["unlocked_achievements"], 1)
        self.assertEqual(stats["unlock_percentage"], 100.0)

if __name__ == '__main__':
    unittest.main()