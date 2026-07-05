"""F-S-053 在线考试 TDD 测试

被测 State : oaepp.states.exam.ExamState
TDD RED   : oaepp.states.exam 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ExamState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.exam import ExamState
    _IMPORT_ERROR = None
except ImportError as _e:
    ExamState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_053_TC01_state_attrs_exist():
    """State 必须声明 questions、answers、time_remaining、exam_status 变量"""
    _guard()
    for attr in ("questions", "answers", "time_remaining", "exam_status"):
        assert hasattr(ExamState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_053_TC02_auto_submit_on_timeout(mem_db):
    """time_remaining 归零时自动提交，exam_status = submitted"""
    _guard()
    state = ExamState()
    state.time_remaining = 0
    await state.tick()  # 或 check_timer()
    submitted_statuses = ("submitted", "finished", "completed", "auto_submitted")
    assert state.exam_status in submitted_statuses, (
        f"倒计时归零后 exam_status='{state.exam_status}' 应为提交状态"
    )


def test_F_S_053_TC03_auto_score_method_exists():
    """ExamState 必须提供 auto_score_objectives() 方法处理客观题自动评分"""
    _guard()
    has_auto = hasattr(ExamState, "auto_score_objectives") and callable(
        getattr(ExamState, "auto_score_objectives")
    )
    has_submit = hasattr(ExamState, "submit_exam") and callable(
        getattr(ExamState, "submit_exam")
    )
    assert has_auto or has_submit, "缺少客观题评分方法 auto_score_objectives() 或 submit_exam()"


def test_F_S_053_TC04_save_draft_method_exists():
    """ExamState 必须提供 save_draft() 方法（答案变更时自动触发）"""
    _guard()
    assert hasattr(ExamState, "save_draft") and callable(
        getattr(ExamState, "save_draft")
    ), "缺少 save_draft() 方法"


def test_F_S_053_TC05_no_cross_student_access():
    """ExamState 必须携带 current_user_id 防止查看他人答案"""
    _guard()
    assert hasattr(ExamState, "current_user_id"), "缺少 current_user_id 防越权变量"
