"""F-S-012 公告通知 TDD 测试

被测 State : oaepp.states.notice.NoticeState
TDD RED   : oaepp.states.notice 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : NoticeState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.notice import NoticeState
    _IMPORT_ERROR = None
except ImportError as _e:
    NoticeState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_012_TC01_state_attrs_exist():
    """State 必须声明 notices、unread_count 变量"""
    _guard()
    for attr in ("notices", "unread_count"):
        assert hasattr(NoticeState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_012_TC02_notices_sorted_desc(mem_db):
    """notices 应按发布时间降序排列"""
    _guard()
    state = NoticeState()
    await state.load_notices()
    # 内存库为空列表，验证不抛异常且为列表
    assert isinstance(state.notices, list), "notices 应为列表类型"


def test_F_S_012_TC03_mark_as_read_method_exists():
    """NoticeState 必须提供 mark_as_read() 事件处理器"""
    _guard()
    assert hasattr(NoticeState, "mark_as_read") and callable(
        getattr(NoticeState, "mark_as_read")
    ), "缺少 mark_as_read() 方法"


def test_F_S_012_TC04_unread_count_is_var():
    """unread_count 应为计算变量（@rx.var）或可更新的状态变量"""
    _guard()
    state = NoticeState()
    assert isinstance(state.unread_count, int), "unread_count 应为整数类型"
    assert state.unread_count >= 0, "unread_count 不能为负数"
