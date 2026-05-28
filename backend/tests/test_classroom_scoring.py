"""F-S-053 客观题评分单元测试"""
import pytest
from app.classroom_scoring import (
    score_single,
    score_multi,
    score_blank_multi,
    score_question,
    compute_attempt_scores,
)


def test_single_correct():
    ratio, ng = score_single("A", {"correct": "A"})
    assert ratio == 1.0 and not ng


def test_multi_full():
    ratio, ng = score_multi(["A", "C"], {"correct": ["A", "C"]})
    assert ratio == 1.0


def test_blank_multi():
    key = {
        "blanks": [
            {"acceptable": ["hello"], "score": 2},
            {"acceptable": ["world", "WORLD"], "score": 3},
        ]
    }
    earned, max_pts = score_blank_multi(["hello", "world"], key)
    assert earned == 5.0 and max_pts == 5.0


def test_short_needs_grading():
    ratio, ng = score_question("short", "任意文字", {})
    assert ratio is None and ng


def test_compute_with_blanks():
    questions = [
        {
            "id": 1,
            "qtype": "single",
            "score": 2,
            "answer_key_json": '{"correct":"A"}',
        },
        {
            "id": 2,
            "qtype": "blank",
            "score": 5,
            "answer_key_json": '{"blanks":[{"acceptable":["x"],"score":5}]}',
        },
        {
            "id": 3,
            "qtype": "short",
            "score": 10,
            "answer_key_json": "{}",
        },
    ]
    obj, max_obj, pending, q_scores, _ = compute_attempt_scores(
        questions, {1: "A", 2: ["x"], 3: "简答"}
    )
    assert obj == 7.0
    assert max_obj == 7.0
    assert pending == 1
    assert q_scores["1"] == 2.0
    assert q_scores["2"] == 5.0
    assert q_scores["3"] is None
