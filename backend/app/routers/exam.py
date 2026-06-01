from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_student_token

router = APIRouter()


class SubmitRequest(BaseModel):
    score: float
    total: float


@router.post("/api/exam/submit")
def submit_score(req: SubmitRequest, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = verify_student_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    student_id = payload["student_id"]
    exam_id = payload["exam_id"]

    if req.score < 0 or req.total <= 0 or req.score > req.total:
        raise HTTPException(status_code=422, detail="成绩数据无效")

    with db() as conn:
        existing = conn.execute(
            "SELECT ea.id FROM exam_attempts ea "
            "JOIN users u ON ea.student_user_id = u.id "
            "WHERE u.student_no = %s AND ea.exam_id = CAST(%s AS UNSIGNED) "
            "AND ea.status IN ('submitted', 'graded')",
            (student_id, exam_id)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="您已经提交过本次考试的成绩")

        conn.execute(
            "INSERT INTO exam_attempts (exam_id, student_user_id, status, total_score, submitted_at) "
            "VALUES (CAST(%s AS UNSIGNED), (SELECT id FROM users WHERE student_no = %s), 'submitted', %s, NOW())",
            (exam_id, student_id, req.score)
        )

    return {"ok": True, "student_id": student_id, "exam_id": exam_id,
            "score": req.score, "total": req.total}


@router.get("/api/scores")
def get_scores(student_id: str = Query(...)):
    with db() as conn:
        student = conn.execute(
            "SELECT u.full_name AS name, u.student_no AS student_id, s.class_name "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.student_no = %s AND u.role = 'student'",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        exams = conn.execute("SELECT id, title FROM exams ORDER BY id").fetchall()
        scores_map = {
            row["exam_id"]: dict(row)
            for row in conn.execute(
                "SELECT ea.exam_id, ea.total_score AS score, ea.submitted_at, "
                "(SELECT COALESCE(SUM(eq.score),0) FROM exam_questions eq WHERE eq.exam_id = ea.exam_id) AS total "
                "FROM exam_attempts ea "
                "JOIN users u ON ea.student_user_id = u.id "
                "WHERE u.student_no = %s AND ea.status IN ('submitted', 'graded')",
                (student_id,)
            ).fetchall()
        }

    result = []
    for exam in exams:
        s = scores_map.get(exam["id"])
        result.append({
            "exam_id": exam["id"],
            "exam_title": exam["title"],
            "score": float(s["score"]) if s else None,
            "total": float(s["total"]) if s else None,
            "submitted_at": str(s["submitted_at"]) if s else None,
        })

    return {"student": dict(student), "scores": result}
