import os
import pymysql
from contextlib import contextmanager
from pymysql.cursors import DictCursor

DB_HOST     = os.environ.get("DB_HOST", "156.239.252.40")
DB_PORT     = int(os.environ.get("DB_PORT", "13306"))
DB_NAME     = os.environ.get("DB_NAME", "oaepp_dev")
DB_USER     = os.environ.get("DB_USER", "student_dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "OaEpp@Dev2026")


def get_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )
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


def init_db():
    """尝试建表；若当前用户无 DDL 权限则静默跳过（表已由管理员创建）。"""
    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id          INT PRIMARY KEY AUTO_INCREMENT,
                    name        VARCHAR(255) NOT NULL,
                    student_id  VARCHAR(255) UNIQUE NOT NULL,
                    class_name  VARCHAR(255) DEFAULT '',
                    pinyin      VARCHAR(255) DEFAULT '',
                    pinyin_abbr VARCHAR(255) DEFAULT '',
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id         VARCHAR(255) PRIMARY KEY,
                    title      VARCHAR(255) NOT NULL,
                    is_active  TINYINT DEFAULT 1
                )
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id           INT PRIMARY KEY AUTO_INCREMENT,
                    student_id   VARCHAR(255) NOT NULL,
                    exam_id      VARCHAR(255) NOT NULL,
                    score        FLOAT NOT NULL,
                    total        FLOAT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_student_exam (student_id, exam_id)
                )
                """)
            print("[init_db] 表结构初始化完成")
    except pymysql.err.OperationalError as e:
        # student_dev 无 CREATE 权限 → 假设表已由管理员预先创建
        print(f"[init_db] 无 DDL 权限，跳过建表（表应由管理员预创建）：{e}")
