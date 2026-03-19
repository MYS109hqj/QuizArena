-- 版本：V001
-- 描述：添加成就系统所需的表结构
-- 创建日期：2025-11-7

-- 数据库选择已在执行脚本时通过命令行参数指定，不再需要硬编码数据库名

-- 创建成就定义表
CREATE TABLE IF NOT EXISTS achievements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    achievement_type VARCHAR(50) NOT NULL, -- basic, game_stat, game_process, game_end
    condition_type VARCHAR(50) NOT NULL, -- total_games, win_count, score_threshold, action_count, etc.
    target_value BIGINT NOT NULL DEFAULT 0,
    game_type VARCHAR(50) NULL, -- NULL表示适用于所有游戏
    icon VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_achievement_type (achievement_type),
    INDEX idx_condition_type (condition_type),
    INDEX idx_game_type (game_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建用户成就进度表
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id INT NOT NULL,
    achievement_id INT NOT NULL,
    current_progress BIGINT NOT NULL DEFAULT 0,
    is_unlocked BOOLEAN NOT NULL DEFAULT FALSE,
    unlocked_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id),
    INDEX idx_achievement_id (achievement_id),
    INDEX idx_is_unlocked (is_unlocked),
    INDEX idx_unlocked_at (unlocked_at),
    CONSTRAINT fk_user_achievements_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_achievements_achievement_id FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建更新玩家统计信息时的触发器，自动检查并更新成就进度
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS after_player_stats_update
AFTER UPDATE ON player_stats
FOR EACH ROW
BEGIN
    -- 这里将由应用程序代码来检查和更新成就
    -- 触发器仅记录需要检查成就的事件
    INSERT INTO achievement_check_queue (user_id, game_type, trigger_event)
    VALUES (NEW.user_id, NEW.game_type, 'player_stats_update')
    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
END $$
DELIMITER ;

-- 创建成就检查队列表
CREATE TABLE IF NOT EXISTS achievement_check_queue (
    user_id INT NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    trigger_event VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id, game_type, trigger_event),
    INDEX idx_processed (processed),
    INDEX idx_updated_at (updated_at),
    CONSTRAINT fk_achievement_check_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 显示迁移结果
SELECT 'V001成就系统表结构迁移完成' AS message;
SELECT 'V001表结构已创建：achievements, user_achievements, achievement_check_queue' AS details;
SELECT 'V001触发器已创建：after_player_stats_update' AS triggers;