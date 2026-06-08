from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_password, hash_password, verify_token

router = APIRouter()


class ProfileUpdate(BaseModel):
    full_name: str
    class_name: str
    phone: str = ""


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


def _require_student(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if payload.get("role") != "student":
        raise HTTPException(status_code=403, detail="仅限学生操作")
    return payload


def _row(conn, sql, params):
    r = conn.execute(sql, params).fetchone()
    return dict(r._mapping) if r else None


@router.get("/api/student/profile")
def get_profile(authorization: Optional[str] = Header(None)):
    payload = _require_student(authorization)
    user_id = payload["user_id"]

    with db() as conn:
        user = _row(conn,
            "SELECT full_name, email, student_no FROM users WHERE id = %s",
            (user_id,))
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        student = _row(conn,
            "SELECT class_name, phone FROM students WHERE user_id = %s",
            (user_id,))

    return {
        "full_name": user["full_name"],
        "email": user["email"],
        "student_no": user["student_no"] or "",
        "class_name": student["class_name"] if student else "",
        "phone": student["phone"] if student else "",
    }


@router.put("/api/student/profile")
def update_profile(req: ProfileUpdate, authorization: Optional[str] = Header(None)):
    payload = _require_student(authorization)
    user_id = payload["user_id"]
    full_name = req.full_name.strip()
    class_name = req.class_name.strip()
    phone = req.phone.strip()

    if not full_name:
        raise HTTPException(status_code=422, detail="姓名不能为空")

    with db() as conn:
        conn.execute(
            "UPDATE users SET full_name = %s WHERE id = %s",
            (full_name, user_id))
        conn.execute(
            "INSERT INTO students (user_id, class_name, phone) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE class_name = VALUES(class_name), phone = VALUES(phone)",
            (user_id, class_name, phone))

    return {"ok": True, "full_name": full_name, "class_name": class_name, "phone": phone}


@router.put("/api/student/password")
def change_password(req: PasswordUpdate, authorization: Optional[str] = Header(None)):
    payload = _require_student(authorization)
    user_id = payload["user_id"]

    if len(req.new_password) < 6:
        raise HTTPException(status_code=422, detail="新密码长度不能少于6位")

    with db() as conn:
        user = _row(conn,
            "SELECT password_hash FROM users WHERE id = %s",
            (user_id,))

    if not verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码错误")

    new_hash = hash_password(req.new_password)
    with db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, user_id))

    return {"ok": True}
