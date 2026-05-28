"""
F-S-053 课堂在线考试 API
- 教师：发布考试、题目管理、批改主观题
- 学生：限时作答、草稿保存、提交出分、截止自动交卷
- 考试期间仅可访问本人作答，无法查看他人答案
"""
import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

from app.auth_utils import create_token, verify_student_token, verify_teacher_token
from app.database import db
from app.classroom_exam_service import (
    ensure_attempt,
    exam_status,
    get_attempt,
    get_attempt_by_id,
    get_exam,
    get_questions,
    load_answers,
    maybe_auto_submit,
    parse_dt,
    question_for_student,
    result_for_student,
    submit_attempt,
)

router = APIRouter()


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _require_classroom_student(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_student_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if payload.get("exam_kind") != "classroom":
        raise HTTPException(status_code=403, detail="无效的考试令牌")
    return payload


class QuestionIn(BaseModel):
    qtype: str = Field(..., pattern="^(single|multi|blank|short)$")
    content: str
    options: Optional[list[str]] = None
    answer_key: dict
    score: float = Field(..., gt=0)


class ClassroomExamCreate(BaseModel):
    id: Optional[str] = None
    title: str
    start_at: str
    end_at: str
    questions: list[QuestionIn]


class ClassroomExamUpdate(BaseModel):
    title: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    is_active: Optional[int] = None


class VerifyClassroomRequest(BaseModel):
    student_id: str
    exam_id: str


class DraftRequest(BaseModel):
    answers: dict[str, Any]


class GradeAnswerIn(BaseModel):
    question_id: int
    score: float = Field(..., ge=0)


class GradeAttemptRequest(BaseModel):
    grades: list[GradeAnswerIn]


# ── 学生：考试列表（不含他人数据）────────────────────────

@router.get("/api/classroom-exam/list")
def list_public_exams():
    """可参加的课堂考试列表（不含题目与答案）。"""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, start_at, end_at, is_active FROM classroom_exams ORDER BY start_at DESC"
        ).fetchall()
    result = []
    for r in rows:
        exam = dict(r)
        st = exam_status(exam)
        if not exam["is_active"]:
            st = "closed"
        result.append({
            "id": exam["id"],
            "title": exam["title"],
            "start_at": exam["start_at"],
            "end_at": exam["end_at"],
            "status": st,
        })
    return result


