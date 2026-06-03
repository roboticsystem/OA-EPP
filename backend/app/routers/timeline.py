from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import db

router = APIRouter()


@router.get("/api/timeline")
def get_timeline(
    student_id: str = Query(...),
    course: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取学生学习时间线事件"""
    with db() as conn:
        student = conn.execute(
            "SELECT name, student_id, class_name FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        sql = "SELECT * FROM timeline_events WHERE student_id = ?"
        params = [student_id]

        if course:
            sql += " AND course = ?"
            params.append(course)
        if start_date:
            sql += " AND event_time >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND event_time <= ?"
            params.append(end_date)

        sql += " ORDER BY event_time DESC"

        events = [dict(r) for r in conn.execute(sql, params).fetchall()]

    return {
        "student": dict(student),
        "events": events,
        "total": len(events),
    }
