"""F_D_008 GitHub 快捷链接页面 — 开发运维面板

自动发现路由: /devops_links
页面函数: devops_links_page()

由 oaepp/app.py 的 _auto_discover 自动注册。
实际 UI 组件委托给 pages.admin_devops_github，状态管理使用
oaepp.states.devops_links.GitHubLinksState。
"""

from __future__ import annotations

# 复用已有的完整页面组件（UI 逻辑一致，State 已统一到 oaepp.states.devops_links）
from pages.admin_devops_github import github_quicklinks_page as devops_links_page  # noqa: F401
