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

    async def _api_student_scores(request):
        from starlette.responses import JSONResponse as JR
        from urllib.parse import parse_qs

        params = parse_qs(request.url.query.decode() if hasattr(request.url.query, "decode") else str(request.url.query))
        student_no = (params.get("student_no") or [None])[0]
        password = (params.get("password") or [None])[0]
        if not student_no:
            return JR({"error": "缺少学号"}, status_code=400)

        from oaepp.states.score import ScoreState
        import pymysql

        state = ScoreState()
        try:
            conn = pymysql.connect(
                host="156.239.252.40", port=13306, user="student_dev",
                password="OaEpp@Dev2026", database="oaepp_dev",
                charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE student_no=%s AND role='student'", (student_no,))
                user = cur.fetchone()
            conn.close()
            if not user:
                return JR({"error": "学号不存在"})
            state.current_user_id = user["id"]
        except Exception as e:
            return JR({"error": f"数据库连接失败: {e}"}, status_code=500)

        result = await state.load_scores()
        return JR(result)

    app._api.routes.append(Route("/api/student/scores", _api_student_scores, methods=["GET"]))

# ─────────────────────────────────────────────────────────────────────────

# --- profile page ---
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

# --- score page (F-S-030) ---
try:
    from pages import score as score_mod
except Exception:
    try:
        from oaepp.pages import score as score_mod
    except Exception:
        score_mod = None

if app is not None and score_mod is not None:
    if hasattr(score_mod, "score_page") and callable(getattr(score_mod, "score_page")):
        app.add_page(score_mod.score_page, route="/score")

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
