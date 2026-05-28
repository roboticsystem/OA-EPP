import pymysql
import os
from contextlib import contextmanager
from urllib.parse import urlparse, unquote

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


def init_db():
    """Create tables if they don't exist. DDL may fail on shared DB with restricted permissions — that's OK."""
    with db() as conn:
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(255) NOT NULL,
                    student_id  VARCHAR(100) UNIQUE NOT NULL,
                    class_name  VARCHAR(255) DEFAULT '',
                    pinyin      VARCHAR(255) DEFAULT '',
                    pinyin_abbr VARCHAR(255) DEFAULT '',
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] students table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id         VARCHAR(100) PRIMARY KEY,
                    title      VARCHAR(255) NOT NULL,
                    is_active  TINYINT DEFAULT 1
                )
            """)
        except Exception as e:
            print(f"[init_db] exams table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id           INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   VARCHAR(100) NOT NULL,
                    exam_id      VARCHAR(100) NOT NULL,
                    score        DOUBLE NOT NULL,
                    total        DOUBLE NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, exam_id)
                )
            """)
        except Exception as e:
            print(f"[init_db] scores table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS github_bindings (
                    id              INT AUTO_INCREMENT PRIMARY KEY,
                    student_id      VARCHAR(100) UNIQUE NOT NULL,
                    github_username VARCHAR(255) DEFAULT '',
                    status          VARCHAR(50) DEFAULT 'unbound',
                    github_name     VARCHAR(255) DEFAULT '',
                    verified_at     TIMESTAMP NULL,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] github_bindings table skipped: {e}")
