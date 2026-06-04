"""OA-EPP Reflex 应用 — 路由注册

创建应用实例并注册所有页面路由。
兼容 main 分支的 login/profile 页面及 run() 函数。
"""

import shutil
import sys

import reflex as rx
from oaepp.components.layout import page_wrapper
from oaepp.pages.courses import content as courses_content
from oaepp.states.chapter import ChapterState

app = rx.App(
    style={
        "font_family": "system-ui, -apple-system, sans-serif",
    },
)


# ── 课程学习页（F-S-010 + F-S-011） ──────────────────────────────────

def courses_page() -> rx.Component:
    return page_wrapper(courses_content(), current_page="/courses")


@rx.page(route="/", title="课程学习 - OA-EPP", on_load=ChapterState.load_courses)
def index():
    return courses_page()


@rx.page(route="/courses", title="课程学习 - OA-EPP", on_load=ChapterState.load_courses)
def courses():
    return courses_page()


# ── 最简后台 API（挂载在 Reflex 内置 Starlette） ──────────────────────

if hasattr(app, "_api") and app._api is not None:
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


# ── profile page（来自 main） ─────────────────────────────────────────

try:
    from pages import profile as profile_mod
except Exception:
    try:
        from oaepp.pages import profile as profile_mod
    except Exception:
        profile_mod = None

if app is not None and profile_mod is not None:
    if hasattr(profile_mod, "profile_page") and callable(getattr(profile_mod, "profile_page")):
        app.add_page(profile_mod.profile_page, route="/profile")

# ── login page（来自 main） ───────────────────────────────────────────

try:
    from pages import login as login_mod
except Exception:
    try:
        from oaepp.pages import login as login_mod
    except Exception:
        login_mod = None

if app is not None and login_mod is not None:
    try:
        if hasattr(login_mod, "login_page") and callable(getattr(login_mod, "login_page")):
            try:
                app.add_page(login_mod.login_page, route="/login")
            except Exception:
                app.add_page(login_mod.login_page)
        elif hasattr(login_mod, "page"):
            app.add_page(login_mod.page)
    except Exception:
        pass


# ── run() 入口（兼容 reflex CLI 调用） ────────────────────────────────

def run(port: int = 3000):
    """Run Reflex dev server."""
    try:
        app.run(host="0.0.0.0", port=port)
    except Exception:
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
