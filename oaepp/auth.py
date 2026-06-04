"""OA-EPP 认证模块

提供 JWT token 的创建和验证功能。
"""
import os
from datetime import datetime, timedelta
from typing import Optional

try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None
    JWTError = Exception

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-production-secret-key")
ALGORITHM = "HS256"


def create_token(data: dict, expires_hours: int = 2) -> str:
    """创建 JWT token"""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_teacher(token: str) -> dict:
    """验证教师 token"""
    payload = decode_token(token)
    if payload.get("role") != "teacher":
        raise ValueError("not a teacher token")
    return payload


def verify_student(token: str) -> dict:
    """验证学生 token，返回 {student_id, name}"""
    payload = decode_token(token)
    if payload.get("role") != "student":
        raise ValueError("not a student token")
    return payload


def get_student_from_token(authorization: Optional[str]) -> Optional[dict]:
    """从 Authorization header 中提取学生信息"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_student(token)
    except (ValueError, JWTError):
        return None


def require_teacher(authorization: Optional[str]):
    """验证教师 token，失败抛出异常"""
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher(token)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="无效的登录凭证")
