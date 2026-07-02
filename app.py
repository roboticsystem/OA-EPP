"""OA-EPP 主入口 — 注册页面路由"""
import reflex as rx
from pages.admin_devops_github import github_quicklinks_page

app = rx.App()
app.add_page(github_quicklinks_page, route="/", title="OA-EPP · GitHub 快捷链接")
