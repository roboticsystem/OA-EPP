import os
import re
from contextlib import contextmanager

MYSQL_HOST = os.environ.get("MYSQL_HOST", "").strip()
USE_MYSQL = bool(MYSQL_HOST)

# ============================================================
# MySQL backend
# ============================================================
if USE_MYSQL:
    import pymysql
    from pymysql.cursors import DictCursor

    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "oaepp_dev")

    class Row:
        """Supports both dict-style row["col"] and index-style row[0] access."""
        def __init__(self, data: dict):
            self._data = data
            self._keys = list(data.keys())

        def __getitem__(self, key):
            if isinstance(key, int):
                return self._data[self._keys[key]]
            return self._data[key]

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._data.items()

        def values(self):
            return self._data.values()

        def __iter__(self):
            return iter(self._keys)

        def __repr__(self):
            return repr(self._data)

        def get(self, key, default=None):
            return self._data.get(key, default)

    class _CursorWrapper:
        """Wraps a PyMySQL cursor so fetchone/fetchall return Row objects."""
        def __init__(self, cursor):
            self._cursor = cursor
            self.lastrowid = cursor.lastrowid

        def fetchone(self):
            row = self._cursor.fetchone()
            if row is None:
                return None
            return Row(row)

        def fetchall(self):
            return [Row(r) for r in self._cursor.fetchall()]

    def _convert_sql(sql: str) -> str:
        """Convert SQLite SQL dialect to MySQL dialect."""
        # Replace ? placeholders with %s
        sql = sql.replace("?", "%s")
        # INSERT OR REPLACE INTO → REPLACE INTO
        sql = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "REPLACE INTO", sql, flags=re.IGNORECASE)
        # ON CONFLICT(x) DO UPDATE SET → ON DUPLICATE KEY UPDATE
        sql = re.sub(
            r"ON\s+CONFLICT\s*\([^)]+\)\s*DO\s+UPDATE\s+SET\s*",
            "ON DUPLICATE KEY UPDATE ",
            sql, flags=re.IGNORECASE,
        )
        # excluded.col → VALUES(col)
        sql = re.sub(r"\bexcluded\.(\w+)", r"VALUES(\1)", sql)
        # datetime('now','localtime') → NOW()
        sql = sql.replace("datetime('now','localtime')", "NOW()")
        return sql

    class MySQLConnection:
        def __init__(self, conn):
            self._conn = conn

        def execute(self, sql, params=None):
            sql = _convert_sql(sql)
            cursor = self._conn.cursor()
            cursor.execute(sql, params or ())
            return _CursorWrapper(cursor)

        def executemany(self, sql, params):
            sql = _convert_sql(sql)
            cursor = self._conn.cursor()
            cursor.executemany(sql, params)
            return cursor.rowcount

        def executescript(self, sql: str):
            """Execute multiple statements separated by semicolons."""
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            cursor = self._conn.cursor()
            for stmt in statements:
                stmt = _convert_sql(stmt)
                if stmt:
                    cursor.execute(stmt)
            cursor.close()

        def commit(self):
            self._conn.commit()

        def rollback(self):
            self._conn.rollback()

        def close(self):
            self._conn.close()

    def get_connection():
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        return MySQLConnection(conn)

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

    def _init_mysql():
        try:
            with db() as conn:
                conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                student_id  VARCHAR(100) UNIQUE NOT NULL,
                class_name  VARCHAR(255) DEFAULT '',
                pinyin      VARCHAR(1000) DEFAULT '',
                pinyin_abbr VARCHAR(100) DEFAULT '',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS exams (
                id         VARCHAR(200) PRIMARY KEY,
                title      VARCHAR(500) NOT NULL,
                is_active  INT DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS scores (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                student_id   VARCHAR(100) NOT NULL,
                exam_id      VARCHAR(200) NOT NULL,
                score        DOUBLE NOT NULL,
                total        DOUBLE NOT NULL,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_scores_student_exam (student_id, exam_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS teacher_comments (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                student_id  VARCHAR(100) NOT NULL,
                comment     TEXT NOT NULL,
                teacher     VARCHAR(100) DEFAULT 'teacher',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_comments_student (student_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS student_github_info (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                student_id      VARCHAR(100) UNIQUE NOT NULL,
                github_username VARCHAR(255) DEFAULT '',
                repo_name       VARCHAR(255) DEFAULT '',
                github_token    VARCHAR(500) DEFAULT '',
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS audit_logs (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                action       VARCHAR(100) NOT NULL,
                operator     VARCHAR(100) DEFAULT 'teacher',
                target_type  VARCHAR(50) NOT NULL,
                target_id    VARCHAR(200),
                format       VARCHAR(50),
                ip_address   VARCHAR(50),
                user_agent   VARCHAR(500),
                details      TEXT,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS course_settings (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                `key`       VARCHAR(100) UNIQUE NOT NULL,
                value       TEXT NOT NULL,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS attendance (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                student_id   VARCHAR(100) NOT NULL,
                date         VARCHAR(20) NOT NULL,
                status       VARCHAR(20) NOT NULL,
                note         VARCHAR(500) DEFAULT '',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_attendance_student_date (student_id, date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

                # Create indexes (ignore duplicate / permission errors)
                for idx_sql in [
                    "CREATE INDEX idx_scores_student ON scores(student_id)",
                    "CREATE INDEX idx_scores_exam ON scores(exam_id)",
                    "CREATE INDEX idx_attendance_student ON attendance(student_id)",
                    "CREATE INDEX idx_audit_logs_created ON audit_logs(created_at)",
                    "CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id)",
                ]:
                    try:
                        conn.execute(idx_sql)
                    except Exception:
                        pass

            # Insert default settings
            with db() as conn:
                existing = {r["key"] for r in conn.execute("SELECT `key` FROM course_settings").fetchall()}
                defaults = [
                    ("course_name", "研究生课程《机器人系统》"),
                    ("semester", "2024-2025学年第一学期"),
                    ("github_token", ""),
                ]
                for key, value in defaults:
                    if key not in existing:
                        conn.execute(
                            "INSERT INTO course_settings (`key`, value) VALUES (%s, %s)",
                            (key, value),
                        )
        except Exception as e:
            import sys
            print(f"[init_db] MySQL 初始化跳过（权限不足或表已存在）: {e}", file=sys.stderr)

    def init_db():
        _init_mysql()

# ============================================================
# SQLite backend (original, unchanged)
# ============================================================
else:
    import sqlite3

    DB_PATH = os.environ.get(
        "DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "exam.db"),
    )
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

            CREATE TABLE IF NOT EXISTS teacher_comments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  TEXT NOT NULL,
                comment     TEXT NOT NULL,
                teacher     TEXT DEFAULT 'teacher',
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(student_id)
            );

            CREATE TABLE IF NOT EXISTS student_github_info (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      TEXT UNIQUE NOT NULL,
                github_username TEXT DEFAULT '',
                repo_name       TEXT DEFAULT '',
                github_token    TEXT DEFAULT '',
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                action       TEXT NOT NULL,
                operator     TEXT DEFAULT 'teacher',
                target_type  TEXT NOT NULL,
                target_id    TEXT,
                format       TEXT,
                ip_address   TEXT,
                user_agent   TEXT,
                details      TEXT DEFAULT '',
                created_at   TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS course_settings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT UNIQUE NOT NULL,
                value       TEXT NOT NULL,
                updated_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   TEXT NOT NULL,
                date         TEXT NOT NULL,
                status       TEXT NOT NULL,
                note         TEXT DEFAULT '',
                created_at   TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(student_id, date)
            );

            CREATE INDEX IF NOT EXISTS idx_scores_student ON scores(student_id);
            CREATE INDEX IF NOT EXISTS idx_scores_exam ON scores(exam_id);
            CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_type, target_id);
            """)

            existing_keys = conn.execute("SELECT key FROM course_settings").fetchall()
            existing_keys_set = {row["key"] for row in existing_keys}

            default_settings = [
                ("course_name", "研究生课程《机器人系统》"),
                ("semester", "2024-2025学年第一学期"),
                ("github_token", ""),
            ]

            for key, value in default_settings:
                if key not in existing_keys_set:
                    conn.execute(
                        "INSERT INTO course_settings (key, value) VALUES (?, ?)",
                        (key, value),
                    )
