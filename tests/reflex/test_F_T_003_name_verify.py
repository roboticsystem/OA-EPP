"""F-T-003 账号实名核查 TDD 测试

被测 State : oaepp.states.teacher_name_verify.AccountVerifyState
TDD RED   : oaepp.states.teacher_name_verify 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : AccountVerifyState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_name_verify import AccountVerifyState
    _IMPORT_ERROR = None
except ImportError as _e:
    AccountVerifyState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_003_TC01_state_attrs_exist():
    """State 必须声明 verify_results、ai_queue 变量"""
    _guard()
    for attr in ("verify_results", "ai_queue"):
        assert hasattr(AccountVerifyState, attr), f"缺少 {attr} 状态变量"


async def test_F_T_003_TC02_cjk_name_detected(mem_db):
    """全汉字姓名 → AI 判断为疑似真名（suspicious_real_name）"""
    _guard()
    state = AccountVerifyState()
    result = await state.ai_check_name("张三")
    assert result in ("疑似真名", "suspicious_real_name", "real"), (
        f"全汉字姓名应判断为疑似真名，实际返回: {result}"
    )


async def test_F_T_003_TC03_generic_name_flagged(mem_db):
    """student001 类格式 → 标记为待人工审查"""
    _guard()
    state = AccountVerifyState()
    result = await state.ai_check_name("student001")
    assert result in ("待人工审查", "needs_review", "review"), (
        f"student001 格式应标记为待审查，实际返回: {result}"
    )


async def test_F_T_003_TC04_empty_name_flagged(mem_db):
    """空 GitHub 用户名 → 标记为未填写"""
    _guard()
    state = AccountVerifyState()
    result = await state.ai_check_name("")
    assert result in ("未填写", "empty", "not_filled"), (
        f"空用户名应标记为未填写，实际返回: {result}"
    )


def test_F_T_003_TC05_bulk_verify_method_exists():
    """AccountVerifyState 必须提供 bulk_verify_all() 方法"""
    _guard()
    assert hasattr(AccountVerifyState, "bulk_verify_all") and callable(
        getattr(AccountVerifyState, "bulk_verify_all")
    ), "缺少 bulk_verify_all() 方法"
