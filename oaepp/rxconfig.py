import os

import reflex as rx

# Allow running `reflex run` directly inside /oaepp.
config = rx.Config(
    app_name="oaepp",
    app_module_import="app",
    frontend_port=int(os.environ.get("REFLEX_FRONTEND_PORT", "3000")),
    backend_port=int(os.environ.get("REFLEX_BACKEND_PORT", "8001")),
    backend_host=os.environ.get("REFLEX_BACKEND_HOST", "0.0.0.0"),
    api_url=os.environ.get(
        "REFLEX_API_URL",
        f"http://localhost:{os.environ.get('REFLEX_BACKEND_PORT', '8001')}",
    ),
    deploy_url=os.environ.get("REFLEX_DEPLOY_URL"),
    # Reflex 原生参数，直接注入 Vite server.allowedHosts
    vite_allowed_hosts=[".uwis.cn", "oaepp_reflex.uwis.cn"],
)
