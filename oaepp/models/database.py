"""F-T-012 成绩权重配置 — 数据库模型

- WeightScheme: 按课程独立的权重方案
- WeightAuditLog: 不可删除的审计日志
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class WeightScheme(SQLModel, table=True):
    __tablename__ = "weight_schemes"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: str = Field(default="default", index=True)
    name: str = Field(default="默认方案")
    attendance_weight: float = Field(default=25.0)
    exam_weight: float = Field(default=25.0)
    code_weight: float = Field(default=25.0)
    pr_weight: float = Field(default=25.0)
    created_by: str = Field(default="teacher")
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def weights_tuple(self):
        return (
            self.attendance_weight,
            self.exam_weight,
            self.code_weight,
            self.pr_weight,
        )


class WeightAuditLog(SQLModel, table=True):
    __tablename__ = "weight_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    scheme_id: Optional[int] = Field(default=None, foreign_key="weight_schemes.id")
    modified_by: str = Field(default="teacher")
    modified_at: datetime = Field(default_factory=datetime.now)
    old_attendance: float
    old_exam: float
    old_code: float
    old_pr: float
    new_attendance: float
    new_exam: float
    new_code: float
    new_pr: float
