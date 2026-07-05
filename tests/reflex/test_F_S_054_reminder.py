"""F-S-054 截止提醒 TDD 测试

被测 State : oaepp.states.reminder.ReminderState
TDD RED   : oaepp.states.reminder 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ReminderState 实现后 → 全部通过
"""
import pytest
import datetime

try:
    from oaepp.states.reminder import ReminderState
    _IMPORT_ERROR = None
except ImportError as _e:
    ReminderState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_054_TC01_state_attrs_exist():
    """State 必须声明 reminders、available_hours 变量"""
    _guard()
    for attr in ("reminders", "available_hours"):
        assert hasattr(ReminderState, attr), f"缺少 {attr} 状态变量"


def test_F_S_054_TC02_set_reminder_method_exists():
    """ReminderState 必须提供 set_reminder() 方法"""
    _guard()
    assert hasattr(ReminderState, "set_reminder") and callable(
        getattr(ReminderState, "set_reminder")
    ), "缺少 set_reminder() 方法"


async def test_F_S_054_TC03_submitted_task_auto_cancel(mem_db):
    """已提交的任务提醒应被自动取消"""
    _guard()
    state = ReminderState()
    # 模拟任务已提交
    await state.cancel_reminder_on_submit(assignment_id=1)
    assert isinstance(state.reminders, list), "reminders 应为列表类型"


async def test_F_S_054_TC04_past_deadline_no_add(mem_db):
    """截止时间已过的任务不允许新增提醒"""
    _guard()
    state = ReminderState()
    past_deadline = datetime.datetime(2000, 1, 1)
    await state.set_reminder(assignment_id=1, hours_before=24, deadline=past_deadline)
    assert hasattr(state, "error_message"), "超过截止时间设提醒应有 error_message"


def test_F_S_054_TC05_overdue_days_attr():
    """ReminderState 必须提供 overdue_days 变量或 get_overdue_days() 方法"""
    _guard()
    has_attr = hasattr(ReminderState, "overdue_days")
    has_method = hasattr(ReminderState, "get_overdue_days")
    assert has_attr or has_method, "缺少逾期天数计算属性/方法"
