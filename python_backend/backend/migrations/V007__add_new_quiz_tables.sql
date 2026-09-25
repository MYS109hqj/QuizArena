CREATE TABLE IF NOT EXISTS new_quiz_question_banks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    current_version INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_new_quiz_bank_owner (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS new_quiz_question_bank_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bank_id INT NOT NULL,
    user_id INT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    UNIQUE KEY uq_new_quiz_bank_member (bank_id, user_id),
    INDEX ix_new_quiz_member_user (user_id),
    CONSTRAINT fk_new_quiz_member_bank FOREIGN KEY (bank_id)
        REFERENCES new_quiz_question_banks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS new_quiz_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bank_id INT NOT NULL,
    question_type VARCHAR(30) NOT NULL DEFAULT 'single_choice',
    prompt TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_answer_json TEXT NOT NULL,
    explanation TEXT NOT NULL,
    default_score INT NOT NULL DEFAULT 10,
    position INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_new_quiz_question_bank (bank_id),
    CONSTRAINT fk_new_quiz_question_bank FOREIGN KEY (bank_id)
        REFERENCES new_quiz_question_banks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS new_quiz_question_bank_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bank_id INT NOT NULL,
    version INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    snapshot_json LONGTEXT NOT NULL,
    published_by INT NOT NULL,
    published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_new_quiz_bank_version (bank_id, version),
    INDEX ix_new_quiz_version_bank (bank_id),
    CONSTRAINT fk_new_quiz_version_bank FOREIGN KEY (bank_id)
        REFERENCES new_quiz_question_banks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
