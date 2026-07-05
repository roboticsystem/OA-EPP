import sqlite3
import os
from contextlib import contextmanager

import pymysql

DB_PATH = os.environ.get("DB_PATH", "/app/data/exam.db")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "156.239.252.40")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "13306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "student_dev")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "OaEpp@Dev2026")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "oaepp_dev")


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


def get_mysql_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def mysql_db():
    conn = get_mysql_connection()
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
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
