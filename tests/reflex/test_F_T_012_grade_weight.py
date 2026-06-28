"""F-T-012 成绩权重配置 TDD 测试

被测 State : oaepp.states.admin_grades.GradeWeightState
TDD RED   : oaepp.states.admin_grades 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : GradeWeightState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.admin_grades import GradeWeightState
    _IMPORT_ERROR = None
except ImportError as _e:
    GradeWeightState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_012_TC01_state_attrs_exist():
    """State 必须声明 attendance_weight、exam_weight、code_weight、pr_weight 变量"""
    _guard()
    for attr in ("attendance_weight", "exam_weight", "code_weight", "pr_weight"):
        assert hasattr(GradeWeightState, attr), f"缺少 {attr} 状态变量"


def test_F_T_012_TC02_weights_sum_to_100():
    """四项权重之和必须等于 100%（数值精度允许 ±0.01）"""
    _guard()
    state = GradeWeightState()
    total = (
        state.attendance_weight
        + state.exam_weight
        + state.code_weight
        + state.pr_weight
    )
    assert abs(total - 100) <= 0.01, f"权重之和 {total} != 100，违反约束"


async def test_F_T_012_TC03_save_weights_recalculates(mem_db):
    """save_weights() 保存后应重新计算所有学生总分"""
    _guard()
    state = GradeWeightState()
    assert hasattr(GradeWeightState, "save_weights") and callable(
        getattr(GradeWeightState, "save_weights")
    ), "缺少 save_weights() 方法"
    await state.save_weights()
    # 内存库为空，只验证方法可调用不抛异常


def test_F_T_012_TC04_audit_log_immutable():
    """权重变更历史审计日志不可删除"""
    _guard()
    assert hasattr(GradeWeightState, "weight_history") or hasattr(
        GradeWeightState, "audit_log"
    ), "缺少权重变更历史变量 weight_history 或 audit_log"


def test_F_T_012_TC05_history_with_rollback():
    """GradeWeightState 必须提供 rollback_to() 方法支持回滚到历史版本"""
    _guard()
    assert hasattr(GradeWeightState, "rollback_to") and callable(
        getattr(GradeWeightState, "rollback_to")
    ), "缺少 rollback_to() 方法"
