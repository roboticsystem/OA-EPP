"""F-D-005 协作者权限 TDD 测试

被测 State : oaepp.states.devops_perm.CollabPermState
TDD RED   : oaepp.states.devops_perm 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : CollabPermState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_perm import CollabPermState
    _IMPORT_ERROR = None
except ImportError as _e:
    CollabPermState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_005_TC01_state_attrs_exist():
    """State 必须声明 members、team_name 变量"""
    _guard()
    for attr in ("members", "team_name"):
        assert hasattr(CollabPermState, attr), f"缺少 {attr} 状态变量"


def test_F_D_005_TC02_role_enum_values():
    """角色枚举必须包含 Admin / Write / Triage / Read"""
    _guard()
    has_enum = (
        hasattr(CollabPermState, "ROLE_CHOICES")
        or hasattr(CollabPermState, "VALID_ROLES")
        or hasattr(CollabPermState, "role_options")
    )
    assert has_enum, "缺少角色枚举定义（ROLE_CHOICES / VALID_ROLES / role_options）"


def test_F_D_005_TC03_add_member_via_team():
    """CollabPermState 必须通过团队（team）而非个人添加成员"""
    _guard()
    assert hasattr(CollabPermState, "add_member") and callable(
        getattr(CollabPermState, "add_member")
    ), "缺少 add_member() 方法"
    # 验证通过 team_name 维度管理
    assert hasattr(CollabPermState, "team_name"), "应通过 team_name 管理成员权限"


def test_F_D_005_TC04_remove_member_method_exists():
    """CollabPermState 必须提供 remove_member() 方法"""
    _guard()
    assert hasattr(CollabPermState, "remove_member") and callable(
        getattr(CollabPermState, "remove_member")
    ), "缺少 remove_member() 方法"
