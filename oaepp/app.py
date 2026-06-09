"""
OA-EPP Reflex app — 路由注册 & 启动入口
路由映射表：oaepp/routes.json
"""
import importlib
import shutil
import sys

try:
    import reflex as rx
except Exception:
    rx = None

# ── 辅助函数 ─────────────────────────────────────────────────────────────

def _import_page(module_name: str):
    """尝试导入 pages.<module_name>，优先本地，回退 oaepp. 前缀。"""
    for prefix in ("pages", "oaepp.pages"):
        try:
            return importlib.import_module(f"{prefix}.{module_name}")
        except Exception:
            continue
    return None


def _register_page(app, route: str, module_name: str, attr_name: str):
    """安全地导入页面模块并注册路由，失败时静默跳过。"""
    if app is None:
        return
    mod = _import_page(module_name)
    if mod is None:
        return
    page_fn = getattr(mod, attr_name, None)
    if page_fn is not None and callable(page_fn):
        try:
            app.add_page(page_fn, route=route)
        except Exception:
            pass


# ── 导入 AuthState（Reflex 需要注册为全局 State） ─────────────────────────
try:
    from states.auth import AuthState
except Exception:
    try:
        from oaepp.states.auth import AuthState
    except Exception:
        AuthState = None

# ── 创建 App ─────────────────────────────────────────────────────────────
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

# ── 注册所有路由（routes.json 映射表） ─────────────────────────────────────
# 学生端页面
_register_page(app, "/",              "login",       "login_page")
_register_page(app, "/dashboard",     "dashboard",   "dashboard_page")
_register_page(app, "/courses",       "courses",     "courses_page")
_register_page(app, "/assignments",   "assignments", "assignments_page")
_register_page(app, "/attendance",    "attendance",  "attendance_page")
_register_page(app, "/exam",          "exam",        "exam_page")
_register_page(app, "/grades",        "grades",      "grades_page")
_register_page(app, "/profile",       "profile",     "profile_page")

# 管理员/教师端页面（由负责人维护）
_register_page(app, "/admin_students",  "admin_students",  "admin_students_page")
_register_page(app, "/admin_grades",    "admin_grades",    "admin_grades_page")
_register_page(app, "/admin_settings",  "admin_settings",  "admin_settings_page")
_register_page(app, "/admin_devops",    "admin_devops",    "admin_devops_page")


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
