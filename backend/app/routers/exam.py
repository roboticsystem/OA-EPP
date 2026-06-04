from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_student_token
import json

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
        cur = conn.cursor()
        # 检查是否允许重新提交
        cur.execute(
            "SELECT id, allow_resubmit FROM exam_scores WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        existing = cur.fetchone()

        if existing:
            if existing["allow_resubmit"]:
                # 允许重新提交，更新成绩
                cur.execute(
                    "UPDATE exam_scores SET score=%s, total=%s, submitted_at=NOW(), allow_resubmit=0 WHERE id=%s",
                    (req.score, req.total, existing["id"])
                )
                cur.close()
                return {"ok": True, "student_id": student_id, "exam_id": exam_id,
                        "score": req.score, "total": req.total, "resubmitted": True}
            else:
                raise HTTPException(status_code=409, detail="您已经提交过本次考试的成绩")

        cur.execute(
            "INSERT INTO exam_scores (student_id, exam_id, score, total) VALUES (%s,%s,%s,%s)",
            (student_id, exam_id, req.score, req.total)
        )
        cur.close()

    return {"ok": True, "student_id": student_id, "exam_id": exam_id,
            "score": req.score, "total": req.total, "resubmitted": False}


@router.get("/api/exam_scores")
def get_scores(student_id: str = Query(...)):
    """查询某学生所有考试成绩（公开接口，凭学号查询）"""
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, student_id, class_name FROM exam_students WHERE student_id = %s",
            (student_id,)
        )
        student = cur.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        cur.execute("SELECT id, title FROM exam_list ORDER BY id")
        exam_list = cur.fetchall()
        cur.execute(
            "SELECT exam_id, score, total, submitted_at, allow_resubmit FROM exam_scores WHERE student_id = %s",
            (student_id,)
        )
        scores_rows = cur.fetchall()
        scores_map = {row["exam_id"]: dict(row) for row in scores_rows}

        # 查询所有评语
        feedbacks_map = {}
        cur.execute(
            "SELECT id, exam_id, teacher_comment, deduction_items, suggestions, created_at, updated_at "
            "FROM exam_feedbacks WHERE student_id = %s ORDER BY exam_id",
            (student_id,)
        )
        all_feedbacks = cur.fetchall()
        for fb in all_feedbacks:
            exam_id = fb["exam_id"]
            if exam_id not in feedbacks_map:
                feedbacks_map[exam_id] = []
            feedbacks_map[exam_id].append({
                "id": fb["id"],
                "teacher_comment": fb["teacher_comment"],
                "deduction_items": _parse_json(fb["deduction_items"]),
                "suggestions": _parse_json(fb["suggestions"]),
                "created_at": str(fb["created_at"]) if fb["created_at"] else None,
                "updated_at": str(fb["updated_at"]) if fb["updated_at"] else None,
            })
        cur.close()

    result = []
    for exam in exam_list:
        s = scores_map.get(exam["id"])
        result.append({
            "exam_id": exam["id"],
            "exam_title": exam["title"],
            "score": s["score"] if s else None,
            "total": s["total"] if s else None,
            "submitted_at": str(s["submitted_at"]) if s and s["submitted_at"] else None,
            "allow_resubmit": bool(s["allow_resubmit"]) if s else False,
            "exam_feedbacks": feedbacks_map.get(exam["id"], []),
        })

    return {
        "student": dict(student),
        "exam_scores": result,
    }


@router.get("/api/student/exam_feedbacks")
def get_student_feedbacks(student_id: str = Query(...), exam_id: Optional[str] = Query(None)):
    """学生查看自己的评语和改进建议"""
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, student_id FROM exam_students WHERE student_id = %s", (student_id,)
        )
        student = cur.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        if exam_id:
            cur.execute(
                "SELECT id, exam_id, teacher_comment, deduction_items, suggestions, created_at, updated_at "
                "FROM exam_feedbacks WHERE student_id = %s AND exam_id = %s ORDER BY created_at DESC",
                (student_id, exam_id)
            )
        else:
            cur.execute(
                "SELECT id, exam_id, teacher_comment, deduction_items, suggestions, created_at, updated_at "
                "FROM exam_feedbacks WHERE student_id = %s ORDER BY exam_id, created_at DESC",
                (student_id,)
            )
        rows = cur.fetchall()
        cur.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "exam_id": r["exam_id"],
            "teacher_comment": r["teacher_comment"],
            "deduction_items": _parse_json(r["deduction_items"]),
            "suggestions": _parse_json(r["suggestions"]),
            "created_at": str(r["created_at"]) if r["created_at"] else None,
            "updated_at": str(r["updated_at"]) if r["updated_at"] else None,
        })

    return {
        "student_name": student["name"],
        "student_id": student["student_id"],
        "exam_feedbacks": result,
    }


def _parse_json(val):
    """安全解析 JSON 字段（MySQL JSON 列可能直接返回 list/dict）"""
    if not val:
        return []
    if isinstance(val, (list, dict)):
        return val if isinstance(val, list) else [val]
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []
