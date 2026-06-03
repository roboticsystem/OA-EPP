import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

# 使用项目目录下的数据库文件
DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "exam.db")
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

# 确保数据库目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
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
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            student_id  TEXT UNIQUE NOT NULL,
            class_name  TEXT DEFAULT '',
            pinyin      TEXT DEFAULT '',
            pinyin_abbr TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS exams (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            is_active  INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS scores (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            exam_id      TEXT NOT NULL,
            score        REAL NOT NULL,
            total        REAL NOT NULL,
            submitted_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(student_id, exam_id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id  INTEGER NOT NULL,
            action         TEXT NOT NULL,
            target_type    TEXT NOT NULL,
            target_id      TEXT NOT NULL,
            detail_json    TEXT,
            action_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
