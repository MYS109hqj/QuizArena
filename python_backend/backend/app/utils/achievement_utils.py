"""成就相关的工具函数"""

# 支持的成就类型
supported_achievement_types = [
    "basic",           # 基础成就
    "game_stat",       # 游戏统计成就
    "game_process",    # 游戏过程成就
    "game_end"         # 游戏结束成就
]

# 支持的条件类型
supported_condition_types = [
    "total_games",      # 总游戏次数
    "win_count",        # 获胜次数
    "score_threshold",  # 分数阈值
    "action_count",     # 特定动作次数
    "time_played",      # 游戏时长
    "consecutive_wins"  # 连胜次数
]

def is_valid_achievement_type(achievement_type: str) -> bool:
    """验证成就类型是否有效"""
    return achievement_type in supported_achievement_types

def is_valid_condition_type(condition_type: str) -> bool:
    """验证条件类型是否有效"""
    return condition_type in supported_condition_types

def calculate_progress_percentage(current: int, target: int) -> float:
    """计算进度百分比
    
    Args:
        current: 当前进度
        target: 目标进度
        
    Returns:
        float: 进度百分比 (0.0-100.0)
    """
    if target <= 0:
        return 100.0
    return min(100.0, (current / target) * 100)

def get_achievement_icon_default(achievement_type: str) -> str:
    """获取成就默认图标
    
    Args:
        achievement_type: 成就类型
        
    Returns:
        str: 默认图标文件名
    """
    icon_map = {
        "basic": "achievement_basic.png",
        "game_stat": "achievement_stat.png",
        "game_process": "achievement_process.png",
        "game_end": "achievement_end.png"
    }
    return icon_map.get(achievement_type, "achievement_default.png")