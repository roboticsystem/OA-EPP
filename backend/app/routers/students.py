from fastapi import APIRouter, Query, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/students/search")
def search_students(q: str = Query(..., min_length=1)):
    q = q.strip().lower()
    with db() as conn:
        rows = conn.execute("""
            SELECT u.full_name AS name, u.student_no AS student_id, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.role = 'student'
              AND (LOWER(u.full_name) LIKE %s OR LOWER(u.student_no) LIKE %s)
            ORDER BY u.full_name
            LIMIT 10
        """, (f"%{q}%", f"%{q}%")).fetchall()
    return [dict(r) for r in rows]
