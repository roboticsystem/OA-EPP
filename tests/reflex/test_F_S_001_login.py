"""F-S-001 登录/退出 TDD 测试

被测 State : oaepp.states.auth.AuthState
TDD RED   : oaepp.states.auth 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : AuthState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.auth import AuthState
    _IMPORT_ERROR = None
except ImportError as _e:
    AuthState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


# ── TC01 ─────────────────────────────────────────────────────────────
def test_F_S_001_TC01_state_attrs_exist():
    """State 必须声明 is_authenticated、current_user_id、error_message 变量"""
    _guard()
    assert hasattr(AuthState, "is_authenticated"), "缺少 is_authenticated 状态变量"
    assert hasattr(AuthState, "current_user_id"), "缺少 current_user_id 状态变量"
    assert hasattr(AuthState, "error_message"), "缺少 error_message 状态变量"


# ── TC02 ─────────────────────────────────────────────────────────────
def test_F_S_001_TC02_login_method_exists():
    """AuthState 必须提供 login() 事件处理器"""
    _guard()
    assert hasattr(AuthState, "login") and callable(
        getattr(AuthState, "login")
    ), "缺少 login() 方法"


# ── TC03 ─────────────────────────────────────────────────────────────
async def test_F_S_001_TC03_wrong_password_sets_error(mem_db):
    """错误密码 → is_authenticated=False，error_message 非空"""
    _guard()
    state = AuthState()
    await state.login("nonexistent_user", "wrong_password")
    assert state.is_authenticated is False
    assert state.error_message != ""


# ── TC04 ─────────────────────────────────────────────────────────────
def test_F_S_001_TC04_locked_attr_exists():
    """AuthState 必须声明 is_locked 变量以支持连续失败锁定"""
    _guard()
    assert hasattr(AuthState, "is_locked"), "缺少 is_locked 状态变量"


# ── TC05 ─────────────────────────────────────────────────────────────
async def test_F_S_001_TC05_logout_clears_state(mem_db):
    """logout() 后 is_authenticated=False，current_user_id=None"""
    _guard()
    state = AuthState()
    # 手动设置已登录状态
    state.is_authenticated = True
    state.current_user_id = 1
    assert hasattr(state, "logout") and callable(
        getattr(state, "logout")
    ), "缺少 logout() 方法"
    await state.logout()
    assert state.is_authenticated is False
    assert state.current_user_id is None
