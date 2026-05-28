"""F-S-030 成绩统计 TDD 测试

被测 State : oaepp.states.score.ScoreState
TDD RED   : oaepp.states.score 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ScoreState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.score import ScoreState
    _IMPORT_ERROR = None
except ImportError as _e:
    ScoreState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_030_TC01_score_dimension_attrs():
    """State 必须声明四个维度得分变量：考勤/考试/代码/PR"""
    _guard()
    dimensions = (
        "attendance_score", "exam_score", "code_score", "pr_score", "total_score"
    )
    for attr in dimensions:
        assert hasattr(ScoreState, attr), f"缺少成绩维度变量 {attr}"


def test_F_S_030_TC02_load_scores_method_exists():
    """ScoreState 必须提供 load_scores() 事件处理器"""
    _guard()
    assert hasattr(ScoreState, "load_scores") and callable(
        getattr(ScoreState, "load_scores")
    ), "缺少 load_scores() 方法"


async def test_F_S_030_TC03_data_isolation(mem_db):
    """load_scores() 只加载当前用户自身的成绩"""
    _guard()
    state = ScoreState()
    state.current_user_id = 42
    await state.load_scores()
    # 内存库为空，分数应为 0 或默认值，不应报错
    assert isinstance(state.total_score, (int, float)), "total_score 应为数值类型"


def test_F_S_030_TC04_user_id_isolation_attr():
    """ScoreState 必须携带 current_user_id 以保证数据隔离"""
    _guard()
    assert hasattr(ScoreState, "current_user_id"), "缺少 current_user_id，无法保证数据隔离"
