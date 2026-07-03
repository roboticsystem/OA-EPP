"""OA-EPP 主入口 — 注册页面路由

两种启动方式:
  1. python app.py          — 独立启动，仅加载 GitHub 快捷链接页面
  2. python -m oaepp.app    — 完整启动 oaepp 应用（自动发现所有页面）
"""
import reflex as rx
from pages.admin_devops_github import github_quicklinks_page

app = rx.App()
app.add_page(github_quicklinks_page, route="/", title="OA-EPP · GitHub 快捷链接")
