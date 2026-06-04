"""
OA-EPP Reflex 应用入口

注册所有页面和 API 路由：
- 登录页面 /
- 通知页面 /notifications
- 通知 API 路由 /api/notifications/*, /api/teacher/notifications/*
"""
import shutil
import sys

try:
    import reflex as rx
except Exception:
    rx = None

# Attempt to import page modules (may fail if reflex not installed).
# Priority: local `pages.xxx` when running inside /oaepp,
# fallback to `oaepp.pages.xxx` when running from repo root.
def _try_import_page(name):
    try:
        mod = __import__(f"pages.{name}", fromlist=[name])
    except Exception:
        try:
            mod = __import__(f"oaepp.pages.{name}", fromlist=[name])
        except Exception:
            return None
    return mod

login_mod = _try_import_page("login")
notifications_mod = _try_import_page("notifications")

app = None
if rx is not None:
    try:
        app = rx.App()
    except Exception:
        try:
            app = rx.app.App()
        except Exception:
            app = None

# ── 后台 API（挂载在 Reflex 内置 Starlette，端口 8000） ─────────────
if app is not None and hasattr(app, "_api") and app._api is not None:
    from datetime import datetime, timezone
    from starlette.routing import Route
    from starlette.responses import JSONResponse

    async def _api_hello(request):
        return JSONResponse({"message": "Hello from OA-EPP backend!"})

    async def _api_status(request):
        return JSONResponse({
            "status": "ok",
            "time": datetime.now(timezone.utc).isoformat(),
            "app": "OA-EPP",
        })

    app._api.routes.append(Route("/api/hello", _api_hello, methods=["GET"]))
    app._api.routes.append(Route("/api/status", _api_status, methods=["GET"]))

    # ── 注册通知公告 API 路由（F-S-012） ──
    try:
        from oaepp.routers.notice import router as notice_router
        # 使用 include_router 注册到内部 FastAPI/Starlette app
        if hasattr(app._api, "include_router"):
            app._api.include_router(notice_router)
        else:
            # 手动挂载路由到 Starlette
            for route in notice_router.routes:
                app._api.routes.append(route)
    except Exception:
        pass  # 路由注册失败不阻塞启动

# ─────────────────────────────────────────────────────────────────────────

# 注册登录页面
if app is not None and login_mod is not None:
    try:
        if hasattr(login_mod, "login_page") and callable(getattr(login_mod, "login_page")):
            try:
                app.add_page(login_mod.login_page, route="/")
            except Exception:
                app.add_page(login_mod.login_page)
        elif hasattr(login_mod, "page"):
            app.add_page(login_mod.page)
    except Exception:
        pass

# 注册通知公告页面（F-S-012）
if app is not None and notifications_mod is not None:
    try:
        if hasattr(notifications_mod, "notifications_page") and callable(getattr(notifications_mod, "notifications_page")):
            app.add_page(notifications_mod.notifications_page, route="/notifications")
        elif hasattr(notifications_mod, "page"):
            app.add_page(notifications_mod.page, route="/notifications")
    except Exception:
        pass


def run(port: int = 3000):
    """Run Reflex dev server (prefer `reflex` CLI, fallback to python -m reflex)."""
    if rx is None or app is None:
        print("Reflex 或 app 未准备，确保已安装 oaepp/requirements.txt 并重试。")
        return
    try:
        # try app.run if provided by this reflex version
        app.run(host="0.0.0.0", port=port)
    except Exception:
        # fallback to CLI
        import subprocess
        binpath = shutil.which("reflex")
        cmds = []
        if binpath:
            cmds = [
                [binpath, "run", "--backend-port", str(port)],
                [binpath, "run", "--single-port", str(port)],
                [binpath, "run"],
            ]
        else:
            cmds = [
                [sys.executable, "-m", "reflex", "run", "--backend-port", str(port)],
                [sys.executable, "-m", "reflex", "run", "--single-port", str(port)],
                [sys.executable, "-m", "reflex", "run"],
            ]
        for cmd in cmds:
            try:
                subprocess.check_call(cmd)
                return
            except subprocess.CalledProcessError:
                continue


if __name__ == "__main__":
    run()
