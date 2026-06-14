"""
OA-EPP Reflex app — 路由注册 & 启动入口

路由规则：
  - 所有页面：pages/xxx.py → xxx_page() → 自动注册到 /xxx
  - 特殊路由：login → /（首页，显式注册）
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
      - login（特殊路由 /，已由显式注册处理）
    """
    if app is None:
        return

    # 已由显式路由特殊处理的模块（不需要自动发现）
    _skip_modules = {"login", "__init__"}

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

    async def _api_grade_export(request):
        """F-S-032：学生一键下载本人全期成绩单（.xlsx）"""
        from starlette.responses import Response
        from urllib.parse import quote

        student_no = request.query_params.get("student_no", "")
        if not student_no:
            return JSONResponse({"error": "缺少 student_no 参数"}, status_code=400)

        try:
            from states.grade_export import GradeExportState
        except Exception:
            try:
                from oaepp.states.grade_export import GradeExportState
            except Exception:
                return JSONResponse({"error": "GradeExportState 加载失败"}, status_code=500)

        state = GradeExportState()
        file_bytes = state.export_my_grades(student_no)

        if file_bytes is None:
            return JSONResponse(
                {"error": state.export_error or "导出失败"}, status_code=500
            )

        filename = state.get_export_filename(student_no)
        # RFC 5987: filename*=UTF-8''percent-encoded-filename
        encoded_filename = quote(filename, safe="")

        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            },
        )

    app._api.routes.append(Route("/api/hello", _api_hello, methods=["GET"]))
    app._api.routes.append(Route("/api/status", _api_status, methods=["GET"]))
    app._api.routes.append(Route("/api/grade-export", _api_grade_export, methods=["POST"]))

# ── 显式路由（特殊路由，如首页 /） ────────────────────────────────────────
_register_page(app, "/", "login", "login_page")

# ═══════════════════════════════════════════════════════════════════════════
#  所有页面 — 自动发现
#  规则：pages/xxx.py → xxx_page() → /xxx
#  学生页面、管理员页面均自动注册，无需修改此文件
# ═══════════════════════════════════════════════════════════════════════════
_auto_discover(app)


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
