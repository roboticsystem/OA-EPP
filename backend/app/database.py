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

<<<<<<< HEAD
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
=======
        # 基础表：scores（兼容 legacy）
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

        # classroom_exams：feature 分支中的在线课堂考试表（使用 MySQL 形式）
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classroom_exams (
                    id         VARCHAR(100) PRIMARY KEY,
                    title      VARCHAR(255) NOT NULL,
                    start_at   DATETIME NOT NULL,
                    end_at     DATETIME NOT NULL,
                    is_active  TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            print(f"[init_db] classroom_exams table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classroom_exam_questions (
                    id              INT AUTO_INCREMENT PRIMARY KEY,
                    exam_id         VARCHAR(100) NOT NULL,
                    qtype           VARCHAR(20) NOT NULL,
                    content         TEXT NOT NULL,
                    options_json    TEXT,
                    answer_key_json TEXT NOT NULL,
                    score           DOUBLE NOT NULL,
                    sort_no         INT NOT NULL DEFAULT 1,
                    FOREIGN KEY (exam_id) REFERENCES classroom_exams(id) ON DELETE CASCADE
                )
            """)
        except Exception as e:
            print(f"[init_db] classroom_exam_questions table skipped: {e}")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classroom_exam_attempts (
                    id                  INT AUTO_INCREMENT PRIMARY KEY,
                    exam_id             VARCHAR(100) NOT NULL,
                    student_id          VARCHAR(100) NOT NULL,
                    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
                    objective_score     DOUBLE,
                    subjective_pending  TINYINT DEFAULT 0,
                    total_score         DOUBLE,
                    max_score           DOUBLE,
                    submitted_at        DATETIME,
                    auto_submitted      TINYINT DEFAULT 0,
                    draft_saved_at      DATETIME,
                    answers_json        TEXT,
                    UNIQUE(exam_id, student_id),
                    FOREIGN KEY (exam_id) REFERENCES classroom_exams(id)
                )
            """)
        except Exception as e:
            print(f"[init_db] classroom_exam_attempts table skipped: {e}")

        # 尝试添加可选字段（兼容旧数据）
        try:
            conn.execute("ALTER TABLE classroom_exam_attempts ADD COLUMN question_scores_json TEXT")
        except Exception:
            pass

        # 继续创建 upstream/main 的表结构
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

        _migrate_chapters(conn)
        _migrate_courses(conn)


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
>>>>>>> upstream/main
