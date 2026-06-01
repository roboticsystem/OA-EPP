from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token
from datetime import datetime

router = APIRouter()


class VerifyRequest(BaseModel):
    student_id: int
    exam_id: int


@router.post("/api/auth/verify")
def verify_identity(req: VerifyRequest):
    """
    核验学生身份并检查是否已提交成绩。
    - 学号不存在 → 403
    - 已提交 → {already_submitted: true, score, total, submitted_at}
    - 未提交 → {already_submitted: false, token}
    """
    with db() as conn:
        student = conn.execute(
            "SELECT u.id, u.full_name, s.class_name FROM users u JOIN students s ON u.id = s.user_id WHERE u.id = %s AND u.role = 'student' AND u.is_active = 1",
            (req.student_id,)
        ).fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        exam = conn.execute(
            "SELECT id, title, start_at, end_at FROM exams WHERE id = %s",
            (req.exam_id,)
        ).fetchone()

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        now = datetime.now()
        if not (exam["start_at"] <= now <= exam["end_at"]):
            raise HTTPException(status_code=403, detail="本次考试不在开放时间内，无法答题")

        existing = conn.execute(
            "SELECT total_score, submitted_at FROM exam_attempts WHERE student_user_id = %s AND exam_id = %s AND status = 'submitted'",
            (req.student_id, req.exam_id)
        ).fetchone()

        if existing:
            return {
                "already_submitted": True,
                "name": student["full_name"],
                "score": existing["total_score"],
                "submitted_at": existing["submitted_at"],
            }

        token = create_token({
            "role": "student",
            "student_id": student["id"],
            "name": student["full_name"],
            "exam_id": req.exam_id,
        }, expires_hours=2)

        return {
            "already_submitted": False,
            "name": student["full_name"],
            "token": token,
        }