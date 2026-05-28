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
        cursor = conn.cursor()
        
        # 获取学生 user_id
        cursor.execute("SELECT id FROM users WHERE student_no = %s AND role = 'student'", (student_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="学生不存在")
        
        user_id = user["id"]
        
        # 查找考试
        cursor.execute("SELECT id, course_id FROM exams WHERE id = %s", (int(exam_id),))
        exam = cursor.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        exam_db_id = exam["id"]
        course_id = exam["course_id"]
        
        # 创建考试尝试记录
        cursor.execute("""
            INSERT INTO exam_attempts (exam_id, student_user_id, status, total_score, submitted_at)
            VALUES (%s, %s, 'submitted', %s, NOW())
        """, (exam_db_id, user_id, req.score))
        
        attempt_id = cursor.lastrowid
        
        # 添加成绩记录
        cursor.execute("""
            INSERT INTO score_items (course_id, student_user_id, score_type, ref_id, score, scored_by, scored_at)
            VALUES (%s, %s, 'exam', %s, %s, NULL, NOW())
        """, (course_id, user_id, attempt_id, req.score))

    return {"ok": True, "student_id": student_id, "exam_id": exam_id, "score": req.score, "total": req.total}


@router.get("/api/scores")
def get_scores(student_id: str = Query(...)):
    """查询某学生所有考试成绩"""
    with db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name as name, u.student_no as student_id, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.student_no = %s AND u.role = 'student'
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        cursor.execute("SELECT id, title FROM exams ORDER BY id")
        exams = cursor.fetchall()

        # 获取成绩记录
        cursor.execute("""
            SELECT ea.exam_id, ea.total_score as score, ea.total_score as total, ea.submitted_at
            FROM exam_attempts ea
            JOIN users u ON ea.student_user_id = u.id
            WHERE u.student_no = %s
        """, (student_id,))
        scores_data = cursor.fetchall()
        scores_map = {s["exam_id"]: s for s in scores_data}

    result = []
    for exam in exams:
        s = scores_map.get(exam["id"])
        result.append({
            "exam_id": str(exam["id"]),
            "exam_title": exam["title"],
            "score": s["score"] if s else None,
            "total": s["total"] if s else None,
            "submitted_at": s["submitted_at"] if s else None,
        })

    return {
        "student": dict(student),
        "scores": result,
    }
