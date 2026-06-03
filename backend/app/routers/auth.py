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
