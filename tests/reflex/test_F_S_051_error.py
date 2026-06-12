"""F-S-051 异常提示 TDD 测试

被测模块 : oaepp.states.error.ErrorState
          oaepp.utils.error_handler.handle_error
TDD RED   : 模块不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.error import ErrorState
    _ERR_STATE_IMPORT_ERROR = None
except ImportError as _e:
    ErrorState = None
    _ERR_STATE_IMPORT_ERROR = str(_e)

try:
    from oaepp.utils.error_handler import handle_error, ErrorCode, ErrorSeverity, ERROR_MESSAGES, ERROR_POLICY
    _HANDLER_IMPORT_ERROR = None
except ImportError as _e:
    handle_error = None
    ErrorCode = None
    ErrorSeverity = None
    ERROR_MESSAGES = None
    ERROR_POLICY = None
    _HANDLER_IMPORT_ERROR = str(_e)


def _guard_err():
    if _ERR_STATE_IMPORT_ERROR:
        pytest.fail(f"TDD RED (ErrorState): {_ERR_STATE_IMPORT_ERROR}")

def _guard_handler():
    if _HANDLER_IMPORT_ERROR:
        pytest.fail(f"TDD RED (error_handler): {_HANDLER_IMPORT_ERROR}")


# ══════════════════════════════════════════════════════════
#  ErrorState 测试
# ══════════════════════════════════════════════════════════

def test_F_S_051_TC01_state_attrs_exist():
    """ErrorState 必须声明 current_code, current_message, current_severity, current_visible, retry_label"""
    _guard_err()
    for attr in ("current_code", "current_message", "current_severity",
                 "current_visible", "retry_label", "auto_dismiss_sec"):
        assert hasattr(ErrorState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_051_TC02_show_sets_state(mem_db):
    """show() 设置错误信息并显示 Toast"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.UNKNOWN, "测试错误", ErrorSeverity.ERROR)
    assert state.current_visible is True
    assert state.current_message == "测试错误"
    assert state.current_code == ErrorCode.UNKNOWN


async def test_F_S_051_TC03_dismiss_hides_toast(mem_db):
    """dismiss() 隐藏 Toast 并展示队列中下一个错误"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.UNKNOWN, "第一个错误", ErrorSeverity.ERROR)
    await state.show(ErrorCode.NETWORK_TIMEOUT, "第二个错误", ErrorSeverity.ERROR)
    await state.dismiss()
    assert state.current_visible is True
    assert state.current_message == "第二个错误"
    await state.dismiss()
    assert state.current_visible is False


async def test_F_S_051_TC04_show_stores_retry_info(mem_db):
    """show() 存储重试标签和回调事件名"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.NETWORK_ERROR, "网络异常", ErrorSeverity.ERROR,
                     retry="重试", retry_event="submit_assignment")
    assert state.retry_label == "重试"
    assert state.retry_event == "submit_assignment"


async def test_F_S_051_TC05_dismiss_queue_cleared(mem_db):
    """dismiss() 两次后队列清空，状态重置"""
    _guard_err()
    state = ErrorState()
    state.current_message = "some error"
    state.current_visible = True
    state.retry_label = "重试"
    await state.dismiss()
    await state.dismiss()  # 清空队列
    assert state.current_visible is False
    assert state.current_message == ""


# ══════════════════════════════════════════════════════════
#  handle_error() 测试
# ══════════════════════════════════════════════════════════

def test_F_S_051_TC06_error_messages_complete():
    """ERROR_MESSAGES 覆盖所有 ErrorCode"""
    _guard_handler()
    for code in ErrorCode:
        assert code in ERROR_MESSAGES, f"缺少 {code} 的文案映射"


def test_F_S_051_TC07_error_policy_complete():
    """ERROR_POLICY 覆盖所有 ErrorCode"""
    _guard_handler()
    for code in ErrorCode:
        assert code in ERROR_POLICY, f"缺少 {code} 的策略映射"


def test_F_S_051_TC08_handle_unknown_error():
    """未知异常映射为 UNKNOWN"""
    _guard_handler()
    code, msg, severity, retry = handle_error(Exception("未知错误"))
    assert code == ErrorCode.UNKNOWN
    assert msg == ERROR_MESSAGES[ErrorCode.UNKNOWN]
    assert severity == ErrorSeverity.ERROR


def test_F_S_051_TC09_handle_timeout_error():
    """TimeoutError 映射为 NETWORK_TIMEOUT"""
    _guard_handler()
    code, *_ = handle_error(TimeoutError("连接超时"))
    assert code == ErrorCode.NETWORK_TIMEOUT


def test_F_S_051_TC10_handle_connection_error():
    """ConnectionError 映射为 NETWORK_ERROR"""
    _guard_handler()
    code, *_ = handle_error(ConnectionError("连接被拒绝"))
    assert code == ErrorCode.NETWORK_ERROR


def test_F_S_051_TC11_handle_permission_error():
    """PermissionError 映射为 PERMISSION_DENIED"""
    _guard_handler()
    code, *_ = handle_error(PermissionError("权限不足"))
    assert code == ErrorCode.PERMISSION_DENIED


def test_F_S_051_TC12_retry_label_for_retryable_errors():
    """网络类错误应返回重试标签"""
    _guard_handler()
    _, _, _, retry = handle_error(TimeoutError())
    assert retry != "", "TimeoutError 可重试错误应有 retry_label"
    _, _, _, retry = handle_error(ConnectionError())
    assert retry != "", "ConnectionError 可重试错误应有 retry_label"


def test_F_S_051_TC13_no_retry_for_permission_errors():
    """权限错误不应返回重试标签"""
    _guard_handler()
    _, _, _, retry = handle_error(PermissionError())
    assert retry == "", "权限错误不应可重试"
