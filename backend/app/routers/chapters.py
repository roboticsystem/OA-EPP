"""
chapters.py — 课程与章节 API（F-S-011 章节内容浏览）
"""

from fastapi import APIRouter, HTTPException
from app.database import db

router = APIRouter()


@router.get("/api/courses")
def list_courses():
    """获取所有课程列表（含章节统计）"""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, semester, is_active FROM courses ORDER BY semester"
        ).fetchall()
        result = []
        for c in rows:
            ch_count = conn.execute(
                "SELECT COUNT(*) FROM chapters WHERE course_id=?", (c["id"],)
            ).fetchone()[0]
            # 计算章节完成数：status=已完成 的章节数
            done_count = conn.execute(
                "SELECT COUNT(*) FROM chapters WHERE course_id=? AND status='已完成'",
                (c["id"],)
            ).fetchone()[0]
            result.append({
                "id": c["id"],
                "title": c["title"],
                "semester": c["semester"],
                "is_active": c["is_active"],
                "total_chapters": ch_count,
                "completed_chapters": done_count,
            })
    return result


@router.get("/api/courses/{course_id}/chapters")
def list_chapters(course_id: str):
    """获取某课程的所有章节明细"""
    with db() as conn:
        course = conn.execute(
            "SELECT id, title, semester FROM courses WHERE id=?", (course_id,)
        ).fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        chapters = conn.execute(
            """SELECT id, course_id, chapter_no, title, filename, chapter_type,
                      deadline, status, grading_criteria
               FROM chapters
               WHERE course_id=?
               ORDER BY chapter_no""",
            (course_id,)
        ).fetchall()

    return {
        "course": dict(course),
        "chapters": [dict(c) for c in chapters],
    }


@router.get("/api/chapters/{chapter_id}")
def get_chapter(chapter_id: str):
    """获取单个章节详细信息"""
    with db() as conn:
        ch = conn.execute(
            """SELECT id, course_id, chapter_no, title, filename, file_path,
                      chapter_type, deadline, status, grading_criteria
               FROM chapters WHERE id=?""",
            (chapter_id,)
        ).fetchone()
        if not ch:
            raise HTTPException(status_code=404, detail="章节不存在")
    return dict(ch)
