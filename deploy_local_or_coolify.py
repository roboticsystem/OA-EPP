#!/usr/bin/env python3
"""
manage.py — 课程统一管理入口

启动后显示交互菜单：
  [1] 本地预览  — 同步 md/数据库 → 启动 MkDocs + FastAPI（热重载）
  [2] 远程部署  — 同步 md/数据库 → 确认已手动 git push → 触发 Coolify 重建
  [Q] 退出
"""

# ══════════════════════════════════════════════════════════════════════════════
#  标准库导入
# ══════════════════════════════════════════════════════════════════════════════
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

# ── 项目根目录 ─────────────────────────────────────────────────────────────────
REPO_ROOT        = Path(__file__).resolve().parent
BACKEND_DIR      = REPO_ROOT / "backend"
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"
BACKEND_REQ_FILE  = BACKEND_DIR / "requirements.txt"

# backend/ 加入模块搜索路径，使 `app.*` 可直接导入（幂等）
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── 本地服务器配置 ─────────────────────────────────────────────────────────────
HOST        = "127.0.0.1"
MKDOCS_PORT = 8008
API_PORT    = 8009

# ── Coolify 配置（从 .env 读取敏感数据）─────────────────────────────────────────
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

COOLIFY_BASE = "https://coolify.uwis.cn/api/v1"
COOLIFY_API_KEY = os.environ.get("COOLIFY_API_KEY", "")
PROJECT_NAME = "Robotics_Systems_Course"
APP_NAME     = "robotics_systems_course"
GIT_REPO     = "https://github.com/uwislab/robotics-systems-course.git"
GIT_BRANCH   = "main"
DOMAIN       = "https://robotic.uwis.cn"
ENVIRONMENT  = "production"
COMPOSE_SERVICE = "web"
API_ENV_VARS    = ["TEACHER_PASSWORD", "JWT_SECRET"]
# 容器内固定路径的环境变量（不来自本地 .env，而是远程容器的配置）
CONTAINER_FIXED_ENV = {
    "DOCS_DIR": "/app/docs",
    "DB_PATH":  "/app/data/exam.db",
}


# ══════════════════════════════════════════════════════════════════════════════
#  菜单
# ══════════════════════════════════════════════════════════════════════════════

def show_menu() -> str:
    print()
    print("╔" + "═" * 53 + "╗")
    print("║    🤖  研究生《机器人系统》课程新教材 — 管理工具    ║")
    print("╠" + "═" * 53 + "╣")
    print("║  [1]  本地预览   MkDocs + API（热重载）             ║")
    print("║  [2]  远程部署   触发 Coolify 重建                  ║")
    print("║  [Q]  退出                                          ║")
    print("╚" + "═" * 53 + "╝")
    while True:
        choice = input("请选择 [1 / 2 / Q]: ").strip().upper()
        if choice in ("1", "2", "Q"):
            return choice
        print("  ⚠️  请输入 1、2 或 Q")


# ══════════════════════════════════════════════════════════════════════════════
#  同步 .md ↔ 数据库（调用 backend/app/sync_exams，单一逻辑来源）
# ══════════════════════════════════════════════════════════════════════════════

def run_sync() -> dict:
    """调用 backend/app/sync_exams.sync_exams() 扫描 .md 并同步数据库。"""
    print("\n🔄 同步 .md 与数据库考试信息...")

    data_dir = REPO_ROOT / ".local_exam_data"
    data_dir.mkdir(exist_ok=True)
    db_path  = os.environ.get("DB_PATH",  str(data_dir / "exam.db"))
    docs_dir = os.environ.get("DOCS_DIR", str(REPO_ROOT / "docs"))

    # 在首次 import 前设置环境变量，让模块级常量读到正确值
    os.environ["DB_PATH"]  = db_path
    os.environ["DOCS_DIR"] = docs_dir

    import app.database  as _db
    import app.sync_exams as _se

    # 覆盖模块级变量（应对重复调用 / 模块已缓存的情况）
    _db.DB_PATH   = db_path
    _se.DOCS_DIR  = docs_dir

    # 建表（若尚不存在）
    from app.database import init_db
    init_db()

    summary  = _se.sync_exams()
    injected = summary.get("injected_meta", [])
    added    = summary.get("db_added", [])
    deleted  = summary.get("db_deleted", [])

    if injected: print(f"  📝 已注入 exam-meta：{injected}")
    if added:    print(f"  ➕ 数据库新增考试：{added}")
    if deleted:  print(f"  🗑️  数据库删除孤立考试：{deleted}")
    if not injected and not added and not deleted:
        print("  ✅ 已是最新，无需改动")

    return summary


