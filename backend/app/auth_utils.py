import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException

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
    except JWTError:
        raise ValueError("invalid token")


def verify_teacher_token(token: str) -> dict:
    """解码教师 token，返回 payload，失败抛出异常"""
    try:
        payload = decode_token(token)
        if payload.get("role") != "teacher":
            raise ValueError("not a teacher token")
        return payload
    except JWTError:
        raise ValueError("invalid token")


def require_teacher(authorization: Optional[str]):
    """提取并验证教师 Bearer token，失败抛出 HTTPException"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")


def get_student_from_token(authorization: Optional[str]) -> Optional[dict]:
    """解码学生 token，返回 {student_id, name}，失败返回 None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_student_token(token)
    except ValueError:
        return None
