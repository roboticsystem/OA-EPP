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

# 教师端 — 学生开发日志导出页面
try:
    from pages import teacher_export as teacher_export_mod
except Exception:
    try:
        from oaepp.pages import teacher_export as teacher_export_mod
    except Exception:
        teacher_export_mod = None

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

    # ── F-T-010 学生开发日志导出 API ──────────────────────────────────
    from starlette.requests import Request

    async def _api_export_single(request: Request):
        """GET /api/export/report?student_no=xxx&format=html|pdf|excel"""
        try:
            sno = request.query_params.get("student_no", "")
            fmt = request.query_params.get("format", "html")
            if not sno:
                return JSONResponse({"error": "student_no required"}, status_code=400)
            from export_api import export_report
            content = export_report(sno, fmt, exporter_no="teacher")
            media_map = {
                "html": "text/html; charset=utf-8",
                "pdf": "application/pdf",
                "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
            ext_map = {"html": "html", "pdf": "pdf", "excel": "xlsx"}
            from starlette.responses import Response
            return Response(content=content, media_type=media_map.get(fmt, "application/octet-stream"),
                            headers={"Content-Disposition": f"attachment; filename={sno}_report.{ext_map.get(fmt, fmt)}"})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _api_export_batch(request: Request):
        """GET /api/export/batch?class_name=xxx&format=excel"""
        try:
            cn = request.query_params.get("class_name", "")
            fmt = request.query_params.get("format", "excel")
            if not cn:
                return JSONResponse({"error": "class_name required"}, status_code=400)
            from export_api import export_batch_by_class
            from urllib.parse import quote
            content = export_batch_by_class(cn, fmt, exporter_no="teacher")
            from starlette.responses import Response
            filename = quote(f"{cn}_批量导出.zip")
            return Response(content=content, media_type="application/zip",
                            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _api_classes(request: Request):
        """GET /api/export/classes"""
        try:
            from export_api import get_all_classes
            classes = get_all_classes()
            return JSONResponse({"classes": classes})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _api_audit_logs(request: Request):
        """GET /api/export/audit-logs"""
        try:
            from export_api import get_audit_logs
            import json
            logs = get_audit_logs(100)
            for log in logs:
                for k, v in log.items():
                    if isinstance(v, datetime):
                        log[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        log[k] = v.decode("utf-8", errors="replace")
            return JSONResponse({"logs": logs})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _api_search_students(request: Request):
        """GET /api/students/search?q=xxx"""
        try:
            q = request.query_params.get("q", "").strip()
            if not q:
                return JSONResponse({"students": []})
            from export_api import search_students
            rows = search_students(q)
            return JSONResponse({"students": rows})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    app._api.routes.append(Route("/api/export/report", _api_export_single, methods=["GET"]))
    app._api.routes.append(Route("/api/export/batch", _api_export_batch, methods=["GET"]))
    app._api.routes.append(Route("/api/export/classes", _api_classes, methods=["GET"]))
    app._api.routes.append(Route("/api/export/audit-logs", _api_audit_logs, methods=["GET"]))
    app._api.routes.append(Route("/api/students/search", _api_search_students, methods=["GET"]))

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

# 教师端 — 学生开发日志导出页面
if app is not None and teacher_export_mod is not None:
    try:
        if hasattr(teacher_export_mod, "teacher_export_page") and callable(getattr(teacher_export_mod, "teacher_export_page")):
            try:
                app.add_page(teacher_export_mod.teacher_export_page, route="/teacher/export")
            except Exception:
                app.add_page(teacher_export_mod.teacher_export_page)
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
