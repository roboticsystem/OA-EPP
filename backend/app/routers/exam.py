from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_student_token

router = APIRouter()


class SubmitRequest(BaseModel):
    answers: dict


@router.post("/api/exam/submit")
def submit_exam(req: SubmitRequest, authorization: Optional[str] = Header(None)):
    """提交考试答卷，需要学生 JWT。每人每考试只能提交一次。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = verify_student_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    student_id = payload["student_id"]
    exam_id = payload["exam_id"]

    with db() as conn:
        existing = conn.execute(
            "SELECT id FROM exam_attempts WHERE student_user_id = %s AND exam_id = %s AND status = 'submitted'",
            (student_id, exam_id)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="您已经提交过本次考试")

        conn.execute(
            "INSERT INTO exam_attempts (exam_id, student_user_id, status, submitted_at) VALUES (%s,%s,%s, NOW())",
            (exam_id, student_id, "submitted")
        )

    return {"ok": True, "student_id": student_id, "exam_id": exam_id}


@router.get("/api/scores")
def get_scores(student_id: int = Query(...)):
    """查询某学生所有考试成绩（公开接口，凭学号查询）"""
    with db() as conn:
        student = conn.execute(
            "SELECT u.id AS student_id, u.full_name AS name, s.class_name FROM users u JOIN students s ON u.id = s.user_id WHERE u.id = %s AND u.role = 'student' AND u.is_active = 1",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        exams = conn.execute("SELECT id, title FROM exams ORDER BY id").fetchall()
        scores_map = {
            row["exam_id"]: dict(row)
            for row in conn.execute(
                "SELECT exam_id, total_score, submitted_at FROM exam_attempts WHERE student_user_id = %s AND status = 'submitted'",
                (student_id,)
            ).fetchall()
        }

    result = []
    for exam in exams:
        s = scores_map.get(exam["id"])
        result.append({
            "exam_id": exam["id"],
            "exam_title": exam["title"],
            "score": s["total_score"] if s else None,
            "submitted_at": s["submitted_at"] if s else None,
        })

    return {
        "student": dict(student),
        "scores": result,
    }