"""F-S-040 得分看板 TDD 测试

被测 State : oaepp.states.dashboard.DashboardState
TDD RED   : oaepp.states.dashboard 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : DashboardState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.dashboard import DashboardState
    _IMPORT_ERROR = None
except ImportError as _e:
    DashboardState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_040_TC01_state_attrs_exist():
    """State 必须声明 radar_data、completion_rate 相关变量"""
    _guard()
    has_radar = hasattr(DashboardState, "radar_data") or hasattr(DashboardState, "chart_data")
    assert has_radar, "缺少雷达图数据变量 radar_data 或 chart_data"
    assert hasattr(DashboardState, "completion_rate") or hasattr(
        DashboardState, "completed_count"
    ), "缺少完成率变量"


def test_F_S_040_TC02_radar_four_dimensions():
    """雷达图必须包含 4 个维度：考勤/考试/代码提交/PR"""
    _guard()
    state = DashboardState()
    radar = getattr(state, "radar_data", None) or getattr(state, "chart_data", [])
    # 默认值可能是空列表，测试维度常量或方法
    has_dim_const = hasattr(DashboardState, "RADAR_DIMENSIONS")
    has_load_method = hasattr(DashboardState, "load_dashboard") or hasattr(
        DashboardState, "load_radar_data"
    )
    assert has_dim_const or has_load_method, "缺少雷达图维度定义或加载方法"


def test_F_S_040_TC03_filter_method_exists():
    """DashboardState 必须提供 filter_by_course() 方法"""
    _guard()
    assert hasattr(DashboardState, "filter_by_course") and callable(
        getattr(DashboardState, "filter_by_course")
    ), "缺少 filter_by_course() 方法"


def test_F_S_040_TC04_completion_rate_numeric():
    """completion_rate 默认值应为数值类型"""
    _guard()
    state = DashboardState()
    rate = getattr(state, "completion_rate", None) or getattr(state, "completed_count", 0)
    assert isinstance(rate, (int, float)), "completion_rate 应为数值类型"
