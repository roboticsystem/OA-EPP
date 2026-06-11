import os

import reflex as rx

# 数据库连接（Reflex ORM 使用，通过 rx.session() 访问）
_db_url = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://student_dev:OaEpp%40Dev2026@156.239.252.40:13306/oaepp_dev",
)

# Allow running `reflex run` directly inside /oaepp.
config = rx.Config(
    app_name="oaepp",
    app_module_import="app",
    db_url=_db_url,
    frontend_port=int(os.environ.get("REFLEX_FRONTEND_PORT", "8000")),
    backend_port=int(os.environ.get("REFLEX_BACKEND_PORT", "8000")),
    backend_host=os.environ.get("REFLEX_BACKEND_HOST", "0.0.0.0"),
    api_url=os.environ.get("REFLEX_API_URL")
    or os.environ.get("REFLEX_DEPLOY_URL")
    or f"http://localhost:{os.environ.get('REFLEX_FRONTEND_PORT', '8000')}",
    deploy_url=os.environ.get("REFLEX_DEPLOY_URL"),
    # Reflex 原生参数，直接注入 Vite server.allowedHosts
    vite_allowed_hosts=[".uwis.cn", "oaepp-reflex.uwis.cn"],
)