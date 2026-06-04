"""
Database connection and query functions for the OA-EPP Reflex app.

Uses SQLite for local development (same pattern as backend/app/database.py).
MySQL is configured for production deployment via docker-compose.

The student_dev MySQL account has DML-only privileges (no CREATE TABLE),
so we use SQLite locally. For production, the tables must be pre-created
by an admin account or via the docker-compose MySQL init scripts.
"""

import os
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger("oaepp.database")

# ── Database path ────────────────────────────────────────────────────────

DB_PATH = os.environ.get("OAEPP_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "profile.db"))

@contextmanager
def get_connection():
    """Context manager yielding a sqlite3 connection with Row factory.

    Commits on success, rolls back on exception, closes on exit.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ── Database initialisation ──────────────────────────────────────────────

def init_db():
    """Create tables if they do not exist. Idempotent."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            role          TEXT NOT NULL DEFAULT 'student',
            student_no    TEXT UNIQUE,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name     TEXT NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS students (
            user_id    INTEGER PRIMARY KEY REFERENCES users(id),
            class_name TEXT NOT NULL DEFAULT '',
            phone      TEXT
        );
        """)
    logger.info("Database tables ensured (SQLite: %s)", DB_PATH)

def seed_student():
    """Insert a demo student if the users table is empty."""
    from werkzeug.security import generate_password_hash

    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()["cnt"] > 0:
            return

        cur = conn.execute(
            """INSERT INTO users (role, student_no, email, password_hash, full_name)
               VALUES ('student', ?, ?, ?, ?)""",
            (
                "2021001001",
                "zhangsan@example.edu.cn",
                generate_password_hash("Test@123456"),
                "张三",
            ),
        )
        user_id = cur.lastrowid

        conn.execute(
            """INSERT INTO students (user_id, class_name, phone)
               VALUES (?, ?, ?)""",
            (user_id, "工程实践班A", "13800138000"),
        )
    logger.info("Seed student inserted (student_no=2021001001, password=Test@123456).")

# ── Profile queries ──────────────────────────────────────────────────────

def get_student_profile(student_id: int) -> dict | None:
    """Return joined user + student row for *student_id*, or None."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT u.id, u.student_no, u.email, u.full_name,
                      s.class_name, s.phone
               FROM users u
               LEFT JOIN students s ON s.user_id = u.id
               WHERE u.id = ? AND u.is_active = 1""",
            (student_id,),
        ).fetchone()
    if row:
        return {
            "id": row["id"],
            "student_no": row["student_no"],
            "email": row["email"],
            "full_name": row["full_name"],
            "class_name": row["class_name"] or "",
            "phone": row["phone"] or "",
        }
    return None

def update_student_profile(
    student_id: int,
    full_name: str,
    email: str,
    class_name: str,
    phone: str,
) -> bool:
    """Update a student's profile. Returns True on success."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET full_name = ?, email = ? WHERE id = ?",
            (full_name, email, student_id),
        )
        conn.execute(
            """INSERT INTO students (user_id, class_name, phone)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET class_name = excluded.class_name,
                                                  phone = excluded.phone""",
            (student_id, class_name, phone),
        )
    return True

def verify_password(student_id: int, old_password: str) -> bool:
    """Check that *old_password* matches the stored hash for *student_id*."""
    from werkzeug.security import check_password_hash

    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (student_id,),
        ).fetchone()
    if not row:
        return False
    return check_password_hash(row["password_hash"], old_password)

def update_password(student_id: int, new_password_hash: str) -> bool:
    """Replace the password hash for *student_id*."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password_hash, student_id),
        )
    return True
