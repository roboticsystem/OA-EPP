"""课程与章节状态管理 (F-S-010 + F-S-011)

使用 rx.session() 访问 Course / Chapter 模型。
"""

from __future__ import annotations

from typing import List, Optional

import reflex as rx
from sqlmodel import select

from oaepp.models.database import Chapter, Course


class CoursesState(rx.State):
    """课程主页状态 — F-S-010 课程列表 + F-S-011 章节明细"""

    # ── 课程列表 ──
    courses: List[dict] = []
    courses_loading: bool = False

    # ── 当前课程章节 ──
    current_course: Optional[dict] = None
    chapters: List[dict] = []
    chapters_loading: bool = False

    error_message: str = ""

    async def load_courses(self):
        """从数据库加载所有课程"""
        self.courses_loading = True
        self.courses = []
        self.error_message = ""
        try:
            with rx.session() as session:
                courses = session.exec(
                    select(Course).where(Course.status == "open")
                ).all()
                result = []
                for c in courses:
                    ch_count = len(session.exec(
                        select(Chapter).where(Chapter.course_id == c.id)
                    ).all())
                    result.append({
                        "id": c.id,
                        "code": c.code,
                        "name": c.name,
                        "term": c.term,
                        "status": c.status,
                        "total_chapters": ch_count,
                    })
                self.courses = result
        except Exception as e:
            self.error_message = f"加载课程失败: {e}"
        finally:
            self.courses_loading = False

    async def load_chapters(self, course_id: int):
        """加载某课程所有章节"""
        self.chapters_loading = True
        self.current_course = None
        self.chapters = []
        self.error_message = ""
        try:
            with rx.session() as session:
                course = session.exec(
                    select(Course).where(Course.id == course_id)
                ).first()
                if not course:
                    self.error_message = "课程不存在"
                    self.chapters_loading = False
                    return
                self.current_course = {
                    "id": course.id,
                    "code": course.code,
                    "name": course.name,
                    "term": course.term,
                }
                chapters = session.exec(
                    select(Chapter)
                    .where(Chapter.course_id == course_id)
                    .order_by(Chapter.chapter_no)
                ).all()
                self.chapters = [
                    {
                        "id": ch.id,
                        "chapter_no": ch.chapter_no,
                        "title": ch.title,
                        "chapter_type": self._detect_type(ch),
                    }
                    for ch in chapters
                ]
        except Exception as e:
            self.error_message = f"加载章节失败: {e}"
        finally:
            self.chapters_loading = False

    @staticmethod
    def _detect_type(chapter: Chapter) -> str:
        """根据章节内容猜测类型"""
        if chapter.chapter_no == 1:
            return "签到"
        if chapter.content_md and "<quiz" in chapter.content_md.lower():
            return "考试"
        return "作业"
