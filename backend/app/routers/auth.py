from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from app.auth_utils import create_token, hash_password, verify_password, verify_student_token
from app.database import db

router = APIRouter()

MAX_FAILED_LOGIN = 5
LOCK_MINUTES = 5


class VerifyRequest(BaseModel):
    student_id: str
    exam_id: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


def _parse_locked_until(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


@router.post("/api/auth/login")
def login(req: LoginRequest):
    identifier = req.identifier.strip()
    password = req.password or ""
    if not identifier or not password:
        raise HTTPException(status_code=422, detail="学号/邮箱和密码不能为空")

    lookup = identifier.lower()
    with db() as conn:
        account = conn.execute(
            """
            SELECT a.student_id, a.password_hash, a.failed_attempts, a.locked_until,
                   s.name, s.class_name
            FROM student_accounts a
            JOIN students s ON s.student_id = a.student_id
            WHERE lower(a.student_id) = ? OR lower(a.email) = ?
            """,
            (lookup, lookup),
        ).fetchone()

        if not account:
            student = conn.execute(
                "SELECT name, student_id, class_name FROM students WHERE lower(student_id) = ?",
                (lookup,),
            ).fetchone()
            if not student:
                raise HTTPException(status_code=401, detail="学号/邮箱或密码错误")
            password_hash = hash_password(student["student_id"])
            conn.execute(
                "INSERT INTO student_accounts (student_id, password_hash) VALUES (?, ?)",
                (student["student_id"], password_hash),
            )
            account = conn.execute(
                "SELECT a.student_id, a.password_hash, a.failed_attempts, a.locked_until, s.name, s.class_name "
                "FROM student_accounts a JOIN students s ON s.student_id = a.student_id "
                "WHERE lower(a.student_id) = ? OR lower(a.email) = ?",
                (lookup, lookup),
            ).fetchone()

        locked_until = _parse_locked_until(account["locked_until"])
        now = datetime.utcnow()
        if locked_until and locked_until > now:
            remaining = int((locked_until - now).total_seconds() // 60) + 1
            raise HTTPException(
                status_code=403,
                detail=f"连续登录失败已达 {MAX_FAILED_LOGIN} 次，账户已暂时锁定 {remaining} 分钟"
            )

        if not verify_password(password, account["password_hash"]):
            failed_attempts = account["failed_attempts"] + 1
            if failed_attempts >= MAX_FAILED_LOGIN:
                new_locked_until = (now + timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds")
                conn.execute(
                    "UPDATE student_accounts SET failed_attempts = ?, locked_until = ? WHERE student_id = ?",
                    (failed_attempts, new_locked_until, account["student_id"]),
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"连续登录失败已达 {MAX_FAILED_LOGIN} 次，账户已锁定 {LOCK_MINUTES} 分钟"
                )

            conn.execute(
                "UPDATE student_accounts SET failed_attempts = ? WHERE student_id = ?",
                (failed_attempts, account["student_id"]),
            )
            raise HTTPException(status_code=401, detail="学号/邮箱或密码错误")

        conn.execute(
            "UPDATE student_accounts SET failed_attempts = 0, locked_until = '' WHERE student_id = ?",
            (account["student_id"],),
        )

        token = create_token(
            {
                "role": "student",
                "student_id": account["student_id"],
                "name": account["name"],
            },
            expires_hours=2,
        )

    return {
        "ok": True,
        "student_id": account["student_id"],
        "name": account["name"],
        "token": token,
    }


@router.get("/api/auth/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_student_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return {
        "student_id": payload["student_id"],
        "name": payload["name"],
    }


@router.post("/api/auth/logout")
def logout():
    return {"ok": True}


@router.post("/api/auth/verify")
def verify_identity(req: VerifyRequest):
    """
    核验学生身份并检查是否已提交成绩。
    适配远程 users + students + exams 表。
    """
    with db() as conn:
        student = conn.execute(
            "SELECT name, student_id, class_name FROM students WHERE student_id = %s",
            (req.student_id,)
        ).fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        exam = conn.execute(
            "SELECT id, title, is_active FROM exams WHERE id = %s",
            (req.exam_id,)
        ).fetchone()

        if not exam:
            # 如果考试不存在，仍然允许验证身份（返回 token），
            # 实际考试状态由前端根据列表接口判断
            pass

        if exam and not exam["is_active"]:
            raise HTTPException(status_code=403, detail="本次考试已关闭，无法答题")

        existing = conn.execute(
            "SELECT score, total, submitted_at FROM scores WHERE student_id = %s AND exam_id = %s",
            (req.student_id, req.exam_id)
        ).fetchone()

        if existing:
            return {
                "already_submitted": True,
                "name": student["name"],
                "score": float(existing["score"]) if existing["score"] else 0,
                "total": float(existing["total"]) if existing["total"] else 0,
                "submitted_at": existing["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if existing["submitted_at"] else None,
            }

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
