"""ORM 模型层 — 映射到远程 MySQL oaepp_dev 数据库现有表

使用方式：
    from oaepp.models import Course, Enrollment
    with rx.session() as session:
        courses = session.exec(select(Course)).all()

与 database.py 的关系：
    - database.py → aiomysql 原始 SQL（已有代码使用）
    - models/     → Reflex ORM / SQLModel（新功能优先使用）
    - 两套连接独立并存，按需选择
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field


# ═══════════════════════════════════════════════════════════════════════════
#  用户相关
# ═══════════════════════════════════════════════════════════════════════════

class User(SQLModel, table=True):
    """用户模型 — 映射到 users 表"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    role: str = Field(default="student")            # enum: student, teacher, admin
    student_no: Optional[str] = Field(default=None, index=True)
    email: str = Field(default="")
    password_hash: str = Field(default="")
    full_name: str = Field(default="")
    avatar_url: Optional[str] = Field(default=None)
    login_fail_cnt: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Student(SQLModel, table=True):
    """学生扩展信息 — 映射到 students 表"""
    __tablename__ = "students"

    user_id: int = Field(primary_key=True)
    class_name: str = Field(default="")
    phone: Optional[str] = Field(default=None)


class Teacher(SQLModel, table=True):
    """教师扩展信息 — 映射到 teachers 表"""
    __tablename__ = "teachers"

    user_id: int = Field(primary_key=True)
    title: Optional[str] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════
#  课程相关
# ═══════════════════════════════════════════════════════════════════════════

class Course(SQLModel, table=True):
    """课程模型 — 映射到 courses 表"""
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    name: str = Field(default="")
    term: str = Field(default="")
    status: str = Field(default="open")             # enum: draft, open, closed
    created_at: datetime = Field(default_factory=datetime.now)


class Chapter(SQLModel, table=True):
    """章节模型 — 映射到 chapters 表"""
    __tablename__ = "chapters"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    chapter_no: int = Field(default=0)
    title: str = Field(default="")
    content_md: Optional[str] = Field(default=None)


class Enrollment(SQLModel, table=True):
    """选课记录 — 映射到 enrollments 表"""
    __tablename__ = "enrollments"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    enrolled_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
#  作业相关
# ═══════════════════════════════════════════════════════════════════════════

class Assignment(SQLModel, table=True):
    """作业/任务 — 映射到 assignments 表"""
    __tablename__ = "assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    chapter_id: Optional[int] = Field(
        default=None, foreign_key="chapters.id", index=True
    )
    title: str = Field(default="")
    description_md: Optional[str] = Field(default=None)
    allow_resubmit: bool = Field(default=True)
    late_policy: str = Field(default="deny")        # enum: allow, deny, penalty
    deadline: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Submission(SQLModel, table=True):
    """提交记录 — 映射到 submissions 表"""
    __tablename__ = "submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(foreign_key="assignments.id", index=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    version_no: int = Field(default=1)
    file_url: Optional[str] = Field(default=None)
    text_content: Optional[str] = Field(default=None)
    is_late: bool = Field(default=False)
    grading_status: str = Field(default="pending")  # enum: pending, graded, returned
    allow_resubmit_override: Optional[bool] = Field(default=None)
    submitted_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
#  考试相关
# ═══════════════════════════════════════════════════════════════════════════

class Exam(SQLModel, table=True):
    """考试 — 映射到 exams 表"""
    __tablename__ = "exams"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    title: str = Field(default="")
    exam_type: str = Field(default="quiz")          # enum: quiz, midterm, final, practice
    start_at: datetime = Field(default_factory=datetime.now)
    end_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id", index=True)


class ExamQuestion(SQLModel, table=True):
    """考试题目 — 映射到 exam_questions 表"""
    __tablename__ = "exam_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id", index=True)
    qtype: str = Field(default="single")            # enum: single, multi, blank, short
    content: str = Field(default="")
    options_json: Optional[str] = Field(default=None)
    answer_key: Optional[str] = Field(default=None)
    score: Decimal = Field(default=Decimal("0"))
    sort_no: int = Field(default=1)


class ExamAttempt(SQLModel, table=True):
    """考试答卷 — 映射到 exam_attempts 表"""
    __tablename__ = "exam_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id", index=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="draft")            # enum: draft, submitted, graded
    total_score: Optional[Decimal] = Field(default=None)
    submitted_at: Optional[datetime] = Field(default=None)


class ExamAnswer(SQLModel, table=True):
    """考试答题 — 映射到 exam_answers 表"""
    __tablename__ = "exam_answers"

    id: Optional[int] = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="exam_attempts.id", index=True)
    question_id: int = Field(foreign_key="exam_questions.id", index=True)
    answer_text: Optional[str] = Field(default=None)
    score: Optional[Decimal] = Field(default=None)
    graded_by: Optional[int] = Field(default=None, foreign_key="users.id")


# ═══════════════════════════════════════════════════════════════════════════
#  考勤相关
# ═══════════════════════════════════════════════════════════════════════════

