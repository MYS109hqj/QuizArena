-- 版本：V005
-- 描述：修改achievements表的icon列字符集为utf8mb4以支持emoji
-- 创建日期：2026-02-22

-- 修改achievements表的icon列字符集为utf8mb4
ALTER TABLE achievements 
MODIFY COLUMN icon VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL;

-- 显示修改结果
SELECT 'V005 achievements表icon列字符集已修改为utf8mb4' AS message;

-- 验证修改
SELECT 
    COLUMN_NAME,
    CHARACTER_SET_NAME,
    COLLATION_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'quizarena'
  AND TABLE_NAME = 'achievements'
  AND COLUMN_NAME = 'icon';