@router.post("/api/classroom-exam/verify")
def verify_classroom(req: VerifyClassroomRequest):
    """学生身份核验并创建/恢复作答记录。"""
    with db() as conn:
        student = conn.execute(
            "SELECT name, student_id FROM students WHERE student_id=?",
            (req.student_id,),
        ).fetchone()
        if not student:
            raise HTTPException(status_code=403, detail="学号不在名单中")

        exam = get_exam(conn, req.exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        if not exam["is_active"]:
            raise HTTPException(status_code=403, detail="考试已关闭")

        st = exam_status(exam)
        attempt = ensure_attempt(conn, req.exam_id, req.student_id)
        maybe_auto_submit(conn, attempt)
        attempt = get_attempt(conn, req.exam_id, req.student_id)

        if attempt["status"] in ("submitted", "graded"):
            return {
                "already_submitted": True,
                "name": student["name"],
                **result_for_student(conn, attempt, exam),
            }

        if st == "not_started":
            raise HTTPException(
                status_code=403,
                detail=f"考试尚未开始（开始时间：{exam['start_at']}）",
            )
        if st == "ended":
            raise HTTPException(status_code=403, detail="考试已结束")

        token = create_token({
            "role": "student",
            "exam_kind": "classroom",
            "student_id": student["student_id"],
            "name": student["name"],
            "exam_id": req.exam_id,
            "attempt_id": attempt["id"],
        }, expires_hours=4)

        questions = [question_for_student(q) for q in get_questions(conn, req.exam_id)]
        answers_map = load_answers(attempt)

        return {
            "already_submitted": False,
            "name": student["name"],
            "token": token,
            "attempt_id": attempt["id"],
            "exam": {
                "id": exam["id"],
                "title": exam["title"],
                "start_at": exam["start_at"],
                "end_at": exam["end_at"],
                "status": st,
            },
            "questions": questions,
            "answers": {str(k): v for k, v in answers_map.items()},
            "draft_saved_at": attempt.get("draft_saved_at"),
        }


@router.get("/api/classroom-exam/session")
def get_session(authorization: Optional[str] = Header(None)):
    """刷新会话：拉取题目与草稿（仅本人）。"""
    payload = _require_classroom_student(authorization)
    with db() as conn:
        attempt = get_attempt_by_id(conn, payload["attempt_id"])
        if not attempt or attempt["student_id"] != payload["student_id"]:
            raise HTTPException(status_code=403, detail="无权访问")
        exam = get_exam(conn, payload["exam_id"])
        maybe_auto_submit(conn, attempt)
        attempt = get_attempt_by_id(conn, payload["attempt_id"])

        if attempt["status"] in ("submitted", "graded"):
            return {"submitted": True, **result_for_student(conn, attempt, exam)}

        st = exam_status(exam)
        if st == "ended":
            maybe_auto_submit(conn, attempt)
            attempt = get_attempt_by_id(conn, payload["attempt_id"])
            if attempt["status"] != "draft":
                return {"submitted": True, **result_for_student(conn, attempt, exam)}
            raise HTTPException(status_code=403, detail="考试已结束")

        questions = [question_for_student(q) for q in get_questions(conn, exam["id"])]
        return {
            "submitted": False,
            "exam": {
                "id": exam["id"],
                "title": exam["title"],
                "start_at": exam["start_at"],
                "end_at": exam["end_at"],
                "status": st,
            },
            "attempt_id": attempt["id"],
            "questions": questions,
            "answers": load_answers(attempt),
            "draft_saved_at": attempt.get("draft_saved_at"),
        }


@router.put("/api/classroom-exam/draft")
def save_draft_api(req: DraftRequest, authorization: Optional[str] = Header(None)):
    """实时保存草稿（断线可恢复）。"""
    payload = _require_classroom_student(authorization)
    answers = {int(k): v for k, v in req.answers.items()}

    with db() as conn:
        attempt = get_attempt_by_id(conn, payload["attempt_id"])
        if not attempt or attempt["student_id"] != payload["student_id"]:
            raise HTTPException(status_code=403, detail="无权访问")

        exam = get_exam(conn, attempt["exam_id"])
        if exam_status(exam) == "not_started":
            raise HTTPException(status_code=403, detail="考试尚未开始")

        payload_json = json.dumps({str(k): v for k, v in answers.items()}, ensure_ascii=False)
        conn.execute(
            """UPDATE classroom_exam_attempts
               SET answers_json=?, draft_saved_at=datetime('now','localtime')
               WHERE id=? AND status='draft'""",
            (payload_json, attempt["id"]),
        )

        if exam_status(exam) == "ended":
            result = submit_attempt(conn, attempt["id"], auto=True)
            attempt = get_attempt_by_id(conn, attempt["id"])
            return {
                "auto_submitted": True,
                **result,
                **result_for_student(conn, attempt, exam),
            }

        row = conn.execute(
            "SELECT draft_saved_at FROM classroom_exam_attempts WHERE id=?",
            (attempt["id"],),
        ).fetchone()
        return {"ok": True, "draft_saved_at": row["draft_saved_at"]}


@router.post("/api/classroom-exam/submit")
def submit_api(authorization: Optional[str] = Header(None)):
    """提交试卷；客观题立即出分。"""
    payload = _require_classroom_student(authorization)
    with db() as conn:
        attempt = get_attempt_by_id(conn, payload["attempt_id"])
        if not attempt or attempt["student_id"] != payload["student_id"]:
            raise HTTPException(status_code=403, detail="无权访问")
        exam = get_exam(conn, attempt["exam_id"])
        try:
            result = submit_attempt(conn, attempt["id"], auto=False)
        except ValueError as e:
            code = str(e)
            if code == "already_submitted":
                raise HTTPException(status_code=409, detail="已提交")
            raise HTTPException(status_code=400, detail=code)
        attempt = get_attempt_by_id(conn, attempt["id"])
        return {**result, **result_for_student(conn, attempt, exam)}


@router.get("/api/classroom-exam/my-results")
def my_results(student_id: str = Query(...)):
    """学生历史成绩（仅本人，不含他人答案）。"""
    with db() as conn:
        if not conn.execute("SELECT 1 FROM students WHERE student_id=?", (student_id,)).fetchone():
            raise HTTPException(status_code=404, detail="学号不存在")
        attempts = conn.execute(
            """SELECT a.*, e.title, e.end_at
               FROM classroom_exam_attempts a
               JOIN classroom_exams e ON e.id = a.exam_id
               WHERE a.student_id=? AND a.status IN ('submitted','graded')
               ORDER BY a.submitted_at DESC""",
            (student_id,),
        ).fetchall()
    return [
        {
            "exam_id": r["exam_id"],
            "title": r["title"],
            "submitted_at": r["submitted_at"],
            "max_score": r["max_score"],
            "total_score": r["total_score"],
            "objective_score": r["objective_score"],
            "status": "待批改" if r["subjective_pending"] else "已批改",
            "subjective_pending": r["subjective_pending"],
            "auto_submitted": bool(r["auto_submitted"]),
        }
        for r in attempts
    ]


# ── 教师端 ───────────────────────────────────────────────

@router.get("/api/teacher/classroom-exams")
def teacher_list_exams(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exams = conn.execute(
            "SELECT * FROM classroom_exams ORDER BY start_at DESC"
        ).fetchall()
        out = []
        for e in exams:
            exam = dict(e)
            q_count = conn.execute(
                "SELECT COUNT(*) FROM classroom_exam_questions WHERE exam_id=?",
                (exam["id"],),
            ).fetchone()[0]
            submitted = conn.execute(
                """SELECT COUNT(*) FROM classroom_exam_attempts
                   WHERE exam_id=? AND status IN ('submitted','graded')""",
                (exam["id"],),
            ).fetchone()[0]
            out.append({
                **exam,
                "status": exam_status(exam),
                "question_count": q_count,
                "submitted_count": submitted,
            })
    return out


@router.post("/api/teacher/classroom-exams")
def teacher_create_exam(req: ClassroomExamCreate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    exam_id = (req.id or "").strip() or f"exam-{uuid.uuid4().hex[:8]}"
    try:
        parse_dt(req.start_at)
        parse_dt(req.end_at)
    except Exception:
        raise HTTPException(status_code=422, detail="时间格式无效，请使用 YYYY-MM-DD HH:MM:SS")

    if parse_dt(req.end_at) <= parse_dt(req.start_at):
        raise HTTPException(status_code=422, detail="结束时间必须晚于开始时间")
    if not req.questions:
        raise HTTPException(status_code=422, detail="至少包含一道题目")

    with db() as conn:
        conn.execute(
            """INSERT INTO classroom_exams (id, title, start_at, end_at)
               VALUES (?,?,?,?)""",
            (exam_id, req.title.strip(), req.start_at.strip(), req.end_at.strip()),
        )
        for i, q in enumerate(req.questions, 1):
            opts = json.dumps(q.options, ensure_ascii=False) if q.options else None
            key = json.dumps(q.answer_key, ensure_ascii=False)
            conn.execute(
                """INSERT INTO classroom_exam_questions
                   (exam_id, qtype, content, options_json, answer_key_json, score, sort_no)
                   VALUES (?,?,?,?,?,?,?)""",
                (exam_id, q.qtype, q.content.strip(), opts, key, q.score, i),
            )
    return {"ok": True, "id": exam_id}


@router.get("/api/teacher/classroom-exams/{exam_id}")
def teacher_get_exam(exam_id: str, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exam = get_exam(conn, exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        questions = get_questions(conn, exam_id)
    for q in questions:
        q["options"] = json.loads(q["options_json"]) if q.get("options_json") else None
        q["answer_key"] = json.loads(q["answer_key_json"])
        del q["options_json"]
        del q["answer_key_json"]
    return {"exam": exam, "questions": questions, "status": exam_status(exam)}


@router.put("/api/teacher/classroom-exams/{exam_id}")
def teacher_update_exam(
    exam_id: str, req: ClassroomExamUpdate, authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    with db() as conn:
        if not get_exam(conn, exam_id):
            raise HTTPException(status_code=404, detail="考试不存在")
        if req.title is not None:
            conn.execute("UPDATE classroom_exams SET title=? WHERE id=?", (req.title.strip(), exam_id))
        if req.start_at is not None:
            conn.execute("UPDATE classroom_exams SET start_at=? WHERE id=?", (req.start_at.strip(), exam_id))
        if req.end_at is not None:
            conn.execute("UPDATE classroom_exams SET end_at=? WHERE id=?", (req.end_at.strip(), exam_id))
        if req.is_active is not None:
            conn.execute("UPDATE classroom_exams SET is_active=? WHERE id=?", (req.is_active, exam_id))
    return {"ok": True}


@router.delete("/api/teacher/classroom-exams/{exam_id}")
def teacher_delete_exam(exam_id: str, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        conn.execute("DELETE FROM classroom_exam_questions WHERE exam_id=?", (exam_id,))
        conn.execute("DELETE FROM classroom_exam_attempts WHERE exam_id=?", (exam_id,))
        conn.execute("DELETE FROM classroom_exams WHERE id=?", (exam_id,))
    return {"ok": True}


@router.get("/api/teacher/classroom-exams/{exam_id}/attempts")
def teacher_list_attempts(exam_id: str, authorization: Optional[str] = Header(None)):
    """教师查看提交列表（汇总分，不含可复制他人完整答案的批量导出）。"""
    _require_teacher(authorization)
    with db() as conn:
        exam = get_exam(conn, exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        rows = conn.execute(
            """SELECT a.id, a.student_id, s.name, s.class_name,
                      a.status, a.objective_score, a.total_score, a.max_score,
                      a.subjective_pending, a.submitted_at, a.auto_submitted
               FROM classroom_exam_attempts a
               JOIN students s ON s.student_id = a.student_id
               WHERE a.exam_id=?
               ORDER BY a.submitted_at DESC, s.student_id""",
            (exam_id,),
        ).fetchall()
    return {"exam_title": exam["title"], "attempts": [dict(r) for r in rows]}


@router.get("/api/teacher/classroom-exams/{exam_id}/attempts/{attempt_id}")
def teacher_attempt_detail(
    exam_id: str, attempt_id: int, authorization: Optional[str] = Header(None)
):
    """教师查看单份答卷以批改主观题。"""
    _require_teacher(authorization)
    with db() as conn:
        attempt = get_attempt_by_id(conn, attempt_id)
        if not attempt or attempt["exam_id"] != exam_id:
            raise HTTPException(status_code=404, detail="作答记录不存在")
        exam = get_exam(conn, exam_id)
        questions = get_questions(conn, exam_id)
        answers_map = load_answers(attempt)
        items = []
        for q in questions:
            key = json.loads(q["answer_key_json"])
            items.append({
                "question_id": q["id"],
                "qtype": q["qtype"],
                "content": q["content"],
                "max_score": q["score"],
                "answer_key": key,
                "student_answer": answers_map.get(q["id"]),
            })
    return {"attempt": dict(attempt), "questions": items}


@router.post("/api/teacher/classroom-exams/{exam_id}/attempts/{attempt_id}/grade")
def teacher_grade_attempt(
    exam_id: str,
    attempt_id: int,
    req: GradeAttemptRequest,
    authorization: Optional[str] = Header(None),
):
    _require_teacher(authorization)
    with db() as conn:
        attempt = get_attempt_by_id(conn, attempt_id)
        if not attempt or attempt["exam_id"] != exam_id:
            raise HTTPException(status_code=404, detail="作答记录不存在")
        if attempt["status"] == "draft":
            raise HTTPException(status_code=400, detail="学生尚未提交")

        questions = {q["id"]: q for q in get_questions(conn, exam_id)}
        answers_map = load_answers(attempt)
        grade_map = {g.question_id: g.score for g in req.grades}

        for qid, sc in grade_map.items():
            if qid not in questions:
                raise HTTPException(status_code=422, detail=f"题目 {qid} 不存在")
            if questions[qid]["qtype"] != "short":
                raise HTTPException(status_code=422, detail="仅简答题可手动批改")
            if sc > float(questions[qid]["score"]):
                raise HTTPException(status_code=422, detail="得分不能超过题目满分")

        objective = float(attempt.get("objective_score") or 0)
        subjective = sum(grade_map.values())
        short_ids = [q["id"] for q in questions.values() if q["qtype"] == "short"]
        for sid in short_ids:
            if sid not in grade_map:
                raise HTTPException(status_code=422, detail="请为所有简答题打分")

        total = round(objective + subjective, 2)
        conn.execute(
            """UPDATE classroom_exam_attempts
               SET status='graded', total_score=?, subjective_pending=0
               WHERE id=?""",
            (total, attempt_id),
        )
    return {"ok": True, "total_score": total}
