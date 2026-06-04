import os
import urllib.parse

import reflex as rx

# MySQL数据库配置
# 注意: 密码中的特殊字符需要URL编码
DB_PASSWORD = os.environ.get("DB_PASSWORD", "OaEpp@Dev2026")
DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"mysql+pymysql://student_dev:{DB_PASSWORD_ENCODED}@156.239.252.40:13306/oaepp_dev"
)

# Allow running `reflex run` directly inside /oaepp.
config = rx.Config(
    app_name="oaepp",
    app_module_import="app",
    db_url=DATABASE_URL,
    frontend_port=int(os.environ.get("REFLEX_FRONTEND_PORT", "3000")),
    backend_port=int(os.environ.get("REFLEX_BACKEND_PORT", "8000")),
    backend_host=os.environ.get("REFLEX_BACKEND_HOST", "0.0.0.0"),
    api_url=os.environ.get(
        "REFLEX_API_URL",
        f"http://localhost:{os.environ.get('REFLEX_BACKEND_PORT', '8000')}",
    ),
    deploy_url=os.environ.get("REFLEX_DEPLOY_URL"),
)
