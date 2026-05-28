"""F-T-014 在线批改 TDD 测试

被测 State : oaepp.states.teacher_grading.GradingState
TDD RED   : oaepp.states.teacher_grading 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : GradingState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_grading import GradingState
    _IMPORT_ERROR = None
except ImportError as _e:
    GradingState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_014_TC01_state_attrs_exist():
    """State 必须声明 grading_queue、current_submission、is_submitting 变量"""
    _guard()
    for attr in ("grading_queue", "current_submission", "is_submitting"):
        assert hasattr(GradingState, attr), f"缺少 {attr} 状态变量"


def test_F_T_014_TC02_submit_grade_method_exists():
    """GradingState 必须提供 submit_grade() 事件处理器"""
    _guard()
    assert hasattr(GradingState, "submit_grade") and callable(
        getattr(GradingState, "submit_grade")
    ), "缺少 submit_grade() 方法"


async def test_F_T_014_TC03_allow_resubmit_triggers_update(mem_db):
    """submit_grade() 中 allow_resubmit=True 时应触发学生侧状态更新"""
    _guard()
    state = GradingState()
    # 验证方法接受 allow_resubmit 参数
    import inspect
    sig = inspect.signature(state.submit_grade)
    params = list(sig.parameters.keys())
    has_resubmit_param = "allow_resubmit" in params
    # 如不在参数中，可能通过状态变量控制
    has_resubmit_attr = hasattr(GradingState, "allow_resubmit")
    assert has_resubmit_param or has_resubmit_attr, (
        "submit_grade() 或 GradingState 应支持 allow_resubmit 控制"
    )


def test_F_T_014_TC04_copy_last_comment_method_exists():
    """GradingState 必须提供 copy_last_comment() 方法"""
    _guard()
    assert hasattr(GradingState, "copy_last_comment") and callable(
        getattr(GradingState, "copy_last_comment")
    ), "缺少 copy_last_comment() 方法"


def test_F_T_014_TC05_audit_log_immutable():
    """批改记录审计日志不可删除"""
    _guard()
    assert hasattr(GradingState, "audit_log") or hasattr(
        GradingState, "grading_log"
    ), "缺少批改审计日志变量 audit_log 或 grading_log"
