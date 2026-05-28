"""课堂考试业务逻辑：时间窗口、自动交卷、草稿与提交。"""
import json
from datetime import datetime
from typing import Any, Optional

from app.classroom_scoring import compute_attempt_scores
from app.database import db


def now_local() -> datetime:
    return datetime.now()


def parse_dt(s: str) -> datetime:
    s = s.strip().replace("T", " ")
    if len(s) >= 19:
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    if len(s) >= 16:
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    raise ValueError(f"invalid datetime: {s}")


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def exam_status(exam: dict) -> str:
    """not_started | active | ended"""
    if not exam["is_active"]:
        return "closed"
    now = now_local()
    start = parse_dt(exam["start_at"])
    end = parse_dt(exam["end_at"])
    if now < start:
        return "not_started"
    if now > end:
        return "ended"
    return "active"


def get_exam(conn, exam_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM classroom_exams WHERE id=?", (exam_id,)
    ).fetchone()
    return dict(row) if row else None


def get_questions(conn, exam_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT id, exam_id, qtype, content, options_json, answer_key_json, score, sort_no
           FROM classroom_exam_questions WHERE exam_id=? ORDER BY sort_no, id""",
        (exam_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def question_for_student(q: dict) -> dict:
    opts = json.loads(q["options_json"]) if q.get("options_json") else None
    return {
        "id": q["id"],
        "qtype": q["qtype"],
        "content": q["content"],
        "options": opts,
        "score": q["score"],
        "sort_no": q["sort_no"],
    }


def get_attempt(conn, exam_id: str, student_id: str) -> Optional[dict]:
    row = conn.execute(
        """SELECT * FROM classroom_exam_attempts
           WHERE exam_id=? AND student_id=?""",
        (exam_id, student_id),
    ).fetchone()
    return dict(row) if row else None


def get_attempt_by_id(conn, attempt_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM classroom_exam_attempts WHERE id=?", (attempt_id,)
    ).fetchone()
    return dict(row) if row else None


def load_answers(attempt: dict) -> dict[int, Any]:
    if not attempt.get("answers_json"):
        return {}
    data = json.loads(attempt["answers_json"])
    return {int(k): v for k, v in data.items()}


def save_draft(conn, attempt_id: int, answers: dict[int, Any]) -> dict:
    attempt = get_attempt_by_id(conn, attempt_id)
    if not attempt:
        raise ValueError("attempt_not_found")
    if attempt["status"] != "draft":
        raise ValueError("already_submitted")

    exam = get_exam(conn, attempt["exam_id"])
    if exam_status(exam) == "ended":
        return submit_attempt(conn, attempt_id, auto=True)

    payload = json.dumps({str(k): v for k, v in answers.items()}, ensure_ascii=False)
    conn.execute(
        """UPDATE classroom_exam_attempts
           SET answers_json=?, draft_saved_at=datetime('now','localtime')
           WHERE id=?""",
        (payload, attempt_id),
    )
    return {"ok": True, "draft_saved_at": fmt_dt(now_local())}


def submit_attempt(conn, attempt_id: int, auto: bool = False) -> dict:
    attempt = get_attempt_by_id(conn, attempt_id)
    if not attempt:
        raise ValueError("attempt_not_found")
    if attempt["status"] != "draft":
        raise ValueError("already_submitted")

    exam = get_exam(conn, attempt["exam_id"])
    st = exam_status(exam)
    if st == "not_started" and not auto:
        raise ValueError("not_started")
    if st == "closed":
        raise ValueError("exam_closed")

    questions = get_questions(conn, attempt["exam_id"])
    answers_map = load_answers(attempt)
    max_score = sum(float(q["score"]) for q in questions)
    objective, max_obj, pending, _details = compute_attempt_scores(questions, answers_map)

    status = "graded" if pending == 0 else "submitted"
    total = objective if pending == 0 else None

    conn.execute(
        """UPDATE classroom_exam_attempts SET
            status=?, objective_score=?, subjective_pending=?,
            total_score=?, max_score=?, submitted_at=datetime('now','localtime'),
            auto_submitted=?
           WHERE id=?""",
        (status, objective, pending, total, max_score, 1 if auto else 0, attempt_id),
    )

    return {
        "ok": True,
        "status": status,
        "objective_score": objective,
        "max_objective_score": max_obj,
        "max_score": max_score,
        "total_score": total,
        "subjective_pending": pending,
        "auto_submitted": auto,
    }


def maybe_auto_submit(conn, attempt: dict) -> Optional[dict]:
    """截止时间到自动提交草稿。"""
    if not attempt or attempt["status"] != "draft":
        return None
    exam = get_exam(conn, attempt["exam_id"])
    if exam_status(exam) != "ended":
        return None
    return submit_attempt(conn, attempt["id"], auto=True)


def ensure_attempt(conn, exam_id: str, student_id: str) -> dict:
    attempt = get_attempt(conn, exam_id, student_id)
    if attempt:
        maybe_auto_submit(conn, attempt)
        attempt = get_attempt(conn, exam_id, student_id)
        return attempt
    conn.execute(
        """INSERT INTO classroom_exam_attempts (exam_id, student_id, status, answers_json)
           VALUES (?,?, 'draft', '{}')""",
        (exam_id, student_id),
    )
    return get_attempt(conn, exam_id, student_id)


def result_for_student(conn, attempt: dict, exam: dict) -> dict:
    questions = get_questions(conn, attempt["exam_id"])
    answers_map = load_answers(attempt)
    per_q = []
    for q in questions:
        qid = q["id"]
        ans = answers_map.get(qid)
        item = {
            "question_id": qid,
            "qtype": q["qtype"],
            "content": q["content"],
            "your_answer": ans,
            "max_score": q["score"],
        }
        if attempt["status"] in ("submitted", "graded") and q["qtype"] != "short":
            from app.classroom_scoring import score_question
            key = json.loads(q["answer_key_json"])
            ratio, needs = score_question(q["qtype"], ans, key)
            if not needs and ratio is not None:
                item["score"] = round(float(q["score"]) * ratio, 2)
                item["graded"] = True
            else:
                item["score"] = None
                item["graded"] = False
        elif attempt["status"] == "graded" or (
            attempt["status"] == "submitted" and q["qtype"] == "short"
        ):
            item["score"] = None
            item["graded"] = q["qtype"] != "short"
            if q["qtype"] == "short":
                item["graded"] = attempt.get("subjective_pending", 1) == 0
        else:
            item["score"] = None
            item["graded"] = False
        per_q.append(item)

    return {
        "exam_id": exam["id"],
        "title": exam["title"],
        "status": attempt["status"],
        "objective_score": attempt.get("objective_score"),
        "total_score": attempt.get("total_score"),
        "max_score": attempt.get("max_score"),
        "subjective_pending": attempt.get("subjective_pending", 0),
        "submitted_at": attempt.get("submitted_at"),
        "auto_submitted": bool(attempt.get("auto_submitted")),
        "questions": per_q,
    }
