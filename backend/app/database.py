import os
from contextlib import contextmanager

# 检测使用哪种数据库
USE_SQLITE = "DB_PATH" in os.environ

if USE_SQLITE:
    # SQLite 模式（向后兼容）
    import sqlite3

    DB_PATH = os.environ.get("DB_PATH", "/app/data/exam.db")

    @contextmanager
    def db():
        """数据库连接上下文管理器 - SQLite 版本"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn.cursor()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db():
        """初始化数据库（SQLite版本）"""
        print(f"[database] 初始化 SQLite 数据库: {DB_PATH}")
        with db() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    class_name TEXT,
                    pinyin TEXT,
                    pinyin_abbr TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    deadline TEXT,
                    published_at TEXT,
                    semester TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    score INTEGER,
                    total INTEGER,
                    submitted_at TEXT,
                    version INTEGER DEFAULT 1,
                    FOREIGN KEY (exam_id) REFERENCES exams(id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    UNIQUE(exam_id, student_id)
                )
            """)
        print("[database] SQLite 数据库初始化完成")

else:
    # MySQL 模式（新配置）
    import mysql.connector
    from mysql.connector import Error

    DB_HOST = os.environ.get("DB_HOST", "156.239.252.40")
    DB_PORT = int(os.environ.get("DB_PORT", "13306"))
    DB_NAME = os.environ.get("DB_NAME", "oaepp_dev")
    DB_USER = os.environ.get("DB_USER", "student_dev")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "OaEpp@Dev2026")

    @contextmanager
    def db():
        """数据库连接上下文管理器 - MySQL 版本"""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                charset="utf8mb4",
                autocommit=True
            )
            conn.cursor().execute("SET NAMES utf8mb4")
            yield conn.cursor(dictionary=True)
        except Error as e:
            print(f"数据库连接错误: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def init_db():
        """初始化数据库（MySQL版本）"""
        print("[database] 正在连接 MySQL 数据库...")
        try:
            with db() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    print("[database] MySQL 数据库连接成功！")
        except Exception as e:
            print(f"[database] 数据库初始化失败: {e}")
            raise
