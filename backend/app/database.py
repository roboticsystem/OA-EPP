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

        -- F-S-053 课堂在线考试
        CREATE TABLE IF NOT EXISTS classroom_exams (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            start_at   TEXT NOT NULL,
            end_at     TEXT NOT NULL,
            is_active  INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS classroom_exam_questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id         TEXT NOT NULL,
            qtype           TEXT NOT NULL CHECK(qtype IN ('single','multi','blank','short')),
            content         TEXT NOT NULL,
            options_json    TEXT,
            answer_key_json TEXT NOT NULL,
            score           REAL NOT NULL,
            sort_no         INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (exam_id) REFERENCES classroom_exams(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS classroom_exam_attempts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id             TEXT NOT NULL,
            student_id          TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'draft'
                                CHECK(status IN ('draft','submitted','graded')),
            objective_score     REAL,
            subjective_pending  INTEGER DEFAULT 0,
            total_score         REAL,
            max_score           REAL,
            submitted_at        TEXT,
            auto_submitted      INTEGER DEFAULT 0,
            draft_saved_at      TEXT,
            answers_json        TEXT,
            UNIQUE(exam_id, student_id),
            FOREIGN KEY (exam_id) REFERENCES classroom_exams(id),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE INDEX IF NOT EXISTS idx_classroom_attempt_exam
            ON classroom_exam_attempts(exam_id);
        """)
        try:
            conn.execute(
                "ALTER TABLE classroom_exam_attempts ADD COLUMN question_scores_json TEXT"
            )
        except sqlite3.OperationalError:
            pass
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
