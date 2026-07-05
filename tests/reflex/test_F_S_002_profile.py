"""F-S-002 个人资料 TDD 测试

被测 State : oaepp.states.profile.ProfileState
TDD RED   : oaepp.states.profile 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ProfileState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.profile import ProfileState
    _IMPORT_ERROR = None
except ImportError as _e:
    ProfileState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_002_TC01_state_attrs_exist():
    """State 必须声明用户资料所需的状态变量"""
    _guard()
    for attr in ("username", "email", "phone", "student_class", "bio"):
        assert hasattr(ProfileState, attr), f"缺少 {attr} 状态变量"


def test_F_S_002_TC02_update_profile_method_exists():
    """ProfileState 必须提供 update_profile() 事件处理器"""
    _guard()
    assert hasattr(ProfileState, "update_profile") and callable(
        getattr(ProfileState, "update_profile")
    ), "缺少 update_profile() 方法"


async def test_F_S_002_TC03_wrong_old_password(mem_db):
    """旧密码错误 → 修改密码失败，error_message 非空"""
    _guard()
    state = ProfileState()
    state.current_user_id = 1
    await state.change_password("wrong_old_pwd", "new_pwd123", "new_pwd123")
    assert state.error_message != "", "旧密码错误时应设置 error_message"


async def test_F_S_002_TC04_same_password_rejected(mem_db):
    """新密码与旧密码相同 → 修改失败"""
    _guard()
    state = ProfileState()
    state.current_user_id = 1
    # 模拟旧密码与新密码相同
    await state.change_password("same_pwd", "same_pwd", "same_pwd")
    assert state.error_message != "", "新旧密码相同时应提示错误"


def test_F_S_002_TC05_access_control_attr_exists():
    """ProfileState 必须携带 current_user_id 以实现数据隔离"""
    _guard()
    assert hasattr(ProfileState, "current_user_id"), "缺少 current_user_id，无法保证数据隔离"
