"""F-S-022 截止时间规则 TDD 测试

被测 State : oaepp.states.deadline.DeadlineState
TDD RED   : oaepp.states.deadline 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : DeadlineState 实现后 → 全部通过
"""
import pytest
import datetime

try:
    from oaepp.states.deadline import DeadlineState
    _IMPORT_ERROR = None
except ImportError as _e:
    DeadlineState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_022_TC01_state_attrs_exist():
    """State 必须声明 deadline、is_past_deadline、late_flag 变量"""
    _guard()
    for attr in ("deadline", "is_past_deadline", "late_flag"):
        assert hasattr(DeadlineState, attr), f"缺少 {attr} 状态变量"


def test_F_S_022_TC02_before_deadline_allowed():
    """截止时间前 is_past_deadline 应为 False"""
    _guard()
    state = DeadlineState()
    state.deadline = datetime.datetime(2099, 12, 31)
    # 触发重新计算（实际实现可能是 @rx.var）
    if hasattr(state, "check_deadline"):
        state.check_deadline()
    assert state.is_past_deadline is False, "截止时间未到时 is_past_deadline 应为 False"


def test_F_S_022_TC03_after_deadline_flag():
    """截止时间后 is_past_deadline 应为 True"""
    _guard()
    state = DeadlineState()
    state.deadline = datetime.datetime(2000, 1, 1)
    if hasattr(state, "check_deadline"):
        state.check_deadline()
    assert state.is_past_deadline is True, "截止时间已过时 is_past_deadline 应为 True"


def test_F_S_022_TC04_policy_attr_exists():
    """State 必须声明 deadline_policy 变量（block / mark_late）"""
    _guard()
    assert hasattr(DeadlineState, "deadline_policy"), "缺少 deadline_policy 状态变量"
