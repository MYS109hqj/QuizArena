# 数据库迁移系统

本目录包含QuizArena项目的数据库迁移脚本，用于管理数据库结构的版本化更新。

## 迁移系统说明

### 迁移脚本命名规范

迁移脚本采用以下命名格式：
```
V{版本号}__{描述}.sql
```

- `V` 是固定前缀，表示Version
- `{版本号}` 是数字，从1开始递增
- `{描述}` 是对迁移内容的简要描述，使用下划线分隔单词

### 已创建的迁移脚本

- **V001__add_achievements_tables.sql**: 添加成就系统所需的表结构
  - achievements: 存储成就定义
  - user_achievements: 记录用户成就进度
  - achievement_check_queue: 成就检查队列
  - 相关触发器和索引

  V005修复了V003b中achievements表的字符集问题，将其从utf8mb3升级为utf8mb4，以支持emoji字符。

问题：插入emoji时报错：ERROR 1366: Incorrect string value: '\xF0\x9F\x8E\xB4'
  Emoji 是 4字节 UTF-8 字符（如 \xF0\x9F\x8E\xB4 是 🎴）
  MySQL/MariaDB 的 utf8 只支持 最多3字节
  只有 utf8mb4 才支持完整的4字节 UTF-8
  即使表是 utf8mb4，但客户端连接用 utf8 发送数据时，emoji 在传输层就被截断/拒绝了。

  解决方法：修改客户端连接字符集（临时）
  SET NAMES utf8mb4;
  SET CHARACTER SET utf8mb4;

## 如何使用迁移工具

### 1. 环境配置

迁移工具会自动从 `.env` 文件读取数据库配置，确保该文件包含以下配置：

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=quizarena
```

### 2. 执行迁移

在项目根目录执行以下命令运行迁移工具：

```bash
python backend/migrations/run_migrations.py
```

### 3. 迁移过程

- 工具会自动识别并按版本号顺序执行未应用的迁移脚本
- 执行结果会记录在 `migration_history` 表中
- 每个迁移只会被执行一次

## 成就系统数据库结构

### 1. achievements 表

存储成就的定义信息：

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | INT | 成就ID，主键 |
| name | VARCHAR(100) | 成就名称 |
| description | TEXT | 成就描述 |
| achievement_type | VARCHAR(50) | 成就类型：basic, game_stat, game_process, game_end |
| condition_type | VARCHAR(50) | 条件类型：total_games, win_count, score_threshold, action_count等 |
| target_value | BIGINT | 目标值，达成成就所需的数值 |
| game_type | VARCHAR(50) | 适用游戏类型，NULL表示适用于所有游戏 |
| icon | VARCHAR(255) | 成就图标URL |
| created_at | DATETIME | 创建时间 |

### 2. user_achievements 表

记录用户的成就进度：

| 字段名 | 类型 | 描述 |
|-------|------|------|
| user_id | INT | 用户ID，外键 |
| achievement_id | INT | 成就ID，外键 |
| current_progress | BIGINT | 当前进度 |
| is_unlocked | BOOLEAN | 是否已解锁 |
| unlocked_at | DATETIME | 解锁时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**主键**: (user_id, achievement_id)

### 3. achievement_check_queue 表

用于触发成就检查的队列：

| 字段名 | 类型 | 描述 |
|-------|------|------|
| user_id | INT | 用户ID，外键 |
| game_type | VARCHAR(50) | 游戏类型 |
| trigger_event | VARCHAR(50) | 触发事件类型 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| processed | BOOLEAN | 是否已处理 |

**主键**: (user_id, game_type, trigger_event)

### 4. 触发器

- **after_player_stats_update**: 在玩家统计信息更新后触发，将检查事件加入队列

## 注意事项

1. 迁移脚本执行前请备份数据库
2. 确保数据库用户有足够的权限执行DDL操作
3. 后续更新数据库结构时，请创建新的迁移脚本，不要修改已有的迁移脚本
4. 迁移脚本执行工具会自动处理依赖关系和版本控制

## 如何添加新的迁移

1. 在本目录创建新的迁移脚本，遵循命名规范
2. 编写SQL语句，确保脚本是幂等的（使用CREATE TABLE IF NOT EXISTS等）
3. 运行迁移工具应用新的迁移