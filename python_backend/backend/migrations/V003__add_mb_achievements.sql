-- 版本：V003
-- 描述：添加Memorial Banquet游戏成就
-- 创建日期：2026-02-22

-- 注意：此迁移脚本不会删除用户已解锁的成就数据
-- 只会添加新的成就定义

-- 删除旧的不符合命名规范的MB成就（如果有）
DELETE FROM achievements 
WHERE game_type = 'memorial_banquet' 
AND name NOT LIKE 'MB_%';

-- 添加Memorial Banquet游戏成就

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
('MB_游戏新手', '完成1局Memorial Banquet游戏', 'game_count', 'game_complete', 1, 'memorial_banquet', '🎴'),
('MB_游戏爱好者', '完成5局Memorial Banquet游戏', 'game_count', 'game_complete', 5, 'memorial_banquet', '🎴'),
('MB_游戏达人', '完成10局Memorial Banquet游戏', 'game_count', 'game_complete', 10, 'memorial_banquet', '🎴'),
('MB_游戏大师', '完成20局Memorial Banquet游戏', 'game_count', 'game_complete', 20, 'memorial_banquet', '🎴'),

-- 胜利相关成就
('MB_初次胜利', '获得1次Memorial Banquet游戏胜利', 'victory', 'game_win', 1, 'memorial_banquet', '🏆'),
('MB_锐不可当', '获得3次Memorial Banquet游戏胜利', 'victory', 'game_win', 3, 'memorial_banquet', '🏆'),
('MB_常胜将军', '获得10次Memorial Banquet游戏胜利', 'victory', 'game_win', 10, 'memorial_banquet', '🏆'),

-- 分数相关成就
('MB_初露锋芒', '单局得分达到10分', 'score', 'score_reach', 10, 'memorial_banquet', '⭐'),
('MB_崭露头角', '单局得分达到20分', 'score', 'score_reach', 20, 'memorial_banquet', '⭐'),
('MB_出类拔萃', '单局得分达到30分', 'score', 'score_reach', 30, 'memorial_banquet', '⭐'),

-- 准确率相关成就
('MB_精准记忆', '单局准确率达到80%', 'accuracy', 'accuracy_reach', 80, 'memorial_banquet', '🎯'),
('MB_完美记忆', '单局准确率达到90%', 'accuracy', 'accuracy_reach', 90, 'memorial_banquet', '🎯'),
('MB_神级记忆', '单局准确率达到95%', 'accuracy', 'accuracy_reach', 95, 'memorial_banquet', '🎯'),

-- 难度相关成就
('MB_挑战困难', '完成1局困难难度游戏', 'difficulty', 'difficulty_complete', 1, 'memorial_banquet', '💪'),
('MB_挑战极难', '完成1局极难难度游戏', 'difficulty', 'difficulty_complete', 1, 'memorial_banquet', '💪')

-- 仅当记录不存在时插入，否则更新为正确的值
ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    achievement_type = VALUES(achievement_type),
    condition_type = VALUES(condition_type),
    target_value = VALUES(target_value),
    icon = VALUES(icon);

-- 显示更新结果
SELECT 'V003 MB游戏成就添加完成' AS message;
SELECT COUNT(*) AS total_mb_achievements FROM achievements WHERE game_type = 'memorial_banquet';
SELECT name, description, achievement_type, condition_type, target_value, icon 
FROM achievements 
WHERE game_type = 'memorial_banquet' 
ORDER BY 
    CASE achievement_type 
        WHEN 'game_count' THEN 1 
        WHEN 'victory' THEN 2 
        WHEN 'score' THEN 3 
        WHEN 'accuracy' THEN 4 
        WHEN 'difficulty' THEN 5 
        ELSE 6 
    END,
    target_value;
