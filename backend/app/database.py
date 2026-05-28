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

        CREATE TABLE IF NOT EXISTS commitlint_config (
            id                  INTEGER PRIMARY KEY DEFAULT 1,
            enabled             INTEGER DEFAULT 1,
            rule_type           TEXT DEFAULT 'conventional',
            type_enum           TEXT DEFAULT '["feat","fix","refactor","style","test","docs","chore"]',
            header_max_length   INTEGER DEFAULT 100,
            subject_min_length  INTEGER DEFAULT 5,
            rule_version        TEXT DEFAULT '1.0.0',
            updated_at          TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS commitlint_failures (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_sha  TEXT NOT NULL,
            commit_msg  TEXT NOT NULL,
            author      TEXT DEFAULT '',
            branch      TEXT DEFAULT '',
            pr_number   INTEGER DEFAULT 0,
            failed_at   TEXT DEFAULT (datetime('now','localtime')),
            error_msg   TEXT DEFAULT ''
        );

        INSERT OR IGNORE INTO commitlint_config (id) VALUES (1);
        """)
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
