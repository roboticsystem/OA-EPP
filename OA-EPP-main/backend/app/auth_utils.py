import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-production-secret-key")
ALGORITHM = "HS256"


def create_token(data: dict, expires_hours: int = 2) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_student_token(token: str) -> dict:
    """解码学生 token，返回 {student_id, name}，失败抛出异常"""
    try:
        payload = decode_token(token)
        if payload.get("role") != "student":
            raise ValueError("not a student token")
        return payload
    except JWTError as e:
        raise ValueError(f"invalid token: {e}")


def verify_teacher_token(token: str) -> dict:
    """解码教师 token，返回 payload，失败抛出异常"""
    try:
        payload = decode_token(token)
        if payload.get("role") != "teacher":
            raise ValueError("not a teacher token")
        return payload
    except JWTError as e:
        raise ValueError(f"invalid token: {e}")
