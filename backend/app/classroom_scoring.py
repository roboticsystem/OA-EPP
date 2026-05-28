"""课堂考试客观题自动评分（F-S-053）。"""
import json
import re
from typing import Any, Optional


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip().lower())


def score_single(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    """单选：answer 为选项字母或索引字符串。"""
    correct = key.get("correct")
    if correct is None and "correct_index" in key:
        correct = str(key["correct_index"])
    if correct is None:
        return None, False
    return (1.0 if str(answer).strip().upper() == str(correct).strip().upper() else 0.0), False


def score_multi(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    """多选：全对才满分，部分对可配置 partial（默认无部分分）。"""
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


def score_blank(answer: Any, key: dict) -> tuple[Optional[float], bool]:
    """填空：支持多个可接受答案、忽略大小写与首尾空白。"""
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


def score_question(qtype: str, answer: Any, answer_key: dict) -> tuple[Optional[float], bool]:
    """
    返回 (得分比例 0~1 或 None, needs_grading)。
    最终题目得分 = 比例 * question.score，由调用方计算。
    """
    if qtype == "short":
        return None, True
    if qtype == "single":
        return score_single(answer, answer_key)
    if qtype == "multi":
        return score_multi(answer, answer_key)
    if qtype == "blank":
        return score_blank(answer, answer_key)
    return None, False


def compute_attempt_scores(
    questions: list[dict],
    answers_map: dict[int, Any],
) -> tuple[float, float, int, list[dict]]:
    """
    计算一次作答的分数。
    返回 (objective_score, max_objective_score, subjective_pending_count, per_question_results)
    """
    objective = 0.0
    max_objective = 0.0
    pending = 0
    details: list[dict] = []

    for q in questions:
        qid = q["id"]
        qscore = float(q["score"])
        qtype = q["qtype"]
        key = json.loads(q["answer_key_json"]) if isinstance(q.get("answer_key_json"), str) else (q.get("answer_key_json") or {})
        raw = answers_map.get(qid)

        ratio, needs_grading = score_question(qtype, raw, key)
        if needs_grading:
            pending += 1
            details.append({
                "question_id": qid,
                "score": None,
                "needs_grading": True,
                "max_score": qscore,
            })
            continue

        max_objective += qscore
        if ratio is None:
            details.append({"question_id": qid, "score": None, "needs_grading": False, "max_score": qscore})
            continue
        got = round(qscore * ratio, 2)
        objective += got
        details.append({
            "question_id": qid,
            "score": got,
            "needs_grading": False,
            "max_score": qscore,
        })

    return round(objective, 2), round(max_objective, 2), pending, details
