from fastapi import APIRouter, Query, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/students/search")
def search_students(q: str = Query(..., min_length=1)):
    """按姓名（汉字或拼音）模糊搜索学生，最多返回 10 条"""
    q = q.strip().lower()
    with db() as conn:
        rows = conn.execute("""
            SELECT name, student_id, class_name FROM students
            WHERE lower(name) LIKE ?
               OR lower(pinyin) LIKE ?
               OR lower(pinyin_abbr) LIKE ?
            ORDER BY name
            LIMIT 10
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return [dict(r) for r in rows]
