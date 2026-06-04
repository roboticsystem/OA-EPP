-- ============================================================
-- F-T-003-AI / F-T-010: 缺失表和字段的 DDL
-- 请用具有 DDL 权限的账号（如 root）在 oaepp_dev 库执行
-- ============================================================

-- 1. github_bindings 增加 repo_name 和 github_token
ALTER TABLE github_bindings
  ADD COLUMN repo_name VARCHAR(255) DEFAULT '' AFTER github_name,
  ADD COLUMN github_token VARCHAR(255) DEFAULT '' AFTER repo_name;

-- 2. 教师评语表
CREATE TABLE IF NOT EXISTS teacher_comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_user_id BIGINT NOT NULL,
    comment TEXT NOT NULL,
    teacher_user_id BIGINT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_student (student_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 课程设置表
CREATE TABLE IF NOT EXISTS course_settings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(64) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 默认课程设置
INSERT IGNORE INTO course_settings (setting_key, setting_value) VALUES
('course_name', '研究生课程《机器人系统》'),
('semester', '2024-2025学年第一学期'),
('github_token', '');
