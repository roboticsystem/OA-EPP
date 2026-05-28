"""F-T-009 仓库权限配置 TDD 测试

被测 State : oaepp.states.teacher_repo_perm.RepoPermState
TDD RED   : oaepp.states.teacher_repo_perm 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : RepoPermState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_repo_perm import RepoPermState
    _IMPORT_ERROR = None
except ImportError as _e:
    RepoPermState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_009_TC01_state_attrs_exist():
    """State 必须声明 org_name、team_name、members 变量"""
    _guard()
    for attr in ("org_name", "team_name", "members"):
        assert hasattr(RepoPermState, attr), f"缺少 {attr} 状态变量"


def test_F_T_009_TC02_invite_all_method_exists():
    """RepoPermState 必须提供 invite_all_students() 方法"""
    _guard()
    assert hasattr(RepoPermState, "invite_all_students") and callable(
        getattr(RepoPermState, "invite_all_students")
    ), "缺少 invite_all_students() 方法"


def test_F_T_009_TC03_member_status_enum():
    """成员状态应支持 accepted / pending / left"""
    _guard()
    has_status = (
        hasattr(RepoPermState, "MEMBER_STATUS")
        or hasattr(RepoPermState, "member_status_options")
    )
    assert has_status, "缺少成员状态枚举（MEMBER_STATUS / member_status_options）"


def test_F_T_009_TC04_revoke_access_method_exists():
    """RepoPermState 必须提供 revoke_team_access() 方法"""
    _guard()
    assert hasattr(RepoPermState, "revoke_team_access") and callable(
        getattr(RepoPermState, "revoke_team_access")
    ), "缺少 revoke_team_access() 方法"
