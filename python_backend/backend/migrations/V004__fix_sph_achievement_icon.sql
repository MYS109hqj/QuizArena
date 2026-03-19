-- 版本：V004
-- 描述：修复SPH成就"游戏达人"的icon字段
-- 创建日期：2026-02-22

-- 修复SPH成就"游戏达人"的icon字段，将SVG文件名改为emoji
UPDATE achievements 
SET icon = '⭐'
WHERE game_type = 'same_pattern_hunt' 
AND name = '游戏达人';

-- 显示更新结果
SELECT 'V004 SPH成就icon修复完成' AS message;
SELECT name, icon, game_type 
FROM achievements 
WHERE game_type = 'same_pattern_hunt' 
AND name = '游戏达人';
