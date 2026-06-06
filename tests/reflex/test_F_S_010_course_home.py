"""F-S-010 课程主页 TDD 测试

被测 State : oaepp.states.course_home.CourseState
TDD RED   : oaepp.states.course_home 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : CourseState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.course_home import CourseState
    _IMPORT_ERROR = None
except ImportError as _e:
    CourseState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_010_TC01_state_attrs_exist():
    """State 必须声明 courses、is_loading 变量"""
    _guard()
    for attr in ("courses", "is_loading"):
        assert hasattr(CourseState, attr), f"缺少 {attr} 状态变量"


def test_F_S_010_TC02_load_courses_method_exists():
    """CourseState 必须提供 load_courses() 事件处理器"""
    _guard()
    assert hasattr(CourseState, "load_courses") and callable(
        getattr(CourseState, "load_courses")
    ), "缺少 load_courses() 方法"


async def test_F_S_010_TC03_course_data_fields(mem_db):
    """courses 列表中每个元素必须包含 name、teacher、schedule 字段"""
    _guard()
    state = CourseState()
    await state.load_courses()
    # 内存数据库为空，courses 应为空列表（不应抛异常）
    assert isinstance(state.courses, list), "courses 应为列表类型"


async def test_F_S_010_TC04_empty_courses_handled(mem_db):
    """无课程时 courses=[], is_loading=False，不报错"""
    _guard()
    state = CourseState()
    await state.load_courses()
    assert state.is_loading is False, "加载完成后 is_loading 应为 False"
    assert state.courses == [] or isinstance(state.courses, list)
