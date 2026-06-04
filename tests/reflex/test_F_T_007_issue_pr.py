"""F-T-007 Issue-PR 关联规则 TDD 测试

被测 State : oaepp.states.teacher_issue_pr.IssuePRState
TDD RED   : oaepp.states.teacher_issue_pr 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : IssuePRState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_issue_pr import IssuePRState
    _IMPORT_ERROR = None
except ImportError as _e:
    IssuePRState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_007_TC01_state_attrs_exist():
    """State 必须声明 rule_enabled、close_issue_requires_pr 变量"""
    _guard()
    for attr in ("rule_enabled", "close_issue_requires_pr"):
        assert hasattr(IssuePRState, attr), f"缺少 {attr} 状态变量"


async def test_F_T_007_TC02_close_issue_without_pr_blocked(mem_db):
    """规则启用时关闭 Issue 但无关联 PR → 操作被阻止"""
    _guard()
    state = IssuePRState()
    state.rule_enabled = True
    result = await state.validate_issue_close(issue_id=1, linked_pr_id=None)
    assert result is False or result == "blocked", (
        "无 PR 关联时关闭 Issue 应被阻止（返回 False 或 'blocked'）"
    )


async def test_F_T_007_TC03_close_issue_with_pr_allowed(mem_db):
    """规则启用且有关联 PR → 操作允许"""
    _guard()
    state = IssuePRState()
    state.rule_enabled = True
    result = await state.validate_issue_close(issue_id=1, linked_pr_id=42)
    assert result is True or result == "allowed", (
        "有 PR 关联时关闭 Issue 应被允许（返回 True 或 'allowed'）"
    )


def test_F_T_007_TC04_webhook_handler_method_exists():
    """IssuePRState 必须提供 handle_issue_closed_webhook() 方法"""
    _guard()
    assert hasattr(IssuePRState, "handle_issue_closed_webhook") and callable(
        getattr(IssuePRState, "handle_issue_closed_webhook")
    ), "缺少 handle_issue_closed_webhook() 方法"


def test_F_T_007_TC05_warning_log_attr():
    """IssuePRState 必须声明 warning_log 变量记录缺失 PR 的情况"""
    _guard()
    assert hasattr(IssuePRState, "warning_log") or hasattr(
        IssuePRState, "violation_log"
    ), "缺少违规记录变量 warning_log 或 violation_log"
