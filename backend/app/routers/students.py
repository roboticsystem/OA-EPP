from fastapi import APIRouter, Query, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/students/search")
def search_students(q: str = Query(..., min_length=1)):
    """按姓名或学号模糊搜索学生（适配远程 users + students 表）"""
    q = q.strip()
    with db() as conn:
        rows = conn.execute("""
            SELECT name, student_id, class_name FROM students
            WHERE lower(name) LIKE %s
               OR lower(pinyin) LIKE %s
               OR lower(pinyin_abbr) LIKE %s
            ORDER BY name
            LIMIT 10
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return rows