class AttendanceSession(SQLModel, table=True):
    """签到场次 — 映射到 attendance_sessions 表"""
    __tablename__ = "attendance_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    created_by: int = Field(foreign_key="users.id", index=True)
    expires_at: datetime = Field(default_factory=datetime.now)
    geo_lat: Optional[Decimal] = Field(default=None)
    geo_lng: Optional[Decimal] = Field(default=None)
    geo_radius_m: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


class AttendanceRecord(SQLModel, table=True):
    """签到记录 — 映射到 attendance_records 表"""
    __tablename__ = "attendance_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="attendance_sessions.id", index=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="present")          # enum: present, late, absent
    checkin_at: Optional[datetime] = Field(default=None)
    geo_hash: Optional[str] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════
#  成绩相关
# ═══════════════════════════════════════════════════════════════════════════

class ScoreItem(SQLModel, table=True):
    """成绩条目 — 映射到 score_items 表"""
    __tablename__ = "score_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    score_type: str = Field(default="exam")         # enum: attendance, exam, code, pr
    ref_id: Optional[int] = Field(default=None)
    score: Decimal = Field(default=Decimal("0"))
    scored_by: int = Field(foreign_key="users.id")
    scored_at: datetime = Field(default_factory=datetime.now)


class GradingRecord(SQLModel, table=True):
    """批改记录 — 映射到 grading_records 表"""
    __tablename__ = "grading_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int = Field(unique=True, foreign_key="submissions.id")
    graded_by: int = Field(foreign_key="users.id")
    attendance_score: Optional[Decimal] = Field(default=None)
    exam_score: Optional[Decimal] = Field(default=None)
    code_score: Optional[Decimal] = Field(default=None)
    pr_score: Optional[Decimal] = Field(default=None)
    total_score: Optional[Decimal] = Field(default=None)
    comment_md: Optional[str] = Field(default=None)
    allow_resubmit: bool = Field(default=False)
    graded_at: datetime = Field(default_factory=datetime.now)


class GradeWeightConfig(SQLModel, table=True):
    """成绩权重配置 — 映射到 grade_weight_configs 表"""
    __tablename__ = "grade_weight_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(unique=True, foreign_key="courses.id")
    attendance_weight: Decimal = Field(default=Decimal("20.00"))
    exam_weight: Decimal = Field(default=Decimal("30.00"))
    code_weight: Decimal = Field(default=Decimal("30.00"))
    pr_weight: Decimal = Field(default=Decimal("20.00"))
    updated_by: int = Field(foreign_key="users.id")
    updated_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
#  反馈 / 通知
# ═══════════════════════════════════════════════════════════════════════════

class Feedback(SQLModel, table=True):
    """成绩反馈 — 映射到 feedbacks 表"""
    __tablename__ = "feedbacks"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    teacher_user_id: int = Field(foreign_key="users.id")
    source_type: str = Field(default="manual")      # enum: assignment, exam, pr, manual
    source_id: Optional[int] = Field(default=None)
    content: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)


class Notification(SQLModel, table=True):
    """通知消息 — 映射到 notifications 表"""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(default="")
    body: str = Field(default="")
    category: str = Field(default="announcement")    # enum: announcement, deadline, grade, system, graded
    source_ref: Optional[str] = Field(default=None)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
#  GitHub / PR 相关
# ═══════════════════════════════════════════════════════════════════════════

class GithubBinding(SQLModel, table=True):
    """GitHub 绑定 — 映射到 github_bindings 表"""
    __tablename__ = "github_bindings"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_user_id: int = Field(unique=True, foreign_key="users.id")
    github_username: str = Field(unique=True, default="")
    github_name: Optional[str] = Field(default=None)
    verify_status: str = Field(default="pending")   # enum: pending, approved, rejected
    verified_at: Optional[datetime] = Field(default=None)
    verified_by: Optional[int] = Field(default=None)


class PrRecord(SQLModel, table=True):
    """PR 记录 — 映射到 pr_records 表"""
    __tablename__ = "pr_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_user_id: int = Field(foreign_key="users.id", index=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    issue_no: Optional[int] = Field(default=None)
    pr_number: int = Field(default=0)
    pr_state: str = Field(default="open")           # enum: open, merged, closed
    quality_score: Optional[Decimal] = Field(default=None)
    merged_at: Optional[datetime] = Field(default=None)


class CommitlintConfig(SQLModel, table=True):
    """Commitlint 配置 — 映射到 commitlint_configs 表"""
    __tablename__ = "commitlint_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(unique=True, foreign_key="courses.id")
    rule_set: str = Field(default="conventional")   # enum: conventional, custom
    header_max_len: int = Field(default=100)
    subject_min_len: int = Field(default=5)
    type_enum_json: Optional[str] = Field(default=None)
    enabled: bool = Field(default=False)
    config_version: int = Field(default=1)
    updated_by: int = Field(foreign_key="users.id")
    updated_at: datetime = Field(default_factory=datetime.now)


class ReqDocument(SQLModel, table=True):
    """需求文档 — 映射到 req_documents 表 (F-T-006)"""
    __tablename__ = "req_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    title: str = Field(default="")
    content_md: Optional[str] = Field(default=None)
    status: str = Field(default="draft")            # enum: draft, sealed
    version_no: int = Field(default=1)
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
