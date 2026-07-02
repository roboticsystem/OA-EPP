"""OA-EPP Reflex 项目配置"""

import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="oaepp_admin",
    db_url="sqlite:///oaepp.db",
    frontend_port=3000,
    backend_port=8000,
    plugins=[
        SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
