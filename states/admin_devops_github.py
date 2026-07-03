"""GitHub 快捷链接状态管理 — 委托给 oaepp.states.devops_links（F-D-008 / #41）

本模块作为向后兼容的薄封装，所有逻辑由 oaepp.states.devops_links.GitHubLinksState 提供。
页面可直接导入 GitHubQuickLinksState（别名）使用。
"""

from __future__ import annotations

# 从 oaepp.states.devops_links 导入所有公开符号
from oaepp.states.devops_links import (  # noqa: F401
    GITHUB_REPO_URL,
    REQUIRED_LINK_TYPES,
    DEFAULT_LINK_TYPES,
    build_default_link_records,
    GitHubLinksState,
)

# 向后兼容别名 — 页面可能使用旧名称 GitHubQuickLinksState
GitHubQuickLinksState = GitHubLinksState
