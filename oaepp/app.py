"""OA-EPP Reflex app — 路由注册 & 启动入口

路由规则：
  - 所有页面：pages/xxx.py → xxx_page() → 自动注册到 /xxx
  - 特殊路由：login → /（首页，显式注册）
  - 课程和章节浏览 → 显式注册（F-S-010 + F-S-011）
"""
import importlib
import shutil
import sys
from pathlib import Path

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.states.chapter import ChapterState


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
    """自动发现 pages/ 目录下的页面模块。"""
    if app is None:
        return
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
    page_fn = getattr(courses_mod, "courses_page_component", None)
    if page_fn is not None and callable(page_fn):
        try:
            app.add_page(page_fn, route="/courses",
                         title="课程学习 - OA-EPP",
                         on_load=ChapterState.load_courses)
        except Exception:
            pass


# ── chapter 章节内容详情页（F-S-011 章节浏览） ────────────────────────

try:
    from pages import chapter_detail as chapter_mod
except Exception:
    try:
        from oaepp.pages import chapter_detail as chapter_mod
    except Exception:
        chapter_mod = None

if app is not None and chapter_mod is not None:
    page_fn = getattr(chapter_mod, "chapter_page_component", None)
    if page_fn is not None and callable(page_fn):
        try:
            app.add_page(page_fn, route="/chapter",
                         title="章节内容 - OA-EPP")
        except Exception:
            pass


# ── 显式路由 ──────────────────────────────────────────────────────────
_register_page(app, "/", "login", "login_page")

# ── 自动发现（其余页面） ─────────────────────────────────────────────
_auto_discover(app)


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
