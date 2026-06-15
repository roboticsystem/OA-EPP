"""ORM 模型层 — 统一导出

学生用法：
    from oaepp.models import User, Course, Enrollment, Assignment
"""
from .database import (
    User,
    Student,
    Teacher,
    Course,
    Chapter,
    Enrollment,
    Assignment,
    Submission,
    Exam,
    ExamQuestion,
    ExamAttempt,
    ExamAnswer,
    AttendanceSession,
    AttendanceRecord,
    ScoreItem,
    GradingRecord,
    GradeWeightConfig,
    Feedback,
    Notification,
    PrRecord,
    GithubBinding,
    CommitlintConfig,
)
