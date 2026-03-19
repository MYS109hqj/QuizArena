"""
Same Pattern Hunt 游戏基础成就初始化脚本
用于创建游戏次数和胜利相关的基础成就
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import get_db, engine
from app.models.achievement import Achievement
from sqlalchemy.exc import SQLAlchemyError

def init_sph_achievements():
    """初始化Same Pattern Hunt游戏的基础成就"""
    print("开始初始化 Same Pattern Hunt 游戏的基础成就...")
    
    # 定义游戏次数成就
    game_count_achievements = [
        {
            "name": "SPH_游戏新手",
            "description": "完成1局Same Pattern Hunt游戏",
            "icon": "⭐",
            "game_type": "same_pattern_hunt",
            "achievement_type": "game_count"
        },
        {
            "name": "SPH_游戏爱好者",
            "description": "完成5局Same Pattern Hunt游戏",
            "icon": "⭐",
            "game_type": "same_pattern_hunt",
            "achievement_type": "game_count"
        },
        {
            "name": "SPH_游戏达人",
            "description": "完成10局Same Pattern Hunt游戏",
            "icon": "⭐",
            "game_type": "same_pattern_hunt",
            "achievement_type": "game_count"
        },
        {
            "name": "SPH_游戏大师",
            "description": "完成20局Same Pattern Hunt游戏",
            "icon": "⭐",
            "game_type": "same_pattern_hunt",
            "achievement_type": "game_count"
        }
    ]
    
    # 定义胜利相关成就
    victory_achievements = [
        {
            "name": "SPH_初次胜利",
            "description": "获得1次Same Pattern Hunt游戏胜利",
            "icon": "🏆",
            "game_type": "same_pattern_hunt",
            "achievement_type": "victory"
        },
        {
            "name": "SPH_锐不可当",
            "description": "获得3次Same Pattern Hunt游戏胜利",
            "icon": "🏆",
            "game_type": "same_pattern_hunt",
            "achievement_type": "victory"
        },
        {
            "name": "SPH_常胜将军",
            "description": "获得10次Same Pattern Hunt游戏胜利",
            "icon": "🏆",
            "game_type": "same_pattern_hunt",
            "achievement_type": "victory"
        }
    ]
    
    # 合并所有成就
    all_achievements = game_count_achievements + victory_achievements
    
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
        init_sph_achievements()
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {str(e)}")
        sys.exit(1)