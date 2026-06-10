"""
OA-EPP Reflex app — 路由注册 & 启动入口

路由规则：
  - 学生功能：pages/xxx.py → xxx_page() → 自动注册到 /xxx
  - 特殊路由：显式声明（如 login → /）
  - 管理员页面：由负责人显式注册
"""
import importlib
import shutil
import sys
from pathlib import Path

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


def _auto_discover(app):
    """自动发现 pages/ 目录下的页面模块。

    约定：
      pages/xxx.py 中定义 xxx_page() → 自动注册路由 /xxx

    跳过：
      - __init__.py, __pycache__
      - 已在显式路由中特殊处理过的模块（login → /）
    """
    if app is None:
        return

    # 已由显式路由特殊处理的模块（不需要自动发现）
    _skip_modules = {"login", "__init__", "notifications", "notifications_teacher"}

    pages_dir = Path(__file__).resolve().parent / "pages"
    if not pages_dir.is_dir():
        return

    for py_file in sorted(pages_dir.glob("*.py")):
        module_name = py_file.stem
        if module_name in _skip_modules or module_name.startswith("_"):
            continue
        route = f"/{module_name}"
        attr = f"{module_name}_page"
        _register_page(app, route, module_name, attr)


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

# ── 后台 API（挂载在 Reflex 内置 Starlette） ─────────────────────
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

# ── 显式路由（特殊路由，如首页 /） ────────────────────────────────────────
_register_page(app, "/", "login", "login_page")

# ── 挂载通知公告路由 ──
if app is not None and hasattr(app, "_api") and app._api is not None:
    try:
        from oaepp.routers.notice import router as notice_router
    except ModuleNotFoundError:
        try:
            from routers.notice import router as notice_router
        except ModuleNotFoundError:
            notice_router = None

    if notice_router is not None:
        from fastapi import FastAPI
        # Reflex 的 _api 可能是 FastAPI 或 Starlette
        # 尝试以 FastAPI 方式挂载子路由
        if hasattr(app._api, "include_router"):
            app._api.include_router(notice_router)
        else:
            # 如果是 Starlette Router，逐个挂载 route
            for route in notice_router.routes:
                app._api.routes.append(route)
        print("[OA-EPP] 通知公告 API 路由已挂载")

# ─────────────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════
#  管理员/教师端页面（由负责人维护）
#  学生禁止修改，新增管理端页面请在这里显式注册
# ═══════════════════════════════════════════════════════════════════════════
_register_page(app, "/admin_students",  "admin_students",  "admin_students_page")
_register_page(app, "/admin_grades",    "admin_grades",    "admin_grades_page")
_register_page(app, "/admin_settings",  "admin_settings",  "admin_settings_page")
_register_page(app, "/admin_devops",    "admin_devops",    "admin_devops_page")

# ═══════════════════════════════════════════════════════════════════════════
#  学生功能页面 — 自动发现
#  规则：pages/xxx.py → xxx_page() → /xxx
#  学生创建 pages/grades.py 后直接访问 /grades，无需改 app.py
# ═══════════════════════════════════════════════════════════════════════════
_auto_discover(app)

# ── 通知公告页面 ─────────────────────────────────────────────────
# 学生端
try:
    from oaepp.pages.notifications import notifications_page, NotificationsState
except ModuleNotFoundError:
    try:
        from pages.notifications import notifications_page, NotificationsState
    except ModuleNotFoundError:
        notifications_page = None

if app is not None and notifications_page is not None:
    try:
        app.add_page(notifications_page, route="/notifications", title="公告与通知")
        print("[OA-EPP] 学生端通知页面已注册: /notifications")
    except Exception as e:
        print(f"[OA-EPP] 学生端通知页面注册失败: {e}")

# 教师端
try:
    from oaepp.pages.notifications_teacher import notifications_teacher_page, TeacherNotificationsState
except ModuleNotFoundError:
    try:
        from pages.notifications_teacher import notifications_teacher_page, TeacherNotificationsState
    except ModuleNotFoundError:
        notifications_teacher_page = None

if app is not None and notifications_teacher_page is not None:
    try:
        app.add_page(notifications_teacher_page, route="/notifications/teacher", title="通知管理")
        print("[OA-EPP] 教师端通知页面已注册: /notifications/teacher")
    except Exception as e:
        print(f"[OA-EPP] 教师端通知页面注册失败: {e}")


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
