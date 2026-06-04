from datetime import datetime as _dt
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token, verify_password, verify_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyRequest(BaseModel):
    student_id: str
    exam_id: str


def _require_auth(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _row(conn, sql, params):
    r = conn.execute(sql, params).fetchone()
    if r is None:
        return None
    if isinstance(r, dict):
        return r
    return dict(r._mapping)


@router.post("/api/auth/login")
def login(req: LoginRequest):
    with db() as conn:
        user = _row(conn,
            "SELECT id, role, email, password_hash, full_name, is_active, locked_until "
            "FROM users WHERE email = %s",
            (req.email,))

    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    if user["locked_until"] and user["locked_until"] > _dt.utcnow():
        raise HTTPException(status_code=423, detail="账号已被锁定，请稍后再试")

    if not verify_password(req.password, user["password_hash"]):
        with db() as conn:
            conn.execute(
                "UPDATE users SET login_fail_cnt = login_fail_cnt + 1 WHERE id = %s",
                (user["id"],))
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    with db() as conn:
        conn.execute(
            "UPDATE users SET login_fail_cnt = 0, locked_until = NULL WHERE id = %s",
            (user["id"],))

    token = create_token({
        "user_id": user["id"],
        "role": user["role"],
        "email": user["email"],
        "full_name": user["full_name"],
    }, expires_hours=8)

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "role": user["role"],
            "email": user["email"],
            "full_name": user["full_name"],
        }
    }


@router.get("/api/auth/me")
def get_me(authorization: Optional[str] = Header(None)):
    payload = _require_auth(authorization)
    with db() as conn:
        user = _row(conn,
            "SELECT id, role, email, full_name, student_no FROM users WHERE id = %s",
            (payload["user_id"],))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/api/auth/logout")
def logout():
    return {"ok": True}


@router.post("/api/auth/verify")
def verify_identity(req: VerifyRequest):
    """
    核验学生身份并检查是否已提交成绩，返回 token 供参加考试。
    """
    with db() as conn:
        student = _row(conn,
            "SELECT u.full_name as name, u.student_no as student_id, s.class_name, u.id as user_id "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.student_no = %s AND u.role = 'student'",
            (req.student_id,))

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        exam = _row(conn,
            "SELECT id, title FROM exams WHERE id = %s",
            (req.exam_id,))

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        token = create_token({
            "role": "student",
            "student_id": student["student_id"],
            "name": student["name"],
            "exam_id": req.exam_id,
        }, expires_hours=2)

        return {
            "already_submitted": False,
            "name": student["name"],
            "token": token,
        }
