"""
课程状态管理 (F-S-010)
提供学生课程加载、进度统计、课程选择等功能

映射到远程 MySQL oaepp_dev 现有表结构：
  - enrollments  → 学生选课记录
  - courses      → 课程信息
  - chapters     → 章节（用于统计章节数）
  - assignments  → 作业/任务（用于统计任务数、截止日期）
  - submissions  → 提交记录（用于统计完成数）
"""
from datetime import datetime
from typing import List, Optional

import os as _os

import reflex as rx
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.sql.functions import count

# 优先相对导入（运行在 oaepp/ 目录内），fallback 绝对导入（运行在仓库根目录）
try:
    from models.database import (
        Course, Chapter, Enrollment,
        Assignment, Submission,
    )
except ImportError:
    from oaepp.models.database import (
        Course, Chapter, Enrollment,
        Assignment, Submission,
    )


class CourseProgress(BaseModel):
    """课程进度数据结构"""
    course_id: int
    course_code: str
    course_name: str
    total_chapters: int
    completed_tasks: int
    total_tasks: int
    next_due_date_str: str = ""  # 格式化后的截止日期字符串
    has_due_date: bool = False  # 是否有截止日期
    status: str  # active, completed, dropped
    progress_percentage: int  # 0-100


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
                try:
                    from states.auth_state import AuthState  # 本地运行
                except ImportError:
                    from oaepp.states.auth_state import AuthState  # 容器运行
                student_id = AuthState.current_student_id

            if not student_id:
                # 测试环境：从环境变量获取默认测试学生 ID
                student_id = int(_os.environ.get(
                    "OAEPP_TEST_STUDENT_ID", "0"
                ))
            if not student_id:
                self.error_message = "未找到学生信息"
                return

            with rx.session() as session:
                # 查询学生选课记录（enrollments 表用 student_user_id）
                enrollments = session.exec(
                    select(Enrollment).where(
                        Enrollment.student_user_id == student_id
                    )
                ).all()

                courses_data: List[CourseProgress] = []

                for enr in enrollments:
                    # 获取课程信息
                    course = session.exec(
                        select(Course).where(Course.id == enr.course_id)
                    ).first()

                    if not course:
                        continue

                    # 统计该课程的总章节数
                    total_chapters = session.exec(
                        select(count(Chapter.id)).where(
                            Chapter.course_id == course.id
                        )
                    ).first()

                    # 统计该课程的总任务数（通过 assignments 表）
                    total_tasks = session.exec(
                        select(count(Assignment.id)).where(
                            Assignment.course_id == course.id
                        )
                    ).first()

                    # 统计该学生在该课程的已完成任务数
                    # 通过 submissions 表 JOIN assignments，按 grading_status = 'graded' 计数
                    completed_tasks = session.exec(
                        select(count(Submission.id))
                        .join(
                            Assignment,
                            Submission.assignment_id == Assignment.id,
                        )
                        .where(
                            and_(
                                Assignment.course_id == course.id,
                                Submission.student_user_id == student_id,
                                Submission.grading_status == "graded",
                            )
                        )
                    ).first()

                    # 获取该课程下一个截止任务
                    now = datetime.now()
                    next_due = session.exec(
                        select(Assignment)
                        .where(
                            and_(
                                Assignment.course_id == course.id,
                                Assignment.deadline > now,
                            )
                        )
                        .order_by(Assignment.deadline)
                    ).first()

                    completed_count = completed_tasks or 0
                    total_count = total_tasks or 0
                    progress_pct = (
                        int(completed_count / total_count * 100)
                        if total_count > 0 else 0
                    )

                    # 课程状态映射: courses.status enum('draft','open','closed')
                    if course.status == "closed":
                        display_status = "completed"
                    elif course.status == "draft":
                        display_status = "draft"
                    else:
                        display_status = "active"

                    course_progress = CourseProgress(
                        course_id=course.id,
                        course_code=course.code,
                        course_name=course.name,
                        total_chapters=total_chapters or 0,
                        completed_tasks=completed_count,
                        total_tasks=total_count,
                        next_due_date_str=(
                            next_due.deadline.strftime("%Y-%m-%d %H:%M")
                            if next_due and next_due.deadline else ""
                        ),
                        has_due_date=bool(
                            next_due and next_due.deadline
                        ),
                        status=display_status,
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

    # ── TDD 兼容层：对齐 tests/reflex/test_F_S_010_course_home.py ─────

    @property
    def is_loading(self) -> bool:
        """TDD 兼容别名 → self.loading"""
        return self.loading

    async def load_courses(self):
        """TDD 兼容方法 → self.load_student_courses()"""
        await self.load_student_courses()
