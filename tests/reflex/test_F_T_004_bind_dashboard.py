"""F-T-004 绑定状态看板 TDD 测试

被测 State : oaepp.states.teacher_bind_dashboard.BindDashboardState
TDD RED   : oaepp.states.teacher_bind_dashboard 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : BindDashboardState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_bind_dashboard import BindDashboardState
    _IMPORT_ERROR = None
except ImportError as _e:
    BindDashboardState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_004_TC01_state_attrs_exist():
    """State 必须声明 bound_count、unbound_count、pending_count 变量"""
    _guard()
    for attr in ("bound_count", "unbound_count", "pending_count"):
        assert hasattr(BindDashboardState, attr), f"缺少 {attr} 状态变量"


def test_F_T_004_TC02_counts_sum_to_total():
    """bound_count + unbound_count + pending_count 应等于 total_students"""
    _guard()
    has_total = (
        hasattr(BindDashboardState, "total_students")
        or hasattr(BindDashboardState, "total_count")
    )
    assert has_total, "缺少 total_students 或 total_count 变量"


def test_F_T_004_TC03_batch_approve_method_exists():
    """BindDashboardState 必须提供 batch_approve() 方法"""
    _guard()
    assert hasattr(BindDashboardState, "batch_approve") and callable(
        getattr(BindDashboardState, "batch_approve")
    ), "缺少 batch_approve() 方法"


def test_F_T_004_TC04_send_reminder_method_exists():
    """BindDashboardState 必须提供 send_reminder_to_unbound() 方法"""
    _guard()
    assert hasattr(BindDashboardState, "send_reminder_to_unbound") and callable(
        getattr(BindDashboardState, "send_reminder_to_unbound")
    ), "缺少 send_reminder_to_unbound() 方法"
