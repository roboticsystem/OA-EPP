import os

import reflex as rx

# Allow running `reflex run` directly inside /oaepp.
config = rx.Config(
    app_name="oaepp",
    app_module_import="app",
    frontend_port=int(os.environ.get("REFLEX_FRONTEND_PORT", "3000")),
    backend_port=int(os.environ.get("REFLEX_BACKEND_PORT", "8000")),
    backend_host=os.environ.get("REFLEX_BACKEND_HOST", "0.0.0.0"),
    api_url=os.environ.get(
        "REFLEX_API_URL",
        f"http://localhost:{os.environ.get('REFLEX_BACKEND_PORT', '8000')}",
    ),
    deploy_url=os.environ.get("REFLEX_DEPLOY_URL"),
)
