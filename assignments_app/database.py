"""
作业提交子系统 - 数据库模块
独立于 backend/，不修改全局数据库文件，使用独立的 SQLite 数据库。
"""
import sqlite3
import os
from contextlib import contextmanager

# 独立的数据库文件，不影响 backend/app/data/exam.db
DB_PATH = os.environ.get("ASSIGNMENTS_DB_PATH", "assignments.db")


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
    """初始化作业提交子系统所需的数据库表"""
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS assignments (
            id              TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT DEFAULT '',
            deadline        TEXT NOT NULL,
            allowed_formats TEXT DEFAULT 'pdf,docx,zip,py,c,cpp,txt',
            max_file_size   INTEGER DEFAULT 52428800,
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id   TEXT NOT NULL,
            student_id      TEXT NOT NULL,
            file_path       TEXT DEFAULT '',
            file_name       TEXT DEFAULT '',
            file_size       INTEGER DEFAULT 0,
            file_type       TEXT DEFAULT '',
            content_text    TEXT DEFAULT '',
            version         INTEGER DEFAULT 1,
            submitted_at    TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id),
            UNIQUE(assignment_id, student_id, version)
        );
        """)
