import pymysql
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger("database")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "156.239.252.40"),
    "port": int(os.environ.get("DB_PORT", "13306")),
    "user": os.environ.get("DB_USER", "student_dev"),
    "password": os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
    "database": os.environ.get("DB_NAME", "oaepp_dev"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    conn = pymysql.connect(**DB_CONFIG)
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _try_create_table(cur, table_name, create_sql):
    """尝试建表，无权限则警告并跳过。"""
    cur.execute(f"SHOW TABLES LIKE '{table_name}'")
    if cur.fetchone():
        logger.info(f"表 {table_name} 已存在，跳过。")
        return
    try:
        cur.execute(create_sql)
        logger.info(f"表 {table_name} 创建成功。")
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1142:  # ER_TABLEACCESS_DENIED_ERROR
            logger.warning(f"无 CREATE 权限，跳过建表 {table_name}。请 DBA 手动执行：\n{create_sql}")
        else:
            raise


def init_db():
    with db() as conn:
        cur = conn.cursor()

        _try_create_table(cur, "exam_students", """
        CREATE TABLE exam_students (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            student_id  VARCHAR(50) UNIQUE NOT NULL,
            class_name  VARCHAR(200) DEFAULT '',
            pinyin      VARCHAR(500) DEFAULT '',
            pinyin_abbr VARCHAR(200) DEFAULT '',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        _try_create_table(cur, "exam_list", """
        CREATE TABLE exam_list (
            id         VARCHAR(100) PRIMARY KEY,
            title      VARCHAR(300) NOT NULL,
            is_active  TINYINT DEFAULT 1
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        _try_create_table(cur, "exam_scores", """
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
        """)

        _try_create_table(cur, "exam_feedbacks", """
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
        """)

        cur.close()
