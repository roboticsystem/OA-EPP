-- ==========================================
-- OA-EPP 考试系统所需表
-- 请在 oaepp_dev 数据库中执行此脚本
-- ==========================================

USE oaepp_dev;

-- 1. 学生名单
CREATE TABLE exam_students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    student_id  VARCHAR(50) UNIQUE NOT NULL,
    class_name  VARCHAR(200) DEFAULT '',
    pinyin      VARCHAR(500) DEFAULT '',
    pinyin_abbr VARCHAR(200) DEFAULT '',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 考试列表
CREATE TABLE exam_list (
    id         VARCHAR(100) PRIMARY KEY,
    title      VARCHAR(300) NOT NULL,
    is_active  TINYINT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 考试成绩
CREATE TABLE exam_scores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(50) NOT NULL,
    exam_id         VARCHAR(100) NOT NULL,
    score           DOUBLE NOT NULL,
    total           DOUBLE NOT NULL,
    submitted_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    allow_resubmit  TINYINT DEFAULT 0,
    UNIQUE KEY uk_student_exam (student_id, exam_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 评语与反馈
CREATE TABLE exam_feedbacks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(50) NOT NULL,
    exam_id         VARCHAR(100) NOT NULL,
    teacher_comment TEXT,
    deduction_items JSON,
    suggestions     JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
