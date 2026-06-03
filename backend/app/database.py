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

        CREATE TABLE IF NOT EXISTS timeline_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            event_type   TEXT NOT NULL CHECK(event_type IN ('publish','submit','grade','feedback')),
            title        TEXT NOT NULL,
            description  TEXT DEFAULT '',
            course       TEXT DEFAULT '',
            related_id   TEXT DEFAULT '',
            event_time   TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        # 考试记录由 sync_exams() 根据 .md 文件动态维护，此处不再硬编码预置


def seed_timeline_events():
    """如果 timeline_events 为空，插入演示数据"""
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
            "INSERT INTO timeline_events (student_id, event_type, title, description, course, related_id, event_time) VALUES (?,?,?,?,?,?,?)",
            demo_events,
        )
