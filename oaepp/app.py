"""OA-EPP Reflex 应用 — 路由注册

所有页面路由通过 app.add_page() 注册。
遵循 Reflex框架一个功能模块的开发说明.md 的规范。
"""

import shutil
import sys

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.states.chapter import ChapterState

app = None
if rx is not None:
    app = rx.App(
        style={
            "font_family": "system-ui, -apple-system, sans-serif",
        },
    )


# ── courses 课程学习页（F-S-010 + F-S-011） ───────────────────────────

try:
    from pages import courses as courses_mod
except Exception:
    try:
        from oaepp.pages import courses as courses_mod
    except Exception:
        courses_mod = None

if app is not None and courses_mod is not None:
    if hasattr(courses_mod, "courses_page_component") and callable(courses_mod.courses_page_component):
        app.add_page(courses_mod.courses_page_component, route="/courses",
                     title="课程学习 - OA-EPP",
                     on_load=ChapterState.load_courses)


# ── chapter 章节内容详情页（F-S-011 章节浏览） ────────────────────────

try:
    from pages import chapter_detail as chapter_mod
except Exception:
    try:
        from oaepp.pages import chapter_detail as chapter_mod
    except Exception:
        chapter_mod = None

if app is not None and chapter_mod is not None:
    if hasattr(chapter_mod, "chapter_page_component") and callable(chapter_mod.chapter_page_component):
        app.add_page(chapter_mod.chapter_page_component, route="/chapter",
                     title="章节内容 - OA-EPP")


# ── 最简后台 API ──────────────────────────────────────────────────────

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


# ── profile page ──────────────────────────────────────────────────────

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


# ── login page ────────────────────────────────────────────────────────

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


# ── run() 入口 ────────────────────────────────────────────────────────

def run(port: int = 3000):
    """Run Reflex dev server."""
    if rx is None or app is None:
        print("Reflex 或 app 未准备，确保已安装 requirements.txt 并重试。")
        return
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
