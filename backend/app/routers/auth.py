from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token
import json

router = APIRouter()


def _parse_json_safe(val):
    """安全解析 JSON 字段（MySQL JSON 列可能直接返回 list/dict）"""
    if not val:
        return []
    if isinstance(val, (list, dict)):
        return val if isinstance(val, list) else [val]
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


class VerifyRequest(BaseModel):
    student_id: str
    exam_id: str


@router.post("/api/auth/verify")
def verify_identity(req: VerifyRequest):
    """
    核验学生身份并检查是否已提交成绩。
    - 学号不存在 → 403
    - 已提交 → {already_submitted: true, score, total, submitted_at, allow_resubmit, exam_feedbacks}
    - 未提交 → {already_submitted: false, token}
    """
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, student_id, class_name FROM exam_students WHERE student_id = %s",
            (req.student_id,)
        )
        student = cur.fetchone()

        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中，请联系老师确认")

        cur.execute(
            "SELECT id, title, is_active FROM exam_list WHERE id = %s",
            (req.exam_id,)
        )
        exam = cur.fetchone()

        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        if not exam["is_active"]:
            raise HTTPException(status_code=403, detail="本次考试已关闭，无法答题")

        cur.execute(
            "SELECT score, total, submitted_at, allow_resubmit FROM exam_scores WHERE student_id = %s AND exam_id = %s",
            (req.student_id, req.exam_id)
        )
        existing = cur.fetchone()

        if existing:
            # 查询评语
            cur.execute(
                "SELECT id, teacher_comment, deduction_items, suggestions, created_at, updated_at "
                "FROM exam_feedbacks WHERE student_id = %s AND exam_id = %s ORDER BY created_at DESC",
                (req.student_id, req.exam_id)
            )
            fb_rows = cur.fetchall()
            cur.close()
            exam_feedbacks = []
            for fb in fb_rows:
                exam_feedbacks.append({
                    "id": fb["id"],
                    "teacher_comment": fb["teacher_comment"],
                    "deduction_items": _parse_json_safe(fb["deduction_items"]),
                    "suggestions": _parse_json_safe(fb["suggestions"]),
                    "created_at": str(fb["created_at"]) if fb["created_at"] else None,
                    "updated_at": str(fb["updated_at"]) if fb["updated_at"] else None,
                })

            return {
                "already_submitted": True,
                "name": student["name"],
                "score": existing["score"],
                "total": existing["total"],
                "submitted_at": str(existing["submitted_at"]) if existing["submitted_at"] else None,
                "allow_resubmit": bool(existing["allow_resubmit"]),
                "exam_feedbacks": exam_feedbacks,
            }
        cur.close()

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
