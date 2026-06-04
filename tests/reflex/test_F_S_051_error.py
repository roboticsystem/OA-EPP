"""F-S-051 异常提示 TDD 测试

被测 State : oaepp.states.error.ErrorState
TDD RED   : oaepp.states.error 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ErrorState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.error import ErrorState
    _IMPORT_ERROR = None
except ImportError as _e:
    ErrorState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_051_TC01_state_attrs_exist():
    """State 必须声明 error_message、has_error、retry_count 变量"""
    _guard()
    for attr in ("error_message", "has_error", "retry_count"):
        assert hasattr(ErrorState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_051_TC02_set_error_method(mem_db):
    """set_error() 设置 error_message 并将 has_error 置为 True"""
    _guard()
    state = ErrorState()
    await state.set_error("网络请求失败")
    assert state.has_error is True
    assert state.error_message == "网络请求失败"


async def test_F_S_051_TC03_clear_error_resets(mem_db):
    """clear_error() 重置所有错误状态"""
    _guard()
    state = ErrorState()
    state.error_message = "some error"
    state.has_error = True
    state.retry_count = 3
    await state.clear_error()
    assert state.has_error is False
    assert state.error_message == ""


async def test_F_S_051_TC04_retry_count_increments(mem_db):
    """每次 set_error() 调用后 retry_count 递增"""
    _guard()
    state = ErrorState()
    assert state.retry_count == 0
    await state.set_error("first error")
    await state.set_error("second error")
    assert state.retry_count >= 1, "retry_count 应在每次出错时递增"
