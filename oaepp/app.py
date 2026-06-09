"""
Minimal Reflex app registration and run helper.
"""
import shutil
import sys

try:
    import reflex as rx
except Exception:
    rx = None

# Attempt to import page module (may fail if reflex not installed).
# Priority: local `pages.login` when running inside /oaepp,
# fallback to `oaepp.pages.login` when running from repo root.
try:
    from pages import login as login_mod
except Exception:
    try:
        from oaepp.pages import login as login_mod
    except Exception:
        login_mod = None

app = None
if rx is not None:
    try:
        app = rx.App()
    except Exception:
        try:
            app = rx.app.App()
        except Exception:
            app = None

# ── 最简后台 API（挂载在 Reflex 内置 Starlette，端口 8000） ─────────────
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

# ─────────────────────────────────────────────────────────────────────────

# --- profile page ---
try:
    from pages import profile as profile_mod
except Exception:
    try:
        from oaepp.pages import profile as profile_mod
    except Exception:
        profile_mod = None

# --- grades page ---
try:
    from pages import grades as grades_mod
except Exception:
    try:
        from oaepp.pages import grades as grades_mod
    except Exception:
        grades_mod = None

if app is not None and profile_mod is not None:
    if hasattr(profile_mod, "profile_page") and callable(getattr(profile_mod, "profile_page")):
        app.add_page(profile_mod.profile_page, route="/profile")

if app is not None and grades_mod is not None:
    if hasattr(grades_mod, "grades_page") and callable(getattr(grades_mod, "grades_page")):
        app.add_page(grades_mod.grades_page, route="/grades")

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
