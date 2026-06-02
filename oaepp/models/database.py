import reflex as rx
from typing import Optional
from datetime import datetime


class Student(rx.Model, table=True):
    """学生模型"""
    student_id: str = rx.Field(unique=True, index=True)
    name: str
    email: Optional[str] = None
    class_name: Optional[str] = None
    created_at: datetime = rx.Field(default_factory=datetime.now)


class Course(rx.Model, table=True):
    """课程模型"""
    code: str = rx.Field(unique=True, index=True)  # 课程代码，如 ENG-PRAC-01
    name: str  # 课程名称，如 工程实践1
    description: Optional[str] = None
    instructor: Optional[str] = None
    total_chapters: int = 0  # 总章节数
    is_active: bool = True
    created_at: datetime = rx.Field(default_factory=datetime.now)


class Chapter(rx.Model, table=True):
    """章节模型"""
    course_id: int = rx.Field(foreign_key="course.id", index=True)
    chapter_num: int  # 章节号
    title: str  # 章节标题
    description: Optional[str] = None
    order: int = 0  # 排序
    created_at: datetime = rx.Field(default_factory=datetime.now)


class Task(rx.Model, table=True):
    """任务模型"""
    chapter_id: int = rx.Field(foreign_key="chapter.id", index=True)
    title: str  # 任务名称
    description: Optional[str] = None
    task_type: str  # 任务类型：reading, practice, quiz, project
    due_date: Optional[datetime] = None  # 截止日期
    order: int = 0  # 排序
    created_at: datetime = rx.Field(default_factory=datetime.now)


class StudentCourse(rx.Model, table=True):
    """学生选课关系"""
    student_id: int = rx.Field(foreign_key="student.id", index=True)
    course_id: int = rx.Field(foreign_key="course.id", index=True)
    enrollment_date: datetime = rx.Field(default_factory=datetime.now)
    status: str = "active"  # active, completed, dropped


class TaskCompletion(rx.Model, table=True):
    """任务完成记录"""
    student_id: int = rx.Field(foreign_key="student.id", index=True)
    task_id: int = rx.Field(foreign_key="task.id", index=True)
    completed_at: datetime = rx.Field(default_factory=datetime.now)
    score: Optional[float] = None
    status: str = "completed"  # completed, pending, overdue
