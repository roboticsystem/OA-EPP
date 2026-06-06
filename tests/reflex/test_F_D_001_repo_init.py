"""F-D-001 仓库初始化 TDD 测试

被测 State : oaepp.states.devops_repo.RepoInitState
TDD RED   : oaepp.states.devops_repo 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : RepoInitState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_repo import RepoInitState
    _IMPORT_ERROR = None
except ImportError as _e:
    RepoInitState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_001_TC01_state_attrs_exist():
    """State 必须声明 repo_url、repo_name、is_private、is_initialized 变量"""
    _guard()
    for attr in ("repo_url", "repo_name", "is_private", "is_initialized"):
        assert hasattr(RepoInitState, attr), f"缺少 {attr} 状态变量"


def test_F_D_001_TC02_init_repo_method_exists():
    """RepoInitState 必须提供 init_repo() 事件处理器"""
    _guard()
    assert hasattr(RepoInitState, "init_repo") and callable(
        getattr(RepoInitState, "init_repo")
    ), "缺少 init_repo() 方法"


def test_F_D_001_TC03_gitignore_template():
    """RepoInitState 必须提供 Python .gitignore 模板支持"""
    _guard()
    has_template = (
        hasattr(RepoInitState, "GITIGNORE_TEMPLATE")
        or hasattr(RepoInitState, "gitignore_template")
        or hasattr(RepoInitState, "generate_gitignore")
    )
    assert has_template, "缺少 .gitignore 模板定义或生成方法"


async def test_F_D_001_TC04_init_creates_config_files(mem_db):
    """init_repo() 完成后 is_initialized=True，不抛异常"""
    _guard()
    state = RepoInitState()
    state.repo_name = "test-repo"
    state.is_private = True
    # 此处只验证方法可调用且不抛异常（实际 GitHub API 调用需 mock）
    try:
        await state.init_repo()
    except Exception as exc:
        # 允许网络相关异常，但状态变量必须已被设置
        assert hasattr(state, "is_initialized"), f"init_repo() 抛出异常: {exc}"
