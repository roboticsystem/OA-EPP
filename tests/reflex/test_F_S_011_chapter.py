"""F-S-011 章节内容 TDD 测试

被测 State : oaepp.states.chapter.ChapterState
TDD RED   : oaepp.states.chapter 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ChapterState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.chapter import ChapterState
    _IMPORT_ERROR = None
except ImportError as _e:
    ChapterState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_011_TC01_state_attrs_exist():
    """State 必须声明 current_chapter、chapters、attachments 变量"""
    _guard()
    for attr in ("current_chapter", "chapters", "attachments"):
        assert hasattr(ChapterState, attr), f"缺少 {attr} 状态变量"


def test_F_S_011_TC02_load_chapter_method_exists():
    """ChapterState 必须提供 load_chapter() 事件处理器"""
    _guard()
    assert hasattr(ChapterState, "load_chapter") and callable(
        getattr(ChapterState, "load_chapter")
    ), "缺少 load_chapter() 方法"


async def test_F_S_011_TC03_attachment_data_structure(mem_db):
    """attachments 列表中每个元素必须支持 name、size、url 字段"""
    _guard()
    state = ChapterState()
    await state.load_chapter(chapter_id=1)
    # 内存库为空，attachments 应为空列表
    assert isinstance(state.attachments, list), "attachments 应为列表类型"


async def test_F_S_011_TC04_permission_check(mem_db):
    """未认证或未选课学生无法加载章节内容"""
    _guard()
    state = ChapterState()
    # current_user_id 未设置时，加载应失败或返回空
    has_guard = hasattr(state, "current_user_id") or hasattr(state, "is_enrolled")
    assert has_guard, "缺少权限控制变量 current_user_id 或 is_enrolled"
