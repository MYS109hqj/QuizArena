-- 版本：V006
-- 描述：将 users.avatar 列类型从 TEXT（64KB）改为 LONGTEXT（4GB）
-- 创建日期：2026-09-05
-- 原因：头像以 base64 字符串存储（cropperjs toDataURL），300x300 PNG 约 100-500KB，
--       MySQL TEXT 最大 65,535 字节（64KB），导致 "Data too long for column 'avatar'"，
--       后端返回 500 Internal Server Error，前端 JSON 解析失败报
--       "Unexpected token 'I', 'Internal S'... is not valid JSON"。
-- 注意：MySQL 不允许 TEXT/BLOB/LONGTEXT 列设置 DEFAULT 值（报错 1101），
--       因此这里不设 DEFAULT；默认值由 SQLAlchemy 模型的 Python 端 default 填充。

-- 先修改列类型（去掉 DEFAULT）
ALTER TABLE users
    MODIFY COLUMN avatar LONGTEXT NULL;

-- 将历史 NULL 值补成默认头像（与模型 default 保持一致）
UPDATE users SET avatar = 'default_avatar.png' WHERE avatar IS NULL;

-- 验证列类型
SELECT 'V006 avatar 列已改为 LONGTEXT' AS message;
SHOW COLUMNS FROM users LIKE 'avatar';
