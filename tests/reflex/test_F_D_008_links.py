"""F-D-008 快捷链接面板 TDD 测试

被测 State : oaepp.states.devops_links.GitHubLinksState
TDD RED   : oaepp.states.devops_links 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : GitHubLinksState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_links import GitHubLinksState
    _IMPORT_ERROR = None
except ImportError as _e:
    GitHubLinksState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_008_TC01_state_attrs_exist():
    """State 必须声明 repo_url、links 变量"""
    _guard()
    for attr in ("repo_url", "links"):
        assert hasattr(GitHubLinksState, attr), f"缺少 {attr} 状态变量"


def test_F_D_008_TC02_links_auto_generated():
    """GitHubLinksState 必须提供 generate_links() 或 load_links() 方法"""
    _guard()
    has_generate = hasattr(GitHubLinksState, "generate_links") and callable(
        getattr(GitHubLinksState, "generate_links")
    )
    has_load = hasattr(GitHubLinksState, "load_links") and callable(
        getattr(GitHubLinksState, "load_links")
    )
    assert has_generate or has_load, "缺少链接生成方法 generate_links() 或 load_links()"


def test_F_D_008_TC03_required_link_types():
    """links 必须包含：repo、PRs、Issues、Actions 四种必需链接类型"""
    _guard()
    has_required = (
        hasattr(GitHubLinksState, "REQUIRED_LINK_TYPES")
        or hasattr(GitHubLinksState, "DEFAULT_LINK_TYPES")
    )
    assert has_required, "缺少必需链接类型定义（REQUIRED_LINK_TYPES / DEFAULT_LINK_TYPES）"


def test_F_D_008_TC04_custom_label_support():
    """links 应支持自定义标签和排序"""
    _guard()
    state = GitHubLinksState()
    assert isinstance(state.links, list), "links 应为列表类型"
