"""课堂考试客观题自动评分（F-S-053）。"""
import json
import re
from typing import Any, Optional


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip().lower())


def _letters() -> list[str]:
    return [chr(65 + i) for i in range(26)]


def score_single(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    correct = key.get("correct")
    if correct is None and "correct_index" in key:
        correct = _letters()[int(key["correct_index"])]
    if correct is None:
        return None, False
    return (1.0 if str(answer).strip().upper() == str(correct).strip().upper() else 0.0), False


def score_multi(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    correct = key.get("correct") or key.get("correct_options") or []
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except json.JSONDecodeError:
            answer = [x.strip() for x in answer.split(",") if x.strip()]
    if not isinstance(answer, list):
        return 0.0, False
    a_set = {str(x).strip().upper() for x in answer}
    c_set = {str(x).strip().upper() for x in correct}
    if not c_set:
        return None, False
    if a_set == c_set:
        return 1.0, False
    if key.get("partial") and a_set <= c_set and a_set:
        return len(a_set) / len(c_set), False
    return 0.0, False


def score_blank_legacy(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    acceptable = key.get("acceptable") or key.get("answers") or []
    if isinstance(acceptable, str):
        acceptable = [acceptable]
    if not acceptable and key.get("correct"):
        acceptable = [key["correct"]]
    if not acceptable:
        return None, False
    ans = _norm(str(answer or ""))
    for item in acceptable:
        if ans == _norm(str(item)):
            return 1.0, False
    return 0.0, False


def _blank_answers_list(answer: Any, blank_count: int) -> list[str]:
    if isinstance(answer, dict):
        return [str(answer.get(str(i), answer.get(i, "")) or "") for i in range(blank_count)]
    if isinstance(answer, list):
        vals = [str(x or "") for x in answer]
        while len(vals) < blank_count:
            vals.append("")
        return vals[:blank_count]
    if blank_count <= 1:
        return [str(answer or "")]
    return [str(answer or "")] + [""] * (blank_count - 1)


def score_blank_multi(answer: Any, key: dict) -> tuple[float, float]:
    """多空填空：按空给分。返回 (得分, 满分)。"""
    blanks = key.get("blanks") or []
    if not blanks:
        ratio, _ = score_blank_legacy(answer, key)
        max_pts = float(key.get("max_score") or 0) or 1.0
        return (max_pts * (ratio or 0), max_pts)

    answers = _blank_answers_list(answer, len(blanks))
    earned = 0.0
    max_pts = 0.0
    for i, spec in enumerate(blanks):
        pts = float(spec.get("score") or 0)
        max_pts += pts
        acceptable = spec.get("acceptable") or spec.get("answers") or []
        if isinstance(acceptable, str):
            acceptable = [acceptable]
        ans = _norm(answers[i] if i < len(answers) else "")
        for item in acceptable:
            if ans == _norm(str(item)):
                earned += pts
                break
    return round(earned, 2), round(max_pts, 2)


def score_question(qtype: str, answer: Any, answer_key: dict) -> tuple[Optional[float], bool]:
    if qtype == "short":
        return None, True
    if qtype == "single":
        return score_single(answer, answer_key)
    if qtype == "multi":
        return score_multi(answer, answer_key)
    if qtype == "blank":
        if answer_key.get("blanks"):
            earned, max_pts = score_blank_multi(answer, answer_key)
            if max_pts <= 0:
                return None, False
            return earned / max_pts, False
        return score_blank_legacy(answer, answer_key)
    return None, False


def question_max_score(q: dict) -> float:
    qtype = q["qtype"]
    key = json.loads(q["answer_key_json"]) if isinstance(q.get("answer_key_json"), str) else (q.get("answer_key_json") or {})
    if qtype == "blank" and key.get("blanks"):
        return sum(float(b.get("score") or 0) for b in key["blanks"])
    return float(q["score"])


def compute_attempt_scores(
    questions: list[dict],
    answers_map: dict[int, Any],
) -> tuple[float, float, int, dict[str, Optional[float]], list[dict]]:
    """
    返回 (objective_score, max_objective_score, subjective_pending_count,
          question_scores_map, per_question_details)
    question_scores_map: qid_str -> score or None(待批)
    """
    objective = 0.0
    max_objective = 0.0
    pending = 0
    q_scores: dict[str, Optional[float]] = {}
    details: list[dict] = []

    for q in questions:
        qid = q["id"]
        qtype = q["qtype"]
        key = json.loads(q["answer_key_json"]) if isinstance(q.get("answer_key_json"), str) else (q.get("answer_key_json") or {})
        raw = answers_map.get(qid)
        max_q = question_max_score(q)

        if qtype == "short":
            pending += 1
            q_scores[str(qid)] = None
            details.append({"question_id": qid, "score": None, "needs_grading": True, "max_score": max_q})
            continue

        if qtype == "blank" and key.get("blanks"):
            earned, max_pts = score_blank_multi(raw, key)
            max_objective += max_pts
            objective += earned
            q_scores[str(qid)] = earned
            details.append({
                "question_id": qid, "score": earned, "needs_grading": False, "max_score": max_pts,
            })
            continue

        ratio, needs_grading = score_question(qtype, raw, key)
        max_objective += max_q
        if needs_grading or ratio is None:
            q_scores[str(qid)] = None
            details.append({"question_id": qid, "score": None, "needs_grading": needs_grading, "max_score": max_q})
            continue
        got = round(max_q * ratio, 2)
        objective += got
        q_scores[str(qid)] = got
        details.append({
            "question_id": qid, "score": got, "needs_grading": False, "max_score": max_q,
        })

    return round(objective, 2), round(max_objective, 2), pending, q_scores, details
