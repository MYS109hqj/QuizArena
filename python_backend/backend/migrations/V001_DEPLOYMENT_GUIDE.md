# V001迁移脚本部署指南

## 迁移系统工作原理

QuizArena项目使用版本化的迁移系统管理数据库变更：

1. **版本化命名**：所有迁移脚本按照`Vxxx__description.sql`格式命名
2. **自动排序执行**：`run_migrations.py`脚本会自动按版本号从小到大排序并执行迁移
3. **迁移历史记录**：已执行的迁移会记录在`migration_history`表中
4. **幂等性保证**：系统会跳过已执行过的迁移脚本

## V001迁移说明

`V001__add_achievements_tables.sql`是成就系统的初始迁移脚本，主要功能：

- 创建`achievements`表（成就定义表）
- 创建`user_achievements`表（用户成就进度表）
- 创建`achievement_check_queue`表（成就检查队列表）
- 创建`after_player_stats_update`触发器

## V001修改部署方法

### 情况1：V001尚未执行

如果数据库中还没有应用V001迁移（即`migration_history`表中没有V001记录），则：

1. **直接运行现有迁移系统**：
   ```bash
   # 在backend目录下执行
   python migrations/run_migrations.py
   ```

2. 迁移系统会自动按顺序执行V001，然后执行V002

### 情况2：V001已执行但需要修改

如果V001已执行但需要修改其内容，则有以下选项：

#### 选项A：创建新的迁移脚本（推荐）

1. 创建新的迁移脚本，如`V003__update_achievements_tables.sql`
2. 在新脚本中编写修改表结构的SQL语句
3. 运行迁移系统应用新变更

#### 选项B：重置并重新执行（开发环境）

> **警告**：此方法会删除现有数据，仅适用于开发环境！

1. 删除迁移历史记录：
   ```sql
   DELETE FROM migration_history WHERE version = '001';
   ```

2. （可选）如果需要重新创建表：
   ```sql
   DROP TABLE IF EXISTS achievement_check_queue;
   DROP TABLE IF EXISTS user_achievements;
   DROP TABLE IF EXISTS achievements;
   ```

3. 运行迁移系统重新执行V001和后续迁移

### 情况3：需要修改V001的核心内容

如果需要大幅修改V001的核心逻辑，建议：

1. 在V002或更高版本的脚本中执行必要的修改
2. 确保新脚本与现有表结构兼容
3. 对于表结构变更，使用ALTER TABLE语句

## 迁移执行验证

执行迁移后，可以通过以下命令验证V001是否成功应用：

```sql
-- 检查迁移历史
SELECT * FROM migration_history WHERE version = '001';

-- 检查表是否创建成功
SHOW TABLES LIKE 'achievements';
SHOW TABLES LIKE 'user_achievements';
SHOW TABLES LIKE 'achievement_check_queue';

-- 检查触发器是否创建成功
SHOW TRIGGERS LIKE 'after_player_stats_update';
```

## 注意事项

1. **生产环境**：永远不要修改已应用的迁移脚本，应创建新的迁移脚本
2. **数据安全**：修改表结构前请备份数据
3. **迁移顺序**：确保迁移脚本按正确顺序执行（V001 → V002 → ...）
4. **依赖关系**：新迁移脚本应考虑与现有表结构和数据的兼容性

## 故障排除

### 迁移失败

如果V001迁移失败：

1. 检查错误日志获取详细信息
2. 确保数据库用户有足够权限（CREATE TABLE, CREATE TRIGGER等）
3. 验证`player_stats`表是否存在（触发器依赖此表）
4. 检查SQL语法错误

### 表已存在错误

如果遇到"Table already exists"错误：

1. 检查是否已有同名表
2. 考虑使用ALTER TABLE替代CREATE TABLE
3. 或添加更严格的IF NOT EXISTS条件

## 最佳实践

1. 始终先在测试环境验证迁移脚本
2. 保持迁移脚本的幂等性（可重复执行不会报错）
3. 为重要的数据库变更创建回滚脚本
4. 记录详细的迁移说明和依赖关系