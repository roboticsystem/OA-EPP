"""F-D-007 PR 审查提示词 TDD 测试

被测 State : oaepp.states.devops_review.PRReviewState
TDD RED   : oaepp.states.devops_review 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : PRReviewState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_review import PRReviewState
    _IMPORT_ERROR = None
except ImportError as _e:
    PRReviewState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_007_TC01_state_attrs_exist():
    """State 必须声明 templates、active_template、dry_run_result 变量"""
    _guard()
    for attr in ("templates", "active_template", "dry_run_result"):
        assert hasattr(PRReviewState, attr), f"缺少 {attr} 状态变量"


def test_F_D_007_TC02_three_builtin_templates():
    """内置提示词模板数量应 >= 3"""
    _guard()
    has_builtins = (
        hasattr(PRReviewState, "BUILTIN_TEMPLATES")
        or hasattr(PRReviewState, "DEFAULT_TEMPLATES")
    )
    assert has_builtins, "缺少内置模板常量（BUILTIN_TEMPLATES / DEFAULT_TEMPLATES）"
    builtin = getattr(PRReviewState, "BUILTIN_TEMPLATES", None) or getattr(
        PRReviewState, "DEFAULT_TEMPLATES", []
    )
    assert len(builtin) >= 3, f"内置模板数量 {len(builtin)} < 3"


def test_F_D_007_TC03_save_template_method_exists():
    """PRReviewState 必须提供 save_template() 方法"""
    _guard()
    assert hasattr(PRReviewState, "save_template") and callable(
        getattr(PRReviewState, "save_template")
    ), "缺少 save_template() 方法"


def test_F_D_007_TC04_set_default_template_method_exists():
    """PRReviewState 必须提供 set_default_template() 方法"""
    _guard()
    assert hasattr(PRReviewState, "set_default_template") and callable(
        getattr(PRReviewState, "set_default_template")
    ), "缺少 set_default_template() 方法"


def test_F_D_007_TC05_dry_run_method_exists():
    """PRReviewState 必须提供 dry_run_review() 预览方法"""
    _guard()
    assert hasattr(PRReviewState, "dry_run_review") and callable(
        getattr(PRReviewState, "dry_run_review")
    ), "缺少 dry_run_review() 方法"
