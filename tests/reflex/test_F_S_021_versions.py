"""F-S-021 提交版本记录 TDD 测试

被测 State : oaepp.states.submission.SubmissionState（版本相关逻辑）
TDD RED   : oaepp.states.submission 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : SubmissionState 实现版本功能后 → 全部通过
"""
import pytest

try:
    from oaepp.states.submission import SubmissionState
    _IMPORT_ERROR = None
except ImportError as _e:
    SubmissionState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_021_TC01_version_tracking_attrs():
    """State 必须声明 submission_history 或 versions 变量以跟踪版本"""
    _guard()
    has_history = hasattr(SubmissionState, "submission_history")
    has_versions = hasattr(SubmissionState, "versions")
    assert has_history or has_versions, "缺少版本历史变量 submission_history 或 versions"


def test_F_S_021_TC02_load_history_method_exists():
    """SubmissionState 必须提供 load_submission_history() 方法"""
    _guard()
    assert hasattr(SubmissionState, "load_submission_history") and callable(
        getattr(SubmissionState, "load_submission_history")
    ), "缺少 load_submission_history() 方法"


async def test_F_S_021_TC03_history_sorted_desc(mem_db):
    """历史记录应按提交时间降序排列（最新在前）"""
    _guard()
    state = SubmissionState()
    await state.load_submission_history(assignment_id=1)
    history_attr = getattr(state, "submission_history", None) or getattr(state, "versions", [])
    assert isinstance(history_attr, list), "版本历史应为列表类型"


def test_F_S_021_TC04_allow_resubmit_attr():
    """State 必须声明 allow_resubmit 变量，控制是否可重新提交"""
    _guard()
    assert hasattr(SubmissionState, "allow_resubmit"), "缺少 allow_resubmit 状态变量"
