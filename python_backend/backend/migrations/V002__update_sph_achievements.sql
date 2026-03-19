-- 版本：V002
-- 描述：更新Same Pattern Hunt游戏成就（严格按照init_achievements.py脚本）
-- 创建日期：2025-11-10

-- 注意：此迁移脚本不会删除用户已解锁的成就数据
-- 只会更新成就定义并添加新的成就

-- 备份当前的SPH成就数据（可选）
-- CREATE TABLE IF NOT EXISTS achievements_backup_sph AS
-- SELECT * FROM achievements WHERE game_type = 'same_pattern_hunt';

-- 删除旧的不符合命名规范的SPH成就
DELETE FROM achievements 
WHERE game_type = 'same_pattern_hunt' 
AND name NOT LIKE 'SPH_%';

-- 严格按照init_achievements.py添加/更新SPH游戏成就

-- 游戏次数相关成就
INSERT INTO achievements (
    name, 
    description, 
    achievement_type, 
    condition_type, 
    target_value, 
    game_type, 
    icon
) VALUES
('SPH_游戏新手', '完成1局Same Pattern Hunt游戏', 'game_count', 'total_games', 1, 'same_pattern_hunt', '⭐'),
('SPH_游戏爱好者', '完成5局Same Pattern Hunt游戏', 'game_count', 'total_games', 5, 'same_pattern_hunt', '⭐'),
('SPH_游戏达人', '完成10局Same Pattern Hunt游戏', 'game_count', 'total_games', 10, 'same_pattern_hunt', '⭐'),
('SPH_游戏大师', '完成20局Same Pattern Hunt游戏', 'game_count', 'total_games', 20, 'same_pattern_hunt', '⭐'),

-- 胜利相关成就
('SPH_初次胜利', '获得1次Same Pattern Hunt游戏胜利', 'victory', 'win_count', 1, 'same_pattern_hunt', '🏆'),
('SPH_锐不可当', '获得3次Same Pattern Hunt游戏胜利', 'victory', 'win_count', 3, 'same_pattern_hunt', '🏆'),
('SPH_常胜将军', '获得10次Same Pattern Hunt游戏胜利', 'victory', 'win_count', 10, 'same_pattern_hunt', '🏆')

-- 仅当记录不存在时插入，否则更新为正确的值
ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    achievement_type = VALUES(achievement_type),
    condition_type = VALUES(condition_type),
    target_value = VALUES(target_value),
    icon = VALUES(icon);

-- 显示更新结果
SELECT 'V002 SPH游戏成就更新完成' AS message;
SELECT COUNT(*) AS total_sph_achievements FROM achievements WHERE game_type = 'same_pattern_hunt';
SELECT name, description, achievement_type, condition_type, target_value, icon 
FROM achievements 
WHERE game_type = 'same_pattern_hunt' 
ORDER BY 
    CASE achievement_type 
        WHEN 'game_count' THEN 1 
        WHEN 'victory' THEN 2 
        ELSE 3 
    END,
    target_value;