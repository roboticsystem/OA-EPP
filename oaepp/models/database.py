"""
数据库模型定义 - 基于已有MySQL表结构
"""
import reflex as rx
from sqlmodel import Field
from typing import Optional
from datetime import datetime


class User(rx.Model, table=True):
    """用户表 - 对应users表"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str = Field(sa_column_kwargs={"comment": "角色: student/teacher/admin"})
    student_no: Optional[str] = Field(default=None, max_length=32)
    email: str = Field(max_length=128)
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=64)
    is_active: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Student(rx.Model, table=True):
    """学生信息表 - 对应students表"""
    __tablename__ = "students"
    
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    class_name: str = Field(max_length=64)
    phone: Optional[str] = Field(default=None, max_length=32)


class GithubBinding(rx.Model, table=True):
    """GitHub绑定表 - 对应github_bindings表"""
    __tablename__ = "github_bindings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_user_id: int = Field(foreign_key="students.user_id")
    github_username: str = Field(max_length=64)
    github_name: Optional[str] = Field(default=None, max_length=128)
    verify_status: str = Field(default="pending", max_length=20)  # pending/approved/rejected
    verified_at: Optional[datetime] = Field(default=None)
    verified_by: Optional[int] = Field(default=None, foreign_key="teachers.user_id")