# ══════════════════════════════════════════════════════════════════════════════
#  本地预览
# ══════════════════════════════════════════════════════════════════════════════

def _collect_pids_on_port(port: int):
    pid_set = set()
    for cmd in [["lsof", "-ti", f"tcp:{port}"], ["fuser", "-n", "tcp", str(port)]]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            continue
        text = (res.stdout or "") + " " + (res.stderr or "")
        for token in text.replace("\n", " ").split():
            if token.isdigit():
                pid_set.add(int(token))
    return sorted(pid_set)


def _is_port_busy(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True


def ensure_port_available(host: str, port: int):
    if not _is_port_busy(host, port):
        return
    print(f"⚠️  端口 {port} 已被占用，尝试清理旧进程...")
    pids = _collect_pids_on_port(port)
    if not pids:
        print("❌ 无法识别占用进程，请手动释放端口后重试")
        sys.exit(1)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    time.sleep(1)
    if _is_port_busy(host, port):
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(0.5)
    if _is_port_busy(host, port):
        print(f"❌ 端口 {port} 仍被占用，请手动检查后重试")
        sys.exit(1)
    print(f"✅ 端口 {port} 已释放")


def install_requirements():
    for req_file in [REQUIREMENTS_FILE, BACKEND_REQ_FILE]:
        if not req_file.exists():
            print(f"\n❌ 未找到依赖文件: {req_file}")
            sys.exit(1)
        print(f"⚙️  安装依赖：{req_file.relative_to(REPO_ROOT)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "-r", str(req_file)]
        )
    print("✅ 依赖安装完成\n")


def start_api_server():
    data_dir = REPO_ROOT / ".local_exam_data"
    data_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.setdefault("DB_PATH",          str(data_dir / "exam.db"))
    env.setdefault("TEACHER_PASSWORD", os.environ.get("TEACHER_PASSWORD", "admin123"))
    env.setdefault("JWT_SECRET",       os.environ.get("JWT_SECRET", "local-dev-secret-not-for-production"))
    env.setdefault("DOCS_DIR",         str(REPO_ROOT / "docs"))
    env["PYTHONPATH"] = str(BACKEND_DIR)
    # Ensure unbuffered output so logs appear immediately
    env.setdefault("PYTHONUNBUFFERED", "1")

    # Collect sensible reload directories: backend root, backend/app, docs and repo root
    reload_dirs = [
        str(BACKEND_DIR),
        str(BACKEND_DIR / "app"),
        str(REPO_ROOT / "docs"),
        str(REPO_ROOT),
    ]

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        HOST,
        "--port",
        str(API_PORT),
        "--reload",
    ]

    # Add --reload-dir entries
    for d in reload_dirs:
        cmd += ["--reload-dir", d]

    # Also watch common non-.py assets (md, html, css, js)
    for pat in ("*.py", "*.html", "*.md", "*.css", "*.js"):
        cmd += ["--reload-include", pat]

    popen_kwargs = dict(cwd=str(BACKEND_DIR), env=env)
    # On POSIX, start a new process group so we can terminate whole group later
    if os.name != "nt":
        popen_kwargs["preexec_fn"] = os.setsid

    return subprocess.Popen(cmd, **popen_kwargs)


