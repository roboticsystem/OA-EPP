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
    with db() as conn:
        student = conn.execute(
            "SELECT u.full_name AS name, u.student_no AS student_id, s.class_name "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.student_no = %s AND u.role = 'student'",
            (req.student_id,)
        ).fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        exam = conn.execute(
            "SELECT id, title, "
            "CASE WHEN end_at IS NULL OR end_at > NOW() THEN 1 ELSE 0 END AS is_active "
            "FROM exams WHERE id = CAST(%s AS UNSIGNED)",
            (req.exam_id,)
        ).fetchone()

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        if not exam["is_active"]:
            raise HTTPException(status_code=403, detail="本次考试已关闭，无法答题")

        existing = conn.execute(
            "SELECT ea.total_score AS score, ea.submitted_at, "
            "(SELECT COALESCE(SUM(eq.score), 0) FROM exam_questions eq WHERE eq.exam_id = ea.exam_id) AS total "
            "FROM exam_attempts ea "
            "JOIN users u ON ea.student_user_id = u.id "
            "WHERE u.student_no = %s AND ea.exam_id = CAST(%s AS UNSIGNED) "
            "AND ea.status IN ('submitted', 'graded')",
            (req.student_id, req.exam_id)
        ).fetchone()

        if existing:
            return {
                "already_submitted": True,
                "name": student["name"],
                "score": float(existing["score"]) if existing["score"] else 0,
                "total": float(existing["total"]) if existing["total"] else 0,
                "submitted_at": str(existing["submitted_at"]) if existing["submitted_at"] else "",
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
