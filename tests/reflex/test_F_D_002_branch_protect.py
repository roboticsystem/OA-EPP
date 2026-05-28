"""F-D-002 分支保护 TDD 测试

被测 State : oaepp.states.devops_branch.BranchProtectState
TDD RED   : oaepp.states.devops_branch 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : BranchProtectState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_branch import BranchProtectState
    _IMPORT_ERROR = None
except ImportError as _e:
    BranchProtectState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_002_TC01_state_attrs_exist():
    """State 必须声明 protected_branch、require_reviews、min_reviews 变量"""
    _guard()
    for attr in ("protected_branch", "require_reviews", "min_reviews"):
        assert hasattr(BranchProtectState, attr), f"缺少 {attr} 状态变量"


def test_F_D_002_TC02_set_protection_method_exists():
    """BranchProtectState 必须提供 set_branch_protection() 方法"""
    _guard()
    assert hasattr(BranchProtectState, "set_branch_protection") and callable(
        getattr(BranchProtectState, "set_branch_protection")
    ), "缺少 set_branch_protection() 方法"


def test_F_D_002_TC03_force_push_disabled_by_default():
    """allow_force_push 默认应为 False"""
    _guard()
    state = BranchProtectState()
    force_push = getattr(state, "allow_force_push", False)
    assert force_push is False, "allow_force_push 默认应为 False 以保护主分支"


def test_F_D_002_TC04_min_reviews_default():
    """min_reviews 默认值应 >= 1"""
    _guard()
    state = BranchProtectState()
    assert state.min_reviews >= 1, "min_reviews 默认值应至少为 1"
