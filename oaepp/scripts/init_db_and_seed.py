#!/usr/bin/env python3
"""数据库初始化 + 种子用户脚本

功能：
1. 创建 users 表（如不存在且有权限）
2. 创建成绩权重相关表（grade_weight_configs / grade_weight_history / grade_weight_audit_log / student_scores）
3. 插入默认学生账号：学号 2024000001，密码 2024000001（初始密码=学号）
4. 插入默认教师账号：学号 teacher，密码 admin123

密码使用 bcrypt 哈希（与现有数据库格式一致）。
幂等设计：重复运行不会产生重复数据。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql

from database import DB_CONFIG


def _create_grade_weight_tables(cur):
    """创建成绩权重相关表（如不存在且有权限）"""
    tables = [
        (
            "grade_weight_configs",
            """
            CREATE TABLE IF NOT EXISTS grade_weight_configs (
                course_id         BIGINT PRIMARY KEY,
                attendance_weight INT DEFAULT 25,
                exam_weight       INT DEFAULT 25,
                code_weight       INT DEFAULT 25,
                pr_weight         INT DEFAULT 25,
                updated_by        BIGINT NOT NULL DEFAULT 0,
                updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        ),
        (
            "grade_weight_history",
            """
            CREATE TABLE IF NOT EXISTS grade_weight_history (
                id           BIGINT AUTO_INCREMENT PRIMARY KEY,
                course_id    BIGINT NOT NULL,
                weights_json JSON NOT NULL,
                modified_by  BIGINT NOT NULL DEFAULT 0,
                modified_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_hist_course (course_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        ),
        (
            "grade_weight_audit_log",
            """
            CREATE TABLE IF NOT EXISTS grade_weight_audit_log (
                id         BIGINT AUTO_INCREMENT PRIMARY KEY,
                course_id  BIGINT NOT NULL,
                log_json   JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_audit_course (course_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        ),
        (
            "student_scores",
            """
            CREATE TABLE IF NOT EXISTS student_scores (
                id               BIGINT AUTO_INCREMENT PRIMARY KEY,
                student_no       VARCHAR(32) NOT NULL,
                full_name        VARCHAR(100) NOT NULL DEFAULT '',
                course_id        BIGINT NOT NULL,
                attendance_score DECIMAL(5,2) DEFAULT 0.00,
                exam_score       DECIMAL(5,2) DEFAULT 0.00,
                code_score       DECIMAL(5,2) DEFAULT 0.00,
                pr_score         DECIMAL(5,2) DEFAULT 0.00,
                INDEX idx_ss_course (course_id),
                INDEX idx_ss_student (student_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        ),
    ]

    for name, ddl in tables:
        try:
            cur.execute(ddl)
            print(f"[init] {name} 表已就绪")
        except (pymysql.ProgrammingError, pymysql.OperationalError) as e:
            if "command denied" in str(e).lower():
                print(f"[init] 跳过建表（权限不足），{name} 表应已存在")
            else:
                raise


def main():
    import bcrypt

    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["db"],
        charset=DB_CONFIG["charset"],
        autocommit=True,
    )

    try:
        with conn.cursor() as cur:
            # ── 1. 创建 users 表（如有权限） ──
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id            BIGINT AUTO_INCREMENT PRIMARY KEY,
                        student_no    VARCHAR(32)  NOT NULL UNIQUE,
                        full_name     VARCHAR(100) NOT NULL DEFAULT '',
                        role          VARCHAR(20)  NOT NULL DEFAULT 'student',
                        password_hash VARCHAR(255) NOT NULL DEFAULT '',
                        email         VARCHAR(200) NOT NULL DEFAULT '',
                        created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
                        updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_role (role)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                print("[init] users 表已就绪")
            except (pymysql.ProgrammingError, pymysql.OperationalError) as e:
                if "command denied" in str(e).lower():
                    print(f"[init] 跳过建表（权限不足），users 表应已存在")
                else:
                    raise

            # ── 2. 创建成绩权重相关表 ──
            _create_grade_weight_tables(cur)

            # ── 3. 种子用户 ──
            seed_users = [
                ("2024000001", "张三",   "student", "2024000001"),
                ("2024000002", "李四",   "student", "2024000002"),
                ("2024000003", "王五",   "student", "2024000003"),
                ("teacher",    "教师账号", "teacher", "admin123"),
            ]

            for sno, name, role, pwd in seed_users:
                pwd_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                email = f"{sno}@example.com" if role == "student" else "teacher@example.com"
                try:
                    cur.execute(
                        "INSERT INTO users (student_no, full_name, role, password_hash, email) "
                        "VALUES (%s, %s, %s, %s, %s) "
                        "ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)",
                        (sno, name, role, pwd_hash, email),
                    )
                    print(f"[seed] {role}: {sno} / {pwd}")
                except (pymysql.ProgrammingError, pymysql.OperationalError) as e:
                    if "command denied" in str(e).lower():
                        print(f"[seed] 跳过 {sno}（INSERT 权限不足）")
                    else:
                        raise

            print("[done] 数据库初始化完成")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
