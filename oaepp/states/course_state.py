"""
课程状态管理 (F-S-010)
提供学生课程加载、进度统计、课程选择等功能
"""
from datetime import datetime
from typing import List, Optional

import reflex as rx
from sqlalchemy import select, and_
from sqlalchemy.sql.functions import count
from oaepp.models.database import (
    Course, Chapter, Task,
    StudentCourse, TaskCompletion
)


class CourseProgress(rx.Base):
    """课程进度数据结构"""
    course_id: int
    course_code: str
    course_name: str
    total_chapters: int
    completed_tasks: int
    total_tasks: int
    next_due_date_str: str = ""  # 格式化后的截止日期字符串，用于页面展示
    has_due_date: bool = False  # 是否有截止日期
    status: str  # active, completed, dropped
    progress_percentage: float  # 0-100


class CourseState(rx.State):
    """课程状态管理"""
    # 课程数据
    courses: List[CourseProgress] = []
    selected_course: Optional[CourseProgress] = None
    loading: bool = False
    error_message: str = ""

    async def load_student_courses(self, student_id: int = 0):
        """加载学生已选课程及进度"""
        try:
            self.loading = True
            self.error_message = ""

            # 如果没有传入 student_id，使用 AuthState 中的值
            if student_id == 0:
                from oaepp.states.auth_state import AuthState
                student_id = AuthState.current_student_id

            if not student_id:
                self.error_message = "未找到学生信息"
                return

            # 获取学生的课程列表
            with rx.session() as session:
                # 查询学生选课记录
                student_courses = session.exec(
                    select(StudentCourse).where(
                        StudentCourse.student_id == student_id
                    )
                ).all()

                courses_data: List[CourseProgress] = []

                for sc in student_courses:
                    # 获取课程信息
                    course = session.exec(
                        select(Course).where(Course.id == sc.course_id)
                    ).first()

                    if not course:
                        continue

                    # 统计该课程的总任务数（通过 Chapter 关联）
                    total_tasks = session.exec(
                        select(count(Task.id))
                        .join(Chapter, Task.chapter_id == Chapter.id)
                        .where(Chapter.course_id == course.id)
                    ).first()

                    # 统计该学生在该课程的已完成任务数
                    completed_tasks = session.exec(
                        select(count(TaskCompletion.id))
                        .join(Task, TaskCompletion.task_id == Task.id)
                        .join(Chapter, Task.chapter_id == Chapter.id)
                        .where(
                            and_(
                                Chapter.course_id == course.id,
                                TaskCompletion.student_id == student_id,
                                TaskCompletion.status == "completed",
                            )
                        )
                    ).first()

                    # 获取该课程下一个截止任务
                    next_due = session.exec(
                        select(Task)
                        .join(Chapter, Task.chapter_id == Chapter.id)
                        .where(
                            and_(
                                Chapter.course_id == course.id,
                                Task.due_date.isnot(None),
                                Task.due_date > datetime.now(),
                            )
                        )
                        .order_by(Task.due_date)
                    ).first()

                    completed_count = completed_tasks or 0
                    total_count = total_tasks or 0
                    progress_pct = (
                        (completed_count / total_count * 100)
                        if total_count > 0 else 0
                    )

                    course_progress = CourseProgress(
                        course_id=course.id,
                        course_code=course.code,
                        course_name=course.name,
                        total_chapters=course.total_chapters,
                        completed_tasks=completed_count,
                        total_tasks=total_count,
                        next_due_date_str=(
                            next_due.due_date.strftime("%Y-%m-%d %H:%M")
                            if next_due and next_due.due_date else ""
                        ),
                        has_due_date=bool(next_due and next_due.due_date),
                        status=sc.status,
                        progress_percentage=progress_pct,
                    )
                    courses_data.append(course_progress)

                self.courses = courses_data

        except Exception as e:
            self.error_message = f"加载课程数据失败: {str(e)}"
        finally:
            self.loading = False

    def select_course(self, course_id: int):
        """选择查看某门课程"""
        for course in self.courses:
            if course.course_id == course_id:
                self.selected_course = course
                break

    async def refresh_courses(self):
        """刷新课程数据"""
        await self.load_student_courses()
