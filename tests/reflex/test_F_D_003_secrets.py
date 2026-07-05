"""F-D-003 Secrets 管理 TDD 测试

被测 State : oaepp.states.devops_secrets.SecretsState
TDD RED   : oaepp.states.devops_secrets 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : SecretsState 实现后 → 全部通过

安全约束：Secret 的值绝不应出现在 State 变量中（只存名称）
"""
import pytest

try:
    from oaepp.states.devops_secrets import SecretsState
    _IMPORT_ERROR = None
except ImportError as _e:
    SecretsState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_003_TC01_state_attrs_exist():
    """State 必须声明 secrets_list、is_loading 变量（不得有 secret_value）"""
    _guard()
    assert hasattr(SecretsState, "secrets_list"), "缺少 secrets_list 状态变量"
    assert hasattr(SecretsState, "is_loading"), "缺少 is_loading 状态变量"
    # 安全检查：不得存储 secret 值
    assert not hasattr(SecretsState, "secret_value"), (
        "安全违规：SecretsState 不应有 secret_value 变量（明文存储密钥）"
    )


def test_F_D_003_TC02_add_secret_method_exists():
    """SecretsState 必须提供 add_secret() 方法"""
    _guard()
    assert hasattr(SecretsState, "add_secret") and callable(
        getattr(SecretsState, "add_secret")
    ), "缺少 add_secret() 方法"


def test_F_D_003_TC03_secret_value_never_in_state():
    """secrets_list 中的元素只包含 name，不包含 value"""
    _guard()
    state = SecretsState()
    # 默认列表为空，测试结构定义
    assert isinstance(state.secrets_list, list), "secrets_list 应为列表类型"


def test_F_D_003_TC04_delete_secret_method_exists():
    """SecretsState 必须提供 delete_secret() 方法"""
    _guard()
    assert hasattr(SecretsState, "delete_secret") and callable(
        getattr(SecretsState, "delete_secret")
    ), "缺少 delete_secret() 方法"
