import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "/app/data/exam.db")


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


def _migrate_chapters(conn):
    """幂等地为旧 chapters 表补充 F-S-011 字段"""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(chapters)").fetchall()}
    for col, ddl in {
        "chapter_type":     "ALTER TABLE chapters ADD COLUMN chapter_type     TEXT DEFAULT '作业'",
        "deadline":         "ALTER TABLE chapters ADD COLUMN deadline         TEXT DEFAULT ''",
        "status":           "ALTER TABLE chapters ADD COLUMN status           TEXT DEFAULT '待开始'",
        "grading_criteria": "ALTER TABLE chapters ADD COLUMN grading_criteria TEXT DEFAULT ''",
    }.items():
        if col not in existing:
            conn.execute(ddl)


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

        CREATE TABLE IF NOT EXISTS courses (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            semester   TEXT DEFAULT '',
            is_active  INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id               TEXT PRIMARY KEY,
            course_id        TEXT NOT NULL REFERENCES courses(id),
            chapter_no       INTEGER NOT NULL,
            title            TEXT NOT NULL,
            filename         TEXT NOT NULL,
            file_path        TEXT NOT NULL,
            chapter_type     TEXT DEFAULT '作业',
            deadline         TEXT DEFAULT '',
            status           TEXT DEFAULT '待开始',
            grading_criteria TEXT DEFAULT ''
        );
        """)
        _migrate_chapters(conn)
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
