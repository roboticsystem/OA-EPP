import pymysql
import os
from contextlib import contextmanager
from urllib.parse import urlparse, unquote
from pathlib import Path

# 加载 .env 文件（从项目根目录）
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key not in os.environ:  # 不覆盖已存在的环境变量
                    os.environ[key] = value

DATABASE_URL = os.environ.get("DATABASE_URL", "")


class _RowProxy(dict):
    """A dict that also supports index-based access like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _CursorWrapper:
    """Wraps a pymysql DictCursor so that execute/executemany return self for chaining."""

    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, sql, params=None):
        self._cur.execute(sql, params)
        return self

    def executemany(self, sql, params):
        self._cur.executemany(sql, params)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        return _RowProxy(row) if row else None

    def fetchall(self):
        return [_RowProxy(r) for r in self._cur.fetchall()]

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    def __getattr__(self, name):
        return getattr(self._cur, name)


def _parse_db_url():
    if DATABASE_URL:
        try:
            parsed = urlparse(DATABASE_URL)
            return {
                "host": parsed.hostname or "127.0.0.1",
                "port": parsed.port or 3306,
                "user": parsed.username or "root",
                "password": unquote(parsed.password) if parsed.password else "",
                "database": parsed.path.lstrip("/") or "oaepp_dev",
                "charset": "utf8mb4",
            }
        except Exception:
            pass
    # fallback to individual env vars
    return {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "oaepp_dev"),
        "charset": "utf8mb4",
    }


def get_connection():
    cfg = _parse_db_url()
    conn = pymysql.connect(**cfg, autocommit=False)
    return conn


@contextmanager
def db():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        yield _CursorWrapper(cursor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _migrate_chapters(conn):
    """幂等地为旧 chapters 表补充 F-S-011 字段（MySQL 版）"""
    try:
        conn.execute("SHOW COLUMNS FROM chapters")
        existing = {row["Field"] for row in conn.fetchall()}
        for col, ddl in {
            "chapter_type":     "ALTER TABLE chapters ADD COLUMN chapter_type     VARCHAR(50) DEFAULT '作业'",
            "deadline":         "ALTER TABLE chapters ADD COLUMN deadline         VARCHAR(50) DEFAULT ''",
            "status":           "ALTER TABLE chapters ADD COLUMN status           VARCHAR(50) DEFAULT '待开始'",
            "grading_criteria": "ALTER TABLE chapters ADD COLUMN grading_criteria TEXT",
        }.items():
            if col not in existing:
                try:
                    conn.execute(ddl)
                except Exception as e:
                    print(f"[_migrate_chapters] ALTER denied, skipping {col}: {e}")
    except Exception as e:
        print(f"[_migrate_chapters] SHOW COLUMNS denied, skipping: {e}")


def _migrate_courses(conn):
    """幂等地为旧 courses 表补充总分/截止提醒字段（MySQL 版）"""
    try:
        conn.execute("SHOW COLUMNS FROM courses")
        existing = {row["Field"] for row in conn.fetchall()}
        for col, ddl in {
            "total_score":       "ALTER TABLE courses ADD COLUMN total_score       INT DEFAULT 100",
            "deadline_reminder": "ALTER TABLE courses ADD COLUMN deadline_reminder VARCHAR(255) DEFAULT ''",
        }.items():
            if col not in existing:
                try:
                    conn.execute(ddl)
                except Exception as e:
                    print(f"[_migrate_courses] ALTER denied, skipping {col}: {e}")
    except Exception as e:
        print(f"[_migrate_courses] SHOW COLUMNS denied, skipping: {e}")


def init_db():
    """Create tables if they don't exist. DDL may fail on shared DB with restricted permissions — that's OK."""
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

        CREATE TABLE IF NOT EXISTS student_accounts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id     TEXT UNIQUE NOT NULL,
            email          TEXT DEFAULT '',
            password_hash  TEXT NOT NULL DEFAULT '',
            failed_attempts INTEGER DEFAULT 0,
            locked_until   TEXT DEFAULT '',
            created_at     TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_student_accounts_email_unique
            ON student_accounts(email) WHERE email != '';
        """)
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置
