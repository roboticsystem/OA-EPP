import pymysql
import os
import re
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

# 兼容旧的环境变量配置方式
MYSQL_HOST = os.environ.get("MYSQL_HOST", "").strip()
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "oaepp_dev")


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
        "host": os.environ.get("DB_HOST", MYSQL_HOST or "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", str(MYSQL_PORT))),
        "user": os.environ.get("DB_USER", MYSQL_USER),
        "password": os.environ.get("DB_PASSWORD", MYSQL_PASSWORD),
        "database": os.environ.get("DB_NAME", MYSQL_DATABASE),
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
                CREATE TABLE IF NOT EXISTS courses (
                    id                VARCHAR(100) PRIMARY KEY,
                    title             VARCHAR(255) NOT NULL,
                    semester          VARCHAR(50) DEFAULT '',
                    total_score       INT DEFAULT 100,
                    deadline_reminder VARCHAR(255) DEFAULT '',
                    is_active         TINYINT DEFAULT 1
                )
            """)
        except Exception as e:
            print(f"[init_db] courses table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id               VARCHAR(100) PRIMARY KEY,
                    course_id        VARCHAR(100) NOT NULL,
                    chapter_no       INT NOT NULL,
                    title            VARCHAR(255) NOT NULL,
                    filename         VARCHAR(255) NOT NULL,
                    file_path        VARCHAR(512) NOT NULL,
                    chapter_type     VARCHAR(50) DEFAULT '作业',
                    deadline         VARCHAR(50) DEFAULT '',
                    status           VARCHAR(50) DEFAULT '待开始',
                    grading_criteria TEXT
                )
            """)
        except Exception as e:
            print(f"[init_db] chapters table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS timeline_events (
                    id           INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   VARCHAR(100) NOT NULL,
                    event_type   VARCHAR(50) NOT NULL,
                    title        VARCHAR(255) NOT NULL,
                    description  TEXT,
                    course       VARCHAR(255) DEFAULT '',
                    related_id   VARCHAR(100) DEFAULT '',
                    event_time   VARCHAR(50) NOT NULL,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] timeline_events table skipped: {e}")

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

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teacher_comments (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    student_id  VARCHAR(100) NOT NULL,
                    comment     TEXT NOT NULL,
                    teacher     VARCHAR(100) DEFAULT 'teacher',
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_comments_student (student_id)
                )
            """)
        except Exception as e:
            print(f"[init_db] teacher_comments table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS student_github_info (
                    id              INT AUTO_INCREMENT PRIMARY KEY,
                    student_id      VARCHAR(100) UNIQUE NOT NULL,
                    github_username VARCHAR(255) DEFAULT '',
                    repo_name       VARCHAR(255) DEFAULT '',
                    github_token    VARCHAR(500) DEFAULT '',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] student_github_info table skipped: {e}")

        try:
            conn.execute("""
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
                )
            """)
        except Exception as e:
            print(f"[init_db] audit_logs table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS course_settings (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    `key`       VARCHAR(100) UNIQUE NOT NULL,
                    value       TEXT NOT NULL,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] course_settings table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id           INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   VARCHAR(100) NOT NULL,
                    date         VARCHAR(20) NOT NULL,
                    status       VARCHAR(20) NOT NULL,
                    note         VARCHAR(500) DEFAULT '',
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_attendance_student_date (student_id, date)
                )
            """)
        except Exception as e:
            print(f"[init_db] attendance table skipped: {e}")

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

        _migrate_chapters(conn)
        _migrate_courses(conn)

    # Insert default settings
    try:
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
    except Exception:
        pass


def seed_timeline_events():
    """如果 timeline_events 为空，插入演示数据。无权限或表不存在时跳过。"""
    try:
        with db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
            if count > 0:
                return

            students = conn.execute(
                "SELECT student_id FROM students LIMIT 1"
            ).fetchall()
            if not students:
                return

            sid = students[0]["student_id"]
            demo_events = [
                (sid, "publish", "第3章作业发布", "机器人运动学基础作业", "机器人学", "exam-03", "2026-03-01 08:00"),
                (sid, "submit", "第3章作业已提交", "提交文件：运动学分析报告.pdf", "机器人学", "exam-03", "2026-03-05 14:30"),
                (sid, "grade", "第3章作业已批改", "得分：85/100", "机器人学", "exam-03", "2026-03-08 10:00"),
                (sid, "feedback", "收到第3章批改反馈", "教师评语：分析部分做得很好，计算过程需更详细", "机器人学", "exam-03", "2026-03-08 10:30"),
                (sid, "publish", "期中考试发布", "机器人系统期中考试", "机器人学", "exam-mid", "2026-04-01 08:00"),
                (sid, "submit", "期中考试已提交", "提交用时：45分钟", "机器人学", "exam-mid", "2026-04-10 11:20"),
                (sid, "grade", "期中考试成绩公布", "得分：92/100", "机器人学", "exam-mid", "2026-04-12 14:00"),
                (sid, "publish", "课程设计任务发布", "基于ROS的机器人导航仿真", "工程实践", "project-01", "2026-04-15 08:00"),
                (sid, "submit", "课程设计初稿已提交", "提交文件：导航仿真源码.zip", "工程实践", "project-01", "2026-04-28 23:15"),
                (sid, "feedback", "收到课程设计反馈", "建议优化路径规划算法", "工程实践", "project-01", "2026-05-02 09:00"),
            ]

            conn.executemany(
                "INSERT INTO timeline_events (student_id, event_type, title, description, course, related_id, event_time) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                demo_events,
            )
    except Exception as e:
        print(f"[seed_timeline_events] skipped: {e}")
