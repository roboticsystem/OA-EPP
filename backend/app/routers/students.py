from fastapi import APIRouter, Query, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/exam_students/search")
def search_students(q: str = Query(..., min_length=1)):
    """按姓名（汉字或拼音）模糊搜索学生，最多返回 10 条"""
    q = q.strip().lower()
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, student_id, class_name FROM exam_students
            WHERE LOWER(name) LIKE %s
               OR LOWER(pinyin) LIKE %s
               OR LOWER(pinyin_abbr) LIKE %s
            ORDER BY name
            LIMIT 10
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = cur.fetchall()
        cur.close()
    return [dict(r) for r in rows]