def serve_local():
    install_requirements()
    ensure_port_available(HOST, MKDOCS_PORT)
    ensure_port_available(HOST, API_PORT)

    print("\n" + "=" * 55)
    print("  本地预览服务器（MkDocs + 考试后端）")
    print("=" * 55)
    print(f"📖 文档地址：  http://{HOST}:{MKDOCS_PORT}  （热重载）")
    teacher_pwd = os.environ.get("TEACHER_PASSWORD", "admin123")
    print(f"🎓 教师后台：  http://{HOST}:{API_PORT}/teacher  （密码：{teacher_pwd}）")
    print(f"📊 学生查分：  http://{HOST}:{API_PORT}/score")
    print(f"📡 API 文档：  http://{HOST}:{API_PORT}/api/docs")
    print("⛔ Ctrl+C 停止所有服务\n")

    api_proc = start_api_server()

    # 等待 API 就绪（最多 10 秒）
    for _ in range(20):
        time.sleep(0.5)
        try:
            with socket.create_connection((HOST, API_PORT), timeout=0.3):
                break
        except OSError:
            continue
    else:
        print("⚠️  考试 API 未能在 10 秒内启动，请检查日志")

    try:
        env = os.environ.copy()
        env.setdefault("NO_MKDOCS_2_WARNING", "1")
        subprocess.run(
            ["mkdocs", "serve", "-a", f"{HOST}:{MKDOCS_PORT}", "--open", "--watch-theme"],
            env=env, check=True, cwd=str(REPO_ROOT),
        )
    except KeyboardInterrupt:
        print("\n\n⛔ 正在停止所有服务...")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ MkDocs 启动失败: {e}")
    finally:
        api_proc.terminate()
        try:
            api_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        print("✅ 所有服务已停止")


# ══════════════════════════════════════════════════════════════════════════════
#  远程部署（Coolify）
# ══════════════════════════════════════════════════════════════════════════════

def _step(msg: str):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}")


def _coolify_api(method: str, path: str, **kwargs):
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {
        "Authorization": f"Bearer {COOLIFY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return requests.request(method, f"{COOLIFY_BASE}{path}", headers=headers,
                            verify=False, **kwargs)


def _fetch_logs(app_uuid: str):
    try:
        resp = _coolify_api("GET", f"/applications/{app_uuid}/logs")
        if not resp.ok:
            return None
        data = resp.json()
        if isinstance(data, dict):
            logs = data.get("logs", "")
            return logs if isinstance(logs, str) else ""
        return data if isinstance(data, str) else ""
    except Exception:
        return None


def _print_new_log_lines(full: str, last: str) -> str:
    if not full or full == last:
        return full
    delta = full[len(last):] if (last and full.startswith(last)) else (
        "[log window reset]\n" + "\n".join(full.splitlines()[-30:])
    )
    for line in delta.splitlines():
        if line.strip():
            print(f"  [deploy-log] {line.rstrip()}")
    return full


def _wait_for_site(app_uuid: str, timeout_sec: int = 240):
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    checks   = [f"{DOMAIN}/", f"{DOMAIN}/teacher"]
    deadline = time.time() + timeout_sec
    started  = time.time()
    min_wait = 40
    stable_need = 3
    streak   = 0
    last_status: dict = {}
    last_logs = ""

    print(f"⏳ 等待站点就绪（最多 {timeout_sec}s，至少等 {min_wait}s，连续 {stable_need} 轮通过）...")

    while time.time() < deadline:
        logs = _fetch_logs(app_uuid)
        if logs is not None:
            last_logs = _print_new_log_lines(logs, last_logs)

        all_ok = True
        for url in checks:
            try:
                r = requests.get(url, timeout=10, verify=False,
                                 headers={"Cache-Control": "no-cache"},
                                 params={"_h": int(time.time())})
                last_status[url] = r.status_code
                if r.status_code != 200:
                    all_ok = False
                    continue
                if url.endswith("/"):
                    body = (r.text or "").lower()
                    if not all(m in body for m in ["<html", "assets/stylesheets"]):
                        all_ok = False
                        last_status[url] = "200-invalid-html"
            except requests.RequestException:
                all_ok = False
                last_status[url] = "ERR"

        elapsed = int(time.time() - started)
        if all_ok and elapsed >= min_wait:
            streak += 1
        else:
            streak = 0

        if streak >= stable_need:
            print("✅ 站点已稳定就绪")
            return True

        print(f"  未就绪，8s 后重试  elapsed={elapsed}s streak={streak}/{stable_need} {last_status}")
        time.sleep(8)

    print("❌ 等待超时，请检查 Coolify 部署日志")
    print(f"  最后探测状态: {last_status}")
    return False


