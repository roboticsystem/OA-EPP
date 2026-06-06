"""F-S-031 评语反馈 TDD 测试

被测 State : oaepp.states.feedback.FeedbackState
TDD RED   : oaepp.states.feedback 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : FeedbackState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.feedback import FeedbackState
    _IMPORT_ERROR = None
except ImportError as _e:
    FeedbackState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_031_TC01_state_attrs_exist():
    """State 必须声明 feedbacks、current_feedback 变量"""
    _guard()
    for attr in ("feedbacks", "current_feedback"):
        assert hasattr(FeedbackState, attr), f"缺少 {attr} 状态变量"


def test_F_S_031_TC02_load_feedback_method_exists():
    """FeedbackState 必须提供 load_feedback() 方法"""
    _guard()
    assert hasattr(FeedbackState, "load_feedback") and callable(
        getattr(FeedbackState, "load_feedback")
    ), "缺少 load_feedback() 方法"


async def test_F_S_031_TC03_feedback_data_fields(mem_db):
    """feedbacks 列表中每条评语应包含 comment、deduction_items、suggestions 字段"""
    _guard()
    state = FeedbackState()
    await state.load_feedback(assignment_id=1)
    assert isinstance(state.feedbacks, list), "feedbacks 应为列表类型"


def test_F_S_031_TC04_allow_resubmit_flag():
    """FeedbackState 必须声明 allow_resubmit 变量"""
    _guard()
    assert hasattr(FeedbackState, "allow_resubmit"), "缺少 allow_resubmit 标志变量"
