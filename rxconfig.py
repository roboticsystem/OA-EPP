"""OA-EPP Reflex 项目配置 — 开发运维面板入口

reflex run 启动方式:
  1. 在项目根目录执行: reflex run
     前端 -> http://localhost:3000
     后端 -> http://localhost:8000
  2. 或者手动运行: python app.py
"""

import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="oaepp_admin",
    app_module_import="app",            # 指向根目录 app.py
    db_url="sqlite:///oaepp.db",
    frontend_port=3000,
    backend_port=8000,
    plugins=[
        SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
