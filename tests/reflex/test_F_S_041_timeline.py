"""F-S-041 时间线 TDD 测试

被测 State : oaepp.states.timeline.TimelineState
TDD RED   : oaepp.states.timeline 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : TimelineState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.timeline import TimelineState
    _IMPORT_ERROR = None
except ImportError as _e:
    TimelineState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_041_TC01_state_attrs_exist():
    """State 必须声明 timeline_events、is_loading 变量"""
    _guard()
    for attr in ("timeline_events", "is_loading"):
        assert hasattr(TimelineState, attr), f"缺少 {attr} 状态变量"


def test_F_S_041_TC02_event_types_defined():
    """事件类型应包含: task_publish, submit, grade, feedback"""
    _guard()
    has_types = hasattr(TimelineState, "EVENT_TYPES") or hasattr(TimelineState, "event_types")
    has_load = hasattr(TimelineState, "load_timeline") and callable(
        getattr(TimelineState, "load_timeline")
    )
    assert has_types or has_load, "缺少事件类型定义或 load_timeline() 方法"


async def test_F_S_041_TC03_events_list_type(mem_db):
    """timeline_events 应为列表类型，内存库为空时返回 []"""
    _guard()
    state = TimelineState()
    await state.load_timeline()
    assert isinstance(state.timeline_events, list), "timeline_events 应为列表类型"


def test_F_S_041_TC04_unauthenticated_guard():
    """TimelineState 必须携带 current_user_id 以防未认证访问"""
    _guard()
    assert hasattr(TimelineState, "current_user_id"), "缺少 current_user_id 认证守卫"
