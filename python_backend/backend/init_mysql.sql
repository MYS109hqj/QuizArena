-- MySQL数据库初始化脚本
-- 用于创建QuizArena游戏所需的表结构

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS quizarena DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE quizarena;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_games INT NOT NULL DEFAULT 0,
    total_score INT NOT NULL DEFAULT 0,
    win_count INT NOT NULL DEFAULT 0,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建游戏会话表
CREATE TABLE IF NOT EXISTS game_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    room_id VARCHAR(100) NULL,
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL,
    duration_seconds INT NOT NULL DEFAULT 0,
    score INT NOT NULL DEFAULT 0,
    accuracy DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    rounds_played INT NOT NULL DEFAULT 0,
    rounds_total INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_game_type (game_type),
    INDEX idx_room_id (room_id),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建游戏回合记录表
CREATE TABLE IF NOT EXISTS game_rounds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    round_number INT NOT NULL,
    target_pattern VARCHAR(255) NULL,
    user_pattern VARCHAR(255) NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    response_time_ms INT NOT NULL DEFAULT 0,
    round_score INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_round_number (round_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建玩家统计信息表
CREATE TABLE IF NOT EXISTS player_stats (
    user_id INT NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    total_games INT NOT NULL DEFAULT 0,
    total_score BIGINT NOT NULL DEFAULT 0,
    average_score DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    best_score INT NOT NULL DEFAULT 0,
    average_accuracy DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    total_play_time_seconds BIGINT NOT NULL DEFAULT 0,
    last_played DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, game_type),
    INDEX idx_game_type (game_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建存储过程：更新玩家统计信息
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS UpdatePlayerStats(IN p_user_id INT, IN p_game_type VARCHAR(50))
BEGIN
    -- 声明变量
    DECLARE v_total_games INT DEFAULT 0;
    DECLARE v_total_score BIGINT DEFAULT 0;
    DECLARE v_average_score DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_best_score INT DEFAULT 0;
    DECLARE v_average_accuracy DECIMAL(5,2) DEFAULT 0.00;
    DECLARE v_total_play_time BIGINT DEFAULT 0;
    DECLARE v_last_played DATETIME DEFAULT NULL;
    
    -- 计算统计信息
    SELECT 
        COUNT(*) INTO v_total_games,
        COALESCE(SUM(score), 0) INTO v_total_score,
        COALESCE(AVG(score), 0) INTO v_average_score,
        COALESCE(MAX(score), 0) INTO v_best_score,
        COALESCE(AVG(accuracy), 0) INTO v_average_accuracy,
        COALESCE(SUM(duration_seconds), 0) INTO v_total_play_time,
        MAX(end_time) INTO v_last_played
    FROM game_sessions
    WHERE user_id = p_user_id 
      AND game_type = p_game_type
      AND status = 'completed';
    
    -- 更新或插入统计记录
    INSERT INTO player_stats (user_id, game_type, total_games, total_score, average_score, best_score, average_accuracy, total_play_time_seconds, last_played)
    VALUES (p_user_id, p_game_type, v_total_games, v_total_score, v_average_score, v_best_score, v_average_accuracy, v_total_play_time, v_last_played)
    ON DUPLICATE KEY UPDATE 
        total_games = v_total_games,
        total_score = v_total_score,
        average_score = v_average_score,
        best_score = v_best_score,
        average_accuracy = v_average_accuracy,
        total_play_time_seconds = v_total_play_time,
        last_played = v_last_played;
END $$
DELIMITER ;

-- 创建查看历史游戏数据的视图
CREATE VIEW IF NOT EXISTS user_game_history AS
SELECT 
    gs.id AS session_id,
    u.id AS user_id,
    u.username,
    gs.game_type,
    gs.room_id,
    gs.start_time,
    gs.end_time,
    gs.duration_seconds,
    gs.score,
    gs.accuracy,
    gs.rounds_played,
    gs.rounds_total,
    gs.status,
    gs.created_at,
    ps.total_games AS user_total_games,
    ps.best_score AS user_best_score,
    ps.average_score AS user_average_score
FROM game_sessions gs
JOIN users u ON gs.user_id = u.id
LEFT JOIN player_stats ps ON gs.user_id = ps.user_id AND gs.game_type = ps.game_type
ORDER BY gs.start_time DESC;

-- 显示创建结果
SELECT 'MySQL数据库初始化完成' AS message;
SELECT '表结构已创建：users, game_sessions, game_rounds, player_stats' AS details;