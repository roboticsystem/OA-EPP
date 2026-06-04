"""
Reflex App 注册和路由配置
"""
import reflex as rx
from pages import login as login_mod
from pages import profile as profile_mod

# 创建App实例
app = rx.App()

# 注册页面路由
app.add_page(login_mod.login_page, route="/")
app.add_page(profile_mod.profile_page, route="/profile")
