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
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name as name, u.student_no as student_id, s.class_name, u.id as user_id
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.student_no = %s AND u.role = 'student'
        """, (req.student_id,))
        student = cursor.fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        cursor.execute("SELECT id, title FROM exams WHERE id = %s", (int(req.exam_id),))
        exam = cursor.fetchone()

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        # 检查是否已提交 - 暂时没有成绩记录功能
        existing = None

        if existing:
            return {
                "already_submitted": True,
                "name": student["name"],
                "score": None,
                "total": None,
                "submitted_at": None,
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
