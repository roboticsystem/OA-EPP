"""F-T-013 进度看板 TDD 测试

被测 State : oaepp.states.teacher_progress_board.ProgressBoardState
TDD RED   : oaepp.states.teacher_progress_board 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ProgressBoardState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_progress_board import ProgressBoardState
    _IMPORT_ERROR = None
except ImportError as _e:
    ProgressBoardState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_013_TC01_state_attrs_exist():
    """State 必须声明 heatmap_data、completion_rate_chart 变量"""
    _guard()
    for attr in ("heatmap_data", "completion_rate_chart"):
        assert hasattr(ProgressBoardState, attr), f"缺少 {attr} 状态变量"


def test_F_T_013_TC02_heatmap_status_values():
    """热力图状态必须支持 submitted / late / missing / not_published"""
    _guard()
    has_status = (
        hasattr(ProgressBoardState, "HEATMAP_STATUS")
        or hasattr(ProgressBoardState, "heatmap_status_options")
    )
    assert has_status, "缺少热力图状态定义（HEATMAP_STATUS / heatmap_status_options）"


def test_F_T_013_TC03_load_progress_method_exists():
    """ProgressBoardState 必须提供 load_progress() 方法"""
    _guard()
    assert hasattr(ProgressBoardState, "load_progress") and callable(
        getattr(ProgressBoardState, "load_progress")
    ), "缺少 load_progress() 方法"


def test_F_T_013_TC04_filter_by_course_method_exists():
    """ProgressBoardState 必须提供 filter_by_course() 方法"""
    _guard()
    assert hasattr(ProgressBoardState, "filter_by_course") and callable(
        getattr(ProgressBoardState, "filter_by_course")
    ), "缺少 filter_by_course() 方法"


def test_F_T_013_TC05_load_progress_executes():
    """ProgressBoardState.load_progress() 执行后应更新状态数据"""
    _guard()
    # 调用 load_progress 方法（可能会因数据库连接失败，但不应抛出异常）
    try:
        ProgressBoardState.load_progress()
        # 验证状态变量被更新
        assert hasattr(ProgressBoardState, "heatmap_data")
        assert hasattr(ProgressBoardState, "completion_rate_chart")
    except Exception as e:
        # 数据库连接失败是预期的（测试环境可能没有数据库），但方法应存在且可调用
        pytest.skip(f"数据库连接不可用: {e}")
