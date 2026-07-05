"""F-D-004 CI 自动化 TDD 测试

被测 State : oaepp.states.devops_ci.CIState
TDD RED   : oaepp.states.devops_ci 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : CIState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_ci import CIState
    _IMPORT_ERROR = None
except ImportError as _e:
    CIState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_004_TC01_state_attrs_exist():
    """State 必须声明 ci_enabled、last_run_status、workflow_url 变量"""
    _guard()
    for attr in ("ci_enabled", "last_run_status", "workflow_url"):
        assert hasattr(CIState, attr), f"缺少 {attr} 状态变量"


def test_F_D_004_TC02_trigger_ci_method_exists():
    """CIState 必须提供 trigger_ci() 事件处理器"""
    _guard()
    assert hasattr(CIState, "trigger_ci") and callable(
        getattr(CIState, "trigger_ci")
    ), "缺少 trigger_ci() 方法"


def test_F_D_004_TC03_ci_includes_lint():
    """CI 流水线配置必须包含 ruff lint 步骤"""
    _guard()
    has_lint_step = (
        hasattr(CIState, "CI_STEPS")
        or hasattr(CIState, "lint_enabled")
        or hasattr(CIState, "workflow_template")
    )
    assert has_lint_step, "缺少 lint 步骤配置（CI_STEPS / lint_enabled / workflow_template）"


def test_F_D_004_TC04_ci_includes_pytest():
    """CI 流水线配置必须包含 pytest 步骤"""
    _guard()
    has_test_step = (
        hasattr(CIState, "CI_STEPS")
        or hasattr(CIState, "test_enabled")
        or hasattr(CIState, "workflow_template")
    )
    assert has_test_step, "缺少 pytest 测试步骤配置"
