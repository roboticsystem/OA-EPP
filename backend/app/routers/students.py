from fastapi import APIRouter, Query, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/students/search")
def search_students(q: str = Query(..., min_length=1)):
    """按姓名（汉字或拼音）模糊搜索学生，最多返回 10 条"""
    q = q.strip().lower()
    with db() as conn:
        rows = conn.execute("""
            SELECT u.id AS student_id, u.full_name AS name, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.role = 'student' AND u.is_active = 1
              AND (LOWER(u.full_name) LIKE %s)
            ORDER BY u.full_name
            LIMIT 10
        """, (f"%{q}%",)).fetchall()
    return [dict(r) for r in rows]