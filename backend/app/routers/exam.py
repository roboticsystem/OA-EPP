from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_student_token

router = APIRouter()

# 远程数据库常量
COURSE_ID = 2       # 嵌入式系统综合实践
TEACHER_ID = 14     # 教师 李明


class SubmitRequest(BaseModel):
    score: float
    total: float


def _get_user_id(conn, student_no: str) -> Optional[int]:
    """通过 student_no 获取 user_id"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE role = 'student' AND student_no = %s",
        (student_no,)
    )
    row = cur.fetchone()
    return row["id"] if row else None


@router.post("/api/exam/submit")
def submit_score(req: SubmitRequest, authorization: Optional[str] = Header(None)):
    """提交成绩"""
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
            "SELECT id FROM scores WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="您已经提交过本次考试的成绩")

        conn.execute(
            "INSERT INTO scores (student_id, exam_id, score, total) VALUES (%s,%s,%s,%s)",
            (student_id, exam_id, req.score, req.total)
        )

    return {"ok": True, "student_id": student_id, "exam_id": exam_id,
            "score": req.score, "total": req.total}


@router.get("/api/scores")
def get_scores(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_student_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    student_id = payload["student_id"]
    with db() as conn:
        student = conn.execute(
            "SELECT name, student_id, class_name FROM students WHERE student_id = %s",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        exams = conn.execute("SELECT id, title FROM exams ORDER BY id").fetchall()
        scores_map = {
            row["exam_id"]: dict(row)
            for row in conn.execute(
                "SELECT exam_id, score, total, submitted_at FROM scores WHERE student_id = %s",
                (student_id,)
            ).fetchall()
        }

    result = []
    for exam in exams:
        eid = str(exam["id"])
        s = scores_map.get(eid)
        result.append({
            "exam_id": eid,
            "exam_title": exam["title"],
            "exam_type": exam.get("exam_type", ""),
            "score": float(s["score"]) if s else None,
            "total": float(s["total"]) if s else None,
            "submitted_at": s["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if s and s["submitted_at"] else None,
        })

    return {
        "student": {"name": student["name"], "student_id": student["student_id"], "class_name": student["class_name"]},
        "scores": result,
    }