def _verify_exams_deployed():
    """部署后验证：登录教师账号，检查考试列表是否非空。"""
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    teacher_pwd = os.environ.get("TEACHER_PASSWORD", "admin123")
    base_url = f"{DOMAIN}/api/teacher"
    print("\n🔍 验证远端考试数据...")

    try:
        # 登录
        r = requests.post(f"{base_url}/login",
                          json={"password": teacher_pwd},
                          timeout=15, verify=False)
        if not r.ok:
            print(f"  ⚠️  教师登录失败 HTTP {r.status_code}")
            return

        token = r.json().get("token", "")
        if not token:
            print("  ⚠️  登录未返回 token")
            return

        # 查询考试列表
        r2 = requests.get(f"{base_url}/exams",
                          headers={"Authorization": f"Bearer {token}"},
                          timeout=15, verify=False)
        if not r2.ok:
            print(f"  ⚠️  考试列表接口返回 HTTP {r2.status_code}")
            return

        exams = r2.json()
        if isinstance(exams, list) and len(exams) > 0:
            print(f"  ✅ 远端教师后台已有 {len(exams)} 个考试：")
            for e in exams:
                print(f"     - [{e.get('id')}] {e.get('title')}")
        else:
            print(f"  ❌ 考试列表仍为空（{exams!r}）")
            print("     请检查容器启动日志中 [sync_exams] 的输出")

    except Exception as exc:
        print(f"  ⚠️  验证时出错：{exc}")


def _ensure_compose_domain(app_uuid: str):
    resp = _coolify_api("PATCH", f"/applications/{app_uuid}", json={
        "docker_compose_domains": [{"name": COMPOSE_SERVICE, "domain": DOMAIN}]
    })
    if resp.ok:
        print(f"✅ 已配置域名: {COMPOSE_SERVICE} → {DOMAIN}")
    else:
        print(f"⚠️  配置域名失败 HTTP {resp.status_code}: {resp.text}")


def _sync_env_vars(app_uuid: str):
    vars_to_sync = {k: os.environ.get(k, "") for k in API_ENV_VARS}
    missing = [k for k, v in vars_to_sync.items() if not v]
    if missing:
        print(f"⚠️  本地 .env 缺少 {missing}，将用 docker-compose 默认值")

    # 合并容器固定路径变量（DOCS_DIR、DB_PATH 等）
    all_vars = {**vars_to_sync, **CONTAINER_FIXED_ENV}

    # 先获取已存在的 env var 列表（key → id）
    existing_ids: dict[str, str] = {}
    r0 = _coolify_api("GET", f"/applications/{app_uuid}/envs")
    if r0.ok:
        for item in r0.json():
            existing_ids[item.get("key", "")] = str(item.get("uuid") or item.get("id", ""))

    for key, value in all_vars.items():
        if not value:
            continue
        if key in existing_ids and existing_ids[key]:
            # 已存在 → PATCH 更新（使用 env var 的 uuid/id）
            r = _coolify_api("PATCH", f"/applications/{app_uuid}/envs",
                             json={"key": key, "value": value})
        else:
            # 不存在 → POST 创建
            r = _coolify_api("POST", f"/applications/{app_uuid}/envs",
                             json={"key": key, "value": value, "is_build_time": False})
        if r.ok:
            print(f"  ✅ 环境变量 {key}")
        else:
            print(f"  ⚠️  环境变量 {key} 同步失败  HTTP {r.status_code}: {r.text}")


