"""F-S-052 课堂点名 TDD 测试

被测 State : oaepp.states.attendance.AttendanceState
TDD RED   : oaepp.states.attendance 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : AttendanceState 实现后 → 全部通过
"""
import pytest
import datetime

try:
    from oaepp.states.attendance import AttendanceState
    _IMPORT_ERROR = None
except ImportError as _e:
    AttendanceState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_052_TC01_state_attrs_exist():
    """State 必须声明 session_id、confirm_deadline、attendance_status 变量"""
    _guard()
    for attr in ("session_id", "confirm_deadline", "attendance_status"):
        assert hasattr(AttendanceState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_052_TC02_confirm_in_window(mem_db):
    """在签到窗口内确认 → attendance_status = present"""
    _guard()
    state = AttendanceState()
    state.confirm_deadline = datetime.datetime(2099, 12, 31)
    await state.confirm_attendance(session_id=1)
    valid_statuses = ("present", "confirmed", "on_time")
    assert state.attendance_status in valid_statuses, (
        f"窗口内签到后 attendance_status='{state.attendance_status}' 不在 {valid_statuses} 中"
    )


async def test_F_S_052_TC03_confirm_late_flag(mem_db):
    """超过签到截止时间确认 → attendance_status = late"""
    _guard()
    state = AttendanceState()
    state.confirm_deadline = datetime.datetime(2000, 1, 1)
    await state.confirm_attendance(session_id=1)
    assert state.attendance_status in ("late", "absent", "timeout"), (
        "截止后签到应标记为 late 或 absent"
    )


def test_F_S_052_TC04_status_enum_values():
    """attendance_status 应支持 present / late / absent 三种值"""
    _guard()
    state = AttendanceState()
    # 默认状态不得是未定义值
    assert state.attendance_status in ("present", "late", "absent", "pending", "unknown", ""), (
        f"attendance_status 默认值 '{state.attendance_status}' 无效"
    )


def test_F_S_052_TC05_own_history_only():
    """AttendanceState 必须携带 current_user_id 确保只看自身记录"""
    _guard()
    assert hasattr(AttendanceState, "current_user_id"), "缺少 current_user_id 隔离变量"
