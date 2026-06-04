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
    """提交成绩，需要学生 JWT。每人每考试只能提交一次。"""
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
        # 再次确认未提交（防止并发重复）
        existing = conn.execute(
            "SELECT id FROM scores WHERE student_id = ? AND exam_id = ?",
            (student_id, exam_id)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="您已经提交过本次考试的成绩")

        conn.execute(
            "INSERT INTO scores (student_id, exam_id, score, total) VALUES (?,?,?,?)",
            (student_id, exam_id, req.score, req.total)
        )

    return {"ok": True, "student_id": student_id, "exam_id": exam_id,
            "score": req.score, "total": req.total}


@router.get("/api/scores")
def get_scores(student_id: str = Query(...)):
    """查询某学生所有考试成绩（公开接口，凭学号查询）"""
    with db() as conn:
        student = conn.execute(
            "SELECT name, student_id, class_name FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        exams = conn.execute("SELECT id, title FROM exams ORDER BY id").fetchall()
        scores_map = {
            row["exam_id"]: dict(row)
            for row in conn.execute(
                "SELECT exam_id, score, total, submitted_at FROM scores WHERE student_id = ?",
                (student_id,)
            ).fetchall()
        }

    result = []
    for exam in exams:
        s = scores_map.get(exam["id"])
        result.append({
            "exam_id": exam["id"],
            "exam_title": exam["title"],
            "score": s["score"] if s else None,
            "total": s["total"] if s else None,
            "submitted_at": s["submitted_at"] if s else None,
        })

    return {
        "student": dict(student),
        "scores": result,
    }