def deploy_coolify(sync_summary: dict):
    # ── 前置检查 ──────────────────────────────────────────────────────────────
    if not COOLIFY_API_KEY:
        print("❌ 缺少 COOLIFY_API_KEY，请检查 .env 文件")
        sys.exit(1)

    try:
        import requests  # noqa: F401
    except ImportError:
        print("⚙️  安装部署依赖（requests / urllib3）...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "requests", "urllib3"]
        )

    _step("Step 1: 检查源文件")
    for required in ["mkdocs.yml", "docs", "nginx.conf", "docker-compose.yaml", "backend"]:
        if not (REPO_ROOT / required).exists():
            print(f"❌ 缺少必要文件: {required}")
            sys.exit(1)
    print("✅ 源文件检查通过")

    # ── 提示用户确认已推送最新代码 ───────────────────────────────────────────
    _step("Step 2: 确认 Git 已推送")
    injected = sync_summary.get("injected_meta", [])
    if injected:
        print(f"⚠️  sync 刚修改了以下文件，请先提交并推送后再继续：")
        for f in injected:
            print(f"     docs/{f}")
        print()
        confirm = input("已完成 git commit & push？继续部署请输入 y，取消请输入 n: ").strip().lower()
        if confirm != "y":
            print("🚫 已取消部署")
            sys.exit(0)
    else:
        print("✅ sync 未修改任何 .md 文件，无需额外提交")

    # ── Coolify 项目 ─────────────────────────────────────────────────────────
    _step("Step 3: 查找 / 创建 Coolify 项目")
    resp = _coolify_api("GET", "/projects")
    resp.raise_for_status()
    project = next((p for p in resp.json() if p["name"] == PROJECT_NAME), None)
    if project:
        project_uuid = project["uuid"]
        print(f"✅ 已有项目: {PROJECT_NAME}  uuid={project_uuid}")
    else:
        resp = _coolify_api("POST", "/projects",
                            json={"name": PROJECT_NAME, "description": "机器人系统课程"})
        resp.raise_for_status()
        project_uuid = resp.json()["uuid"]
        print(f"✅ 已创建项目: {PROJECT_NAME}  uuid={project_uuid}")

    # ── Server ───────────────────────────────────────────────────────────────
    _step("Step 4: 获取可用 Server")
    resp = _coolify_api("GET", "/servers")
    resp.raise_for_status()
    server = next((s for s in resp.json() if s.get("is_usable")), None)
    if not server:
        print("❌ 没有可用 Server，请检查 Coolify 面板")
        sys.exit(1)
    server_uuid = server["uuid"]
    print(f"✅ Server: {server['name']}  uuid={server_uuid}")

    # ── 应用查找或创建 ────────────────────────────────────────────────────────
    _step("Step 5: 查找 / 创建应用并触发部署")
    resp = _coolify_api("GET", "/applications")
    resp.raise_for_status()
    git_suffix = GIT_REPO.split("github.com/")[-1]
    app = next(
        (a for a in resp.json() if (
            a.get("git_repository") in (git_suffix, GIT_REPO) or
            a.get("name") == APP_NAME or
            a.get("fqdn") == DOMAIN
        )), None
    )

    if app:
        app_uuid = app["uuid"]
        print(f"✅ 已有应用: {app.get('name')}  uuid={app_uuid}")

        patch = _coolify_api("PATCH", f"/applications/{app_uuid}",
                              json={"build_pack": "dockercompose", "install_command": ""})
        if patch.ok:
            print("✅ 应用配置已更新（build_pack=dockercompose）")

        _ensure_compose_domain(app_uuid)
        _sync_env_vars(app_uuid)

        resp = _coolify_api("POST", f"/applications/{app_uuid}/start",
                            json={"force_rebuild": True})
        data = resp.json()
        if resp.ok or "queued" in str(data).lower() or "deployment" in str(data).lower():
            print("✅ 强制重建已触发")
        else:
            print(f"❌ 触发失败 HTTP {resp.status_code}: {resp.text}")
            sys.exit(1)
    else:
        payload = {
            "project_uuid":           project_uuid,
            "server_uuid":            server_uuid,
            "environment_name":       ENVIRONMENT,
            "git_repository":         GIT_REPO,
            "git_branch":             GIT_BRANCH,
            "build_pack":             "dockercompose",
            "name":                   APP_NAME,
            "docker_compose_domains": [{"name": COMPOSE_SERVICE, "domain": DOMAIN}],
            "is_auto_deploy_enabled": True,
            "instant_deploy":         True,
            "ports_exposes":          "80",
        }
        resp = _coolify_api("POST", "/applications/public", json=payload)
        if resp.status_code not in (200, 201):
            print(f"❌ 创建失败 HTTP {resp.status_code}: {resp.text}")
            sys.exit(1)
        data   = resp.json()
        app_uuid = data.get("uuid")
        _sync_env_vars(app_uuid)
        print(f"✅ 应用创建成功！  uuid={app_uuid}")

    if not _wait_for_site(app_uuid):
        sys.exit(1)

    _verify_exams_deployed()

    print(f"\n🌐 站点地址: {DOMAIN}")
    print("🎉 部署完成，可直接访问课程内容")


# ══════════════════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════════════════

def main():
    choice = show_menu()

    if choice == "Q":
        print("👋 退出")
        sys.exit(0)

    # ── 无论本地还是远程，都先同步 md ↔ 数据库 ──────────────────────────────
    sync_summary = run_sync()

    if choice == "1":
        serve_local()
    elif choice == "2":
        deploy_coolify(sync_summary)


if __name__ == "__main__":
    main()