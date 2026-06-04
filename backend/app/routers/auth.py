from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token

router = APIRouter()


class VerifyRequest(BaseModel):
    student_id: str
    exam_id: str


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
            "SELECT name, student_id, class_name FROM students WHERE student_id = ?",
            (req.student_id,)
        ).fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        exam = conn.execute(
            "SELECT id, title, is_active FROM exams WHERE id = ?",
            (req.exam_id,)
        ).fetchone()

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        if not exam["is_active"]:
            raise HTTPException(status_code=403, detail="本次考试已关闭，无法答题")

        existing = conn.execute(
            "SELECT score, total, submitted_at FROM scores WHERE student_id = ? AND exam_id = ?",
            (req.student_id, req.exam_id)
        ).fetchone()

        if existing:
            return {
                "already_submitted": True,
                "name": student["name"],
                "score": existing["score"],
                "total": existing["total"],
                "submitted_at": existing["submitted_at"],
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
