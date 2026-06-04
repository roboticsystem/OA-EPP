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

try:
    from pages import profile as profile_mod
except Exception:
    try:
        from oaepp.pages import profile as profile_mod
    except Exception:
        profile_mod = None

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

    async def _api_health(request):
        return JSONResponse({"status": "healthy", "app": "OA-EPP"})

    app._api.routes.append(Route("/", _api_health, methods=["GET"]))
    app._api.routes.append(Route("/api/hello", _api_hello, methods=["GET"]))
    app._api.routes.append(Route("/api/status", _api_status, methods=["GET"]))

    # ── Profile API routes ──────────────────────────────────────────
    try:
        try:
            from models.database import (
                get_student_profile,
                update_student_profile,
                verify_password,
                update_password,
                init_db,
                seed_student,
            )
        except ImportError:
            from oaepp.models.database import (
                get_student_profile,
                update_student_profile,
                verify_password,
                update_password,
                init_db,
                seed_student,
            )

        # Initialise DB on startup
        init_db()
        seed_student()

        async def _api_profile_get(request):
            """GET /api/profile?student_id=<id>"""
            student_id = request.query_params.get("student_id")
            if not student_id:
                return JSONResponse({"error": "student_id required"}, status_code=400)
            try:
                profile = get_student_profile(int(student_id))
                if profile:
                    return JSONResponse({"data": profile})
                return JSONResponse({"error": "not found"}, status_code=404)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        async def _api_profile_update(request):
            """PUT /api/profile"""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "invalid JSON"}, status_code=400)
            student_id = body.get("student_id")
            if not student_id:
                return JSONResponse({"error": "student_id required"}, status_code=400)
            try:
                update_student_profile(
                    student_id=int(student_id),
                    full_name=body.get("full_name", ""),
                    email=body.get("email", ""),
                    class_name=body.get("class_name", ""),
                    phone=body.get("phone", ""),
                )
                return JSONResponse({"status": "ok"})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        async def _api_profile_password(request):
            """PUT /api/profile/password"""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "invalid JSON"}, status_code=400)
            student_id = body.get("student_id")
            old_pw = body.get("old_password", "")
            new_pw = body.get("new_password", "")
            if not student_id or not old_pw or not new_pw:
                return JSONResponse(
                    {"error": "student_id, old_password, new_password required"},
                    status_code=400,
                )
            sid = int(student_id)
            if not verify_password(sid, old_pw):
                return JSONResponse({"error": "incorrect old password"}, status_code=403)
            from werkzeug.security import generate_password_hash
            update_password(sid, generate_password_hash(new_pw))
            return JSONResponse({"status": "ok"})

        app._api.routes.append(Route("/api/profile", _api_profile_get, methods=["GET"]))
        app._api.routes.append(Route("/api/profile", _api_profile_update, methods=["PUT"]))
        app._api.routes.append(Route("/api/profile/password", _api_profile_password, methods=["PUT"]))
    except Exception:
        pass  # Profile API not available without database

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
