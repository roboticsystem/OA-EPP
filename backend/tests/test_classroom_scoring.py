"""F-S-053 客观题评分单元测试"""
import pytest
from app.classroom_scoring import (
    score_single,
    score_multi,
    score_blank,
    score_question,
    compute_attempt_scores,
)


def test_single_correct():
    ratio, ng = score_single("A", {"correct": "A"})
    assert ratio == 1.0 and not ng


def test_single_wrong():
    ratio, ng = score_single("B", {"correct": "A"})
    assert ratio == 0.0


def test_multi_full():
    ratio, ng = score_multi(["A", "C"], {"correct": ["A", "C"]})
    assert ratio == 1.0


def test_multi_wrong():
    ratio, ng = score_multi(["A"], {"correct": ["A", "C"]})
    assert ratio == 0.0


def test_blank_acceptable():
    ratio, ng = score_blank("Hello", {"acceptable": ["hello", "HELLO"]})
    assert ratio == 1.0


def test_short_needs_grading():
    ratio, ng = score_question("short", "任意文字", {})
    assert ratio is None and ng


def test_compute_attempt_scores():
    questions = [
        {"id": 1, "qtype": "single", "score": 2, "answer_key_json": '{"correct":"A"}'},
        {"id": 2, "qtype": "short", "score": 5, "answer_key_json": "{}"},
    ]
    obj, max_obj, pending, _ = compute_attempt_scores(questions, {1: "A", 2: "简答内容"})
    assert obj == 2.0
    assert max_obj == 2.0
    assert pending == 1
