"""
作业提交子系统 - JWT 认证工具
"""
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("环境变量 JWT_SECRET 未设置，请设置后启动")

ALGORITHM = "HS256"

# 学生身份验证：通过学号调用平台统一接口核验
# 此处仅提供 Token 创建和验证的工具函数


def create_token(data: dict, expires_hours: int = 2) -> str:
    """创建 JWT Token"""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT Token"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_student_token(token: str) -> dict:
    """验证学生 Token"""
    try:
        payload = decode_token(token)
        if payload.get("role") != "student":
            raise ValueError("not a student token")
        return payload
    except JWTError as e:
        raise ValueError(f"invalid token: {e}")


def verify_teacher_token(token: str) -> dict:
    """验证教师 Token"""
    try:
        payload = decode_token(token)
        if payload.get("role") != "teacher":
            raise ValueError("not a teacher token")
        return payload
    except JWTError as e:
        raise ValueError(f"invalid token: {e}")
