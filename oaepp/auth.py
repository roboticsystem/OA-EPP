"""OA-EPP 认证模块 — JWT token 验证

提供 verify_teacher / verify_student 函数，供 routers/notice.py 的 Depends 使用。
"""
import os
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-production-secret-key")
ALGORITHM = "HS256"


def create_token(data: dict, expires_hours: int = 2) -> str:
    """创建 JWT token"""
    try:
        from jose import jwt
    except ImportError:
        import jwt
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    try:
        from jose import jwt
    except ImportError:
        import jwt
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_student(token: str) -> dict:
    """验证学生 token，返回 {student_id, name, role}"""
    payload = decode_token(token)
    if payload.get("role") != "student":
        raise ValueError("not a student token")
    return payload


def verify_teacher(token: str) -> dict:
    """验证教师 token，返回 payload"""
    payload = decode_token(token)
    if payload.get("role") != "teacher":
        raise ValueError("not a teacher token")
    return payload
