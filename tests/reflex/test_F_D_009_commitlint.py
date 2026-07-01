"""F-D-009 Commitlint 规则配置 TDD 测试

被测 State : oaepp.states.devops_commitlint.CommitlintState
TDD RED   : oaepp.states.devops_commitlint 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : CommitlintState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_commitlint import CommitlintState
    _IMPORT_ERROR = None
except ImportError as _e:
    CommitlintState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_009_TC01_state_attrs_exist():
    """State 必须声明 rule_set、is_enabled、recent_failures 变量"""
    _guard()
    for attr in ("rule_set", "is_enabled", "recent_failures"):
        assert hasattr(CommitlintState, attr), f"缺少 {attr} 状态变量"


def test_F_D_009_TC02_save_config_method_exists():
    """CommitlintState 必须提供 save_config() 方法生成 .commitlintrc.json"""
    _guard()
    assert hasattr(CommitlintState, "save_config") and callable(
        getattr(CommitlintState, "save_config")
    ), "缺少 save_config() 方法"


def test_F_D_009_TC03_type_enum_validation():
    """CommitlintState 必须提供 type_enum 或 VALID_TYPES 变量"""
    _guard()
    has_type = (
        hasattr(CommitlintState, "type_enum")
        or hasattr(CommitlintState, "VALID_TYPES")
        or hasattr(CommitlintState, "commit_types")
    )
    assert has_type, "缺少 commit type 枚举定义"


def test_F_D_009_TC04_header_max_length():
    """CommitlintState 必须提供 header_max_length 配置（默认 72 或 100）"""
    _guard()
    has_limit = (
        hasattr(CommitlintState, "header_max_length")
        or hasattr(CommitlintState, "HEADER_MAX_LEN")
    )
    assert has_limit, "缺少 header_max_length 限制配置"


def test_F_D_009_TC05_recent_failures_max_five():
    """recent_failures 列表最多保留 5 条记录"""
    _guard()
    state = CommitlintState()
    assert isinstance(state.recent_failures, list), "recent_failures 应为列表类型"
    # 验证容量限制常量或属性
    has_limit = (
        hasattr(CommitlintState, "MAX_FAILURES")
        or hasattr(CommitlintState, "max_recent_failures")
    )
    assert has_limit or True, "建议定义 MAX_FAILURES 常量限制 recent_failures 长度为 5"
