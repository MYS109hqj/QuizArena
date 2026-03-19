"""
Memorial Banquet 游戏基础成就初始化脚本
用于创建游戏次数和胜利相关的基础成就
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import get_db, engine
from app.models.achievement import Achievement
from sqlalchemy.exc import SQLAlchemyError

def init_mb_achievements():
    """初始化Memorial Banquet游戏的基础成就"""
    print("开始初始化 Memorial Banquet 游戏的基础成就...")
    
    # 定义游戏次数成就
    game_count_achievements = [
        {
            "name": "MB_游戏新手",
            "description": "完成1局Memorial Banquet游戏",
            "icon": "🎴",
            "game_type": "memorial_banquet",
            "achievement_type": "game_count",
            "condition_type": "game_complete",
            "target_value": 1
        },
        {
            "name": "MB_游戏爱好者",
            "description": "完成5局Memorial Banquet游戏",
            "icon": "🎴",
            "game_type": "memorial_banquet",
            "achievement_type": "game_count",
            "condition_type": "game_complete",
            "target_value": 5
        },
        {
            "name": "MB_游戏达人",
            "description": "完成10局Memorial Banquet游戏",
            "icon": "🎴",
            "game_type": "memorial_banquet",
            "achievement_type": "game_count",
            "condition_type": "game_complete",
            "target_value": 10
        },
        {
            "name": "MB_游戏大师",
            "description": "完成20局Memorial Banquet游戏",
            "icon": "🎴",
            "game_type": "memorial_banquet",
            "achievement_type": "game_count",
            "condition_type": "game_complete",
            "target_value": 20
        }
    ]
    
    # 定义胜利相关成就
    victory_achievements = [
        {
            "name": "MB_初次胜利",
            "description": "获得1次Memorial Banquet游戏胜利",
            "icon": "🏆",
            "game_type": "memorial_banquet",
            "achievement_type": "victory",
            "condition_type": "game_win",
            "target_value": 1
        },
        {
            "name": "MB_锐不可当",
            "description": "获得3次Memorial Banquet游戏胜利",
            "icon": "🏆",
            "game_type": "memorial_banquet",
            "achievement_type": "victory",
            "condition_type": "game_win",
            "target_value": 3
        },
        {
            "name": "MB_常胜将军",
            "description": "获得10次Memorial Banquet游戏胜利",
            "icon": "🏆",
            "game_type": "memorial_banquet",
            "achievement_type": "victory",
            "condition_type": "game_win",
            "target_value": 10
        }
    ]
    
    # 定义分数相关成就
    score_achievements = [
        {
            "name": "MB_初露锋芒",
            "description": "单局得分达到10分",
            "icon": "⭐",
            "game_type": "memorial_banquet",
            "achievement_type": "score",
            "condition_type": "score_reach",
            "target_value": 10
        },
        {
            "name": "MB_崭露头角",
            "description": "单局得分达到20分",
            "icon": "⭐",
            "game_type": "memorial_banquet",
            "achievement_type": "score",
            "condition_type": "score_reach",
            "target_value": 20
        },
        {
            "name": "MB_出类拔萃",
            "description": "单局得分达到30分",
            "icon": "⭐",
            "game_type": "memorial_banquet",
            "achievement_type": "score",
            "condition_type": "score_reach",
            "target_value": 30
        }
    ]
    
    # 定义准确率相关成就
    accuracy_achievements = [
        {
            "name": "MB_精准记忆",
            "description": "单局准确率达到80%",
            "icon": "🎯",
            "game_type": "memorial_banquet",
            "achievement_type": "accuracy",
            "condition_type": "accuracy_reach",
            "target_value": 80
        },
        {
            "name": "MB_完美记忆",
            "description": "单局准确率达到90%",
            "icon": "🎯",
            "game_type": "memorial_banquet",
            "achievement_type": "accuracy",
            "condition_type": "accuracy_reach",
            "target_value": 90
        },
        {
            "name": "MB_神级记忆",
            "description": "单局准确率达到95%",
            "icon": "🎯",
            "game_type": "memorial_banquet",
            "achievement_type": "accuracy",
            "condition_type": "accuracy_reach",
            "target_value": 95
        }
    ]
    
    # 定义难度相关成就
    difficulty_achievements = [
        {
            "name": "MB_挑战困难",
            "description": "完成1局困难难度游戏",
            "icon": "💪",
            "game_type": "memorial_banquet",
            "achievement_type": "difficulty",
            "condition_type": "difficulty_complete",
            "target_value": 1
        },
        {
            "name": "MB_挑战极难",
            "description": "完成1局极难难度游戏",
            "icon": "💪",
            "game_type": "memorial_banquet",
            "achievement_type": "difficulty",
            "condition_type": "difficulty_complete",
            "target_value": 1
        }
    ]
    
    # 合并所有成就
    all_achievements = game_count_achievements + victory_achievements + score_achievements + accuracy_achievements + difficulty_achievements
    
    # 获取数据库会话
    db = next(get_db())
    try:
        created_count = 0
        updated_count = 0
        
        for achievement_data in all_achievements:
            # 检查成就是否已存在
            existing_achievement = db.query(Achievement).filter(
                Achievement.name == achievement_data["name"],
                Achievement.game_type == achievement_data["game_type"]
            ).first()
            
            if existing_achievement:
                # 更新现有成就
                for key, value in achievement_data.items():
                    setattr(existing_achievement, key, value)
                updated_count += 1
                print(f"✓ 更新成就: {achievement_data['name']}")
            else:
                # 创建新成就
                new_achievement = Achievement(**achievement_data)
                db.add(new_achievement)
                created_count += 1
                print(f"✓ 创建成就: {achievement_data['name']}")
        
        # 提交事务
        db.commit()
        print(f"\n✅ 成就初始化完成!")
        print(f"  - 创建了 {created_count} 个新成就")
        print(f"  - 更新了 {updated_count} 个现有成就")
        print(f"  - 总共 {created_count + updated_count} 个成就")
        
    except SQLAlchemyError as e:
        print(f"\n❌ 初始化成就时发生数据库错误: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        print(f"\n❌ 初始化成就时发生错误: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        init_mb_achievements()
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {str(e)}")
        sys.exit(1)
