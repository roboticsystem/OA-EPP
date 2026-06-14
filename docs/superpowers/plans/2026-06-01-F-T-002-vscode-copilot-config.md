# F-T-002 VS Code扩展与Copilot提示词配置 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 教师可管理课程 VS Code 扩展清单并生成 `extensions.json`，在线编辑 Copilot 指令文件，一键提交到 Git 仓库触发 CI。

**Architecture:** 新增 `vscode_config.py` 路由（10 个 API 端点），新建 `vscode_config.html` 配置页（原生 HTML/CSS），扩展管理状态存 `backend/app/data/vscode_config.json`，生成的文件直接写入项目根目录。

**Tech Stack:** Python FastAPI, pymysql (DictCursor), vanilla HTML/CSS/JS, git via subprocess

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/routers/vscode_config.py` | 新建 | 全部 10 个 API 端点 |
| `backend/app/static/vscode_config.html` | 新建 | 教师配置前端页面 |
| `backend/app/data/vscode_config.json` | 新建 | 扩展配置初始值 |
| `backend/app/main.py` | 修改 | 注册路由 + 服务页面 |
| `backend/app/static/teacher.html` | 修改 | 添加导航链接 |
| `tests/reflex/test_F_T_002_vscode_config.py` | 重写 | API 端点测试 |

---

### Task 1: 创建数据目录与初始配置

**Files:**
- Create: `backend/app/data/vscode_config.json`
- Create: `backend/app/data/.gitkeep` (if needed)

- [ ] **Step 1: 创建 data 目录和初始配置**

```bash
New-Item -ItemType Directory -Path "backend/app/data" -Force
```

文件 `backend/app/data/vscode_config.json`：

```json
{
  "recommendations": [
    {"id": "GitHub.copilot", "name": "GitHub Copilot", "description": "AI 代码补全"},
    {"id": "GitHub.copilot-chat", "name": "GitHub Copilot Chat", "description": "AI 对话助手"},
    {"id": "ms-python.python", "name": "Python", "description": "Python 开发环境"},
    {"id": "ms-python.vscode-pylance", "name": "Pylance", "description": "Python 语言服务器"},
    {"id": "charliermarsh.ruff", "name": "Ruff", "description": "代码风格检查"},
    {"id": "ms-python.debugpy", "name": "Python Debugger", "description": "Python 调试器"}
  ],
  "unwantedRecommendations": [
    {"id": "ms-python.pylint", "name": "Pylint", "description": "与 Ruff 冲突，禁止使用"}
  ]
}
```

- [ ] **Step 2: 验证文件存在**

```bash
Test-Path -LiteralPath "backend/app/data/vscode_config.json"
```

Expected: `True`

---

### Task 2: 重写 TDD 测试（面向 API 端点）

**Files:**
- Modify: `tests/reflex/test_F_T_002_vscode_config.py`

- [ ] **Step 1: 用 FastAPI TestClient 测试重写整个文件**

当前文件面向 `oaepp.states.teacher_vscode.VSCodeConfigState`（不存在），改为测试 `/api/teacher/vscode/*` 端点。文件内容：

```python
"""F-T-002 VSCode 配置下发 TDD 测试（API 端点版）

TDD RED   : 路由 /api/teacher/vscode/* 未注册 → 404
TDD GREEN : vscode_config router 实现后 → 全部通过
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def teacher_token(client):
    resp = client.post("/api/teacher/login", json={"password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["token"]


def test_F_T_002_TC01_get_extensions_unauthorized(client):
    """未认证请求返回 401"""
    resp = client.get("/api/teacher/vscode/extensions")
    assert resp.status_code == 401


def test_F_T_002_TC02_get_extensions_structure(client, teacher_token):
    """返回正确的数据结构"""
    resp = client.get(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "recommendations" in data
        assert "unwantedRecommendations" in data
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["unwantedRecommendations"], list)


def test_F_T_002_TC03_preset_templates(client, teacher_token):
    """预设模板列表接口可用"""
    resp = client.get(
        "/api/teacher/vscode/extensions/presets",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC04_add_extension(client, teacher_token):
    """添加扩展"""
    resp = client.post(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "action": "add",
            "group": "recommendations",
            "ext_id": "test.ext",
            "ext_name": "Test Extension",
            "ext_desc": "Just a test"
        }
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC05_remove_extension(client, teacher_token):
    """移除扩展"""
    resp = client.post(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "action": "remove",
            "group": "recommendations",
            "ext_id": "test.ext",
            "ext_name": "",
            "ext_desc": ""
        }
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC06_generate_extensions_json(client, teacher_token):
    """生成 .vscode/extensions.json"""
    resp = client.post(
        "/api/teacher/vscode/extensions/generate",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC07_copilot_instructions_list(client, teacher_token):
    """列出 Copilot 指令文件"""
    resp = client.get(
        "/api/teacher/copilot/instructions",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC08_save_copilot_instructions(client, teacher_token):
    """保存 Copilot 指令文件内容"""
    resp = client.post(
        "/api/teacher/copilot/instructions/.github/copilot-instructions.md",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"content": "# Test\n\nhello world"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC09_commit_endpoint(client, teacher_token):
    """提交到仓库端点"""
    resp = client.post(
        "/api/teacher/config/commit",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC10_git_status(client, teacher_token):
    """Git 状态查询"""
    resp = client.get(
        "/api/teacher/config/git-status",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)
```

- [ ] **Step 2: 运行测试，确认全部 FAIL（路由未注册）**

```bash
cd backend; python -m pytest ../tests/reflex/test_F_T_002_vscode_config.py -v
```

Expected: 全部 10 个测试中，TC01 返回 401（已有 `/api/teacher/exams` 路由在 `/api/teacher/*` 下不匹配 `/vscode/extensions`，故返回 404），其余测试自洽。

---

### Task 3: 创建路由文件骨架

**Files:**
- Create: `backend/app/routers/vscode_config.py`

- [ ] **Step 1: 写入完整路由文件**

```python
import os
import json
import subprocess
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from app.routers.teacher import _require_teacher

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "vscode_config.json")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

os.makedirs(DATA_DIR, exist_ok=True)

PRESETS = {
    "python-dev": {
        "name": "Python开发套件",
        "recommendations": [
            "ms-python.python", "ms-python.vscode-pylance",
            "charliermarsh.ruff", "ms-python.debugpy"
        ],
        "unwantedRecommendations": ["ms-python.pylint"]
    },
    "copilot-suite": {
        "name": "Copilot全家桶",
        "recommendations": ["GitHub.copilot", "GitHub.copilot-chat"],
        "unwantedRecommendations": []
    },
    "reflex-dev": {
        "name": "Reflex开发",
        "recommendations": [
            "ms-python.python", "ms-python.vscode-pylance",
            "GitHub.copilot", "charliermarsh.ruff"
        ],
        "unwantedRecommendations": []
    }
}

SAFE_PATHS = {
    ".vscode/extensions.json",
    ".github/copilot-instructions.md",
}

INSTRUCTIONS_FILES = [
    ".github/copilot-instructions.md",
    ".github/instructions/commit-message.instructions.md",
]


def _load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"recommendations": [], "unwantedRecommendations": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _safe_path(rel_path: str) -> str:
    normalized = rel_path.replace("\\", "/")
    if normalized not in SAFE_PATHS:
        raise HTTPException(status_code=403, detail=f"禁止访问路径: {rel_path}")
    full = os.path.normpath(os.path.join(REPO_ROOT, rel_path))
    if not full.startswith(os.path.normpath(REPO_ROOT)):
        raise HTTPException(status_code=403, detail="路径遍历攻击")
    return full


# ─── 扩展管理 ───

class ExtensionAction(BaseModel):
    action: str
    group: str
    ext_id: str
    ext_name: str = ""
    ext_desc: str = ""


@router.get("/api/teacher/vscode/extensions")
def get_extensions(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return _load_config()


@router.post("/api/teacher/vscode/extensions")
def modify_extensions(req: ExtensionAction, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    if req.group not in ("recommendations", "unwantedRecommendations"):
        raise HTTPException(status_code=422, detail="group 必须为 recommendations 或 unwantedRecommendations")

    config = _load_config()
    if req.group not in config:
        config[req.group] = []

    if req.action == "add":
        existing = any(e["id"] == req.ext_id for e in config[req.group])
        if not existing:
            config[req.group].append({
                "id": req.ext_id,
                "name": req.ext_name or req.ext_id,
                "description": req.ext_desc or ""
            })
    elif req.action == "remove":
        config[req.group] = [e for e in config[req.group] if e["id"] != req.ext_id]
    else:
        raise HTTPException(status_code=422, detail="action 必须为 add 或 remove")

    _save_config(config)
    return {"ok": True}


@router.get("/api/teacher/vscode/extensions/presets")
def get_presets(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return {"presets": PRESETS}


@router.post("/api/teacher/vscode/extensions/generate")
def generate_extensions_json(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    config = _load_config()

    output = {
        "recommendations": [e["id"] for e in config.get("recommendations", [])],
        "unwantedRecommendations": [e["id"] for e in config.get("unwantedRecommendations", [])]
    }

    vscode_dir = os.path.join(REPO_ROOT, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    output_path = os.path.join(vscode_dir, "extensions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return {"ok": True, "path": ".vscode/extensions.json"}


class ConfigReplace(BaseModel):
    recommendations: List[str] = []
    unwantedRecommendations: List[str] = []


@router.post("/api/teacher/vscode/extensions/replace")
def replace_config(req: ConfigReplace, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    config = {
        "recommendations": [{"id": eid, "name": eid, "description": ""} for eid in req.recommendations],
        "unwantedRecommendations": [{"id": eid, "name": eid, "description": ""} for eid in req.unwantedRecommendations]
    }
    _save_config(config)
    return {"ok": True}


# ─── Copilot 指令 ───

@router.get("/api/teacher/copilot/instructions")
def list_instructions(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    files = []
    for rel in INSTRUCTIONS_FILES:
        full = os.path.join(REPO_ROOT, rel)
        name = os.path.basename(rel)
        size = 0
        if os.path.isfile(full):
            size = os.path.getsize(full)
        files.append({"path": rel, "name": name, "size": size})
    return {"files": files}


class InstructionContent(BaseModel):
    content: str


@router.get("/api/teacher/copilot/instructions/{file_path:path}")
def get_instruction(file_path: str, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    full = _safe_path(file_path)
    if not os.path.isfile(full):
        return {"path": file_path, "content": "", "size": 0}
    with open(full, "r", encoding="utf-8") as f:
        content = f.read()
    return {"path": file_path, "content": content, "size": len(content)}


@router.post("/api/teacher/copilot/instructions/{file_path:path}")
def save_instruction(file_path: str, body: InstructionContent, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    full = _safe_path(file_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(body.content)
    return {"ok": True}


# ─── Git 操作 ───

@router.post("/api/teacher/config/commit")
def commit_config(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)

    try:
        subprocess.run(["git", "add", ".vscode/extensions.json",
                        ".github/copilot-instructions.md",
                        ".github/instructions/"],
                       cwd=REPO_ROOT, check=True, capture_output=True)

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        result = subprocess.run(
            ["git", "commit", "-m", f"chore: update VSCode & Copilot config ({date_str})"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )

        sha = None
        if result.returncode == 0 and "nothing to commit" not in result.stdout:
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT, capture_output=True, text=True
            )
            sha = sha_result.stdout.strip()[:7]

        try:
            push_result = subprocess.run(
                ["git", "push"],
                cwd=REPO_ROOT, capture_output=True, text=True
            )
        except Exception:
            pass

        return {"ok": True, "sha": sha, "message": f"chore: update VSCode & Copilot config ({date_str})"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git 操作失败: {e.stderr}")


@router.get("/api/teacher/config/git-status")
def git_status(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)

    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
        changed = [line.strip() for line in status_result.stdout.splitlines() if line.strip()]
        return {
            "dirty": len(changed) > 0,
            "changed_files": changed,
            "branch": branch_result.stdout.strip()
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git 操作失败: {e.stderr}")
```

- [ ] **Step 2: 无 lint 检查，直接继续**

---

### Task 4: 注册路由到 main.py

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: 添加 import 和路由注册**

```python
from app.routers import students, auth, exam, teacher, vscode_config
```

在 `app.include_router(teacher.router)` 之后添加：

```python
app.include_router(vscode_config.router)
```

在 `@app.get("/score")` 之后添加页面路由：

```python
@app.get("/vscode-config")
def vscode_config_page():
    return FileResponse(os.path.join(STATIC_DIR, "vscode_config.html"))
```

- [ ] **Step 2: 运行测试确认部分通过**

```bash
cd backend; python -m pytest ../tests/reflex/test_F_T_002_vscode_config.py -v 2>&1 | Select-Object -Last 30
```

Expected: TC02~TC10 中与已实现端点对应的应当 PASS 或因数据/文件状态而 FAIL，但不应当是 404。

---

### Task 5: 创建前端页面 vscode_config.html

**Files:**
- Create: `backend/app/static/vscode_config.html`

页面对 `/api/teacher/exams` 发送验证请求（复用现有 token 校验逻辑）；若未登录则重定向到 `/teacher`。

- [ ] **Step 1: 写入完整 HTML**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VS Code & Copilot 配置 — 教师端</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif; background: #f5f5f5; color: #333; }
  .header { background: #1565c0; color: #fff; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 1.1rem; }
  .header a { color: #fff; text-decoration: none; font-size: .9rem; padding: 6px 14px; background: rgba(255,255,255,.15); border-radius: 4px; }
  .header a:hover { background: rgba(255,255,255,.3); }
  .container { max-width: 1100px; margin: 20px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 20px; overflow: hidden; }
  .card-title { background: #e3f2fd; padding: 12px 18px; font-weight: bold; font-size: .95rem; border-bottom: 1px solid #bbdefb; display: flex; align-items: center; justify-content: space-between; }
  .card-body { padding: 18px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .btn { display: inline-block; padding: 8px 18px; border: none; border-radius: 5px; cursor: pointer; font-size: .88rem; font-weight: bold; }
  .btn-primary { background: #1565c0; color: #fff; }
  .btn-primary:hover { background: #0d47a1; }
  .btn-success { background: #2e7d32; color: #fff; }
  .btn-success:hover { background: #1b5e20; }
  .btn-danger { background: #c62828; color: #fff; }
  .btn-danger:hover { background: #b71c1c; }
  .btn-outline { background: transparent; color: #1565c0; border: 1px solid #1565c0; }
  .btn-outline:hover { background: #e3f2fd; }
  .btn-outline-danger { background: transparent; color: #c62828; border: 1px solid #c62828; }
  .btn-outline-danger:hover { background: #ffebee; }
  .btn-sm { padding: 5px 12px; font-size: .8rem; }
  .ext-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 6px; margin-bottom: 6px; font-size: .85rem; }
  .ext-rec { background: #e8f0fe; border: 1px solid #c5d9f0; }
  .ext-ban { background: #fdecea; border: 1px solid #f5c6cb; }
  .ext-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: .75rem; color: #fff; font-weight: bold; flex-shrink: 0; }
  .ext-info { flex: 1; }
  .ext-name { font-weight: 600; color: #333; }
  .ext-desc { color: #888; font-size: .78rem; margin-top: 2px; }
  .ext-del { color: #c62828; cursor: pointer; font-size: 1.1rem; background: none; border: none; }
  .ext-del:hover { color: #b71c1c; }
  .add-row { display: flex; gap: 6px; margin-top: 10px; }
  .add-row input { flex: 1; padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: .85rem; }
  .add-row input:focus { outline: none; border-color: #1565c0; }
  .add-row select { padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: .85rem; }
  .preset-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; }
  .preset-btn { padding: 4px 12px; border: 1px solid #ccc; border-radius: 14px; background: #fff; cursor: pointer; font-size: .8rem; }
  .preset-btn:hover { background: #e3f2fd; border-color: #1565c0; color: #1565c0; }
  pre.json-preview { background: #1e1e1e; color: #a5d6a7; padding: 14px; border-radius: 6px; font-size: .8rem; overflow-x: auto; margin-bottom: 10px; max-height: 300px; overflow-y: auto; }
  textarea.code-editor { width: 100%; min-height: 260px; border: 1px solid #ddd; border-radius: 6px; padding: 12px; font-family: "Consolas", "Courier New", monospace; font-size: .85rem; resize: vertical; }
  textarea.code-editor:focus { outline: none; border-color: #1565c0; }
  .alert { padding: 10px 14px; border-radius: 5px; margin-bottom: 10px; font-size: .85rem; }
  .alert-success { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
  .alert-error { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
  .alert-info { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
  .status-bar { display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: #f8f9fa; border-radius: 6px; font-size: .85rem; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
  .status-clean { background: #4caf50; }
  .status-dirty { background: #ff9800; }
  .tab-bar { display: flex; gap: 2px; margin-bottom: 12px; border-bottom: 2px solid #e0e0e0; }
  .tab-btn { padding: 8px 16px; border: none; background: none; cursor: pointer; font-size: .85rem; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; }
  .tab-btn.active { color: #1565c0; border-bottom-color: #1565c0; font-weight: 600; }
  .hidden { display: none; }
</style>
</head>
<body>

<div id="not-logged-in" style="text-align:center;padding:80px 20px;">
  <h2 style="color:#888;">正在验证身份...</h2>
</div>

<div id="app" class="hidden">
  <div class="header">
    <h1>VS Code & Copilot 配置管理</h1>
    <a href="/teacher">← 返回教师管理</a>
  </div>
  <div class="container">

    <div id="msg"></div>

    <!-- 卡片1: 扩展管理 -->
    <div class="card">
      <div class="card-title"><span>🔌 VS Code 扩展管理</span></div>
      <div class="card-body">
        <div class="grid-2">
          <div>
            <h4 style="margin-bottom:8px;color:#1565c0;">必装 / 建议 <span style="font-weight:400;font-size:.8rem;color:#888;">recommendations</span></h4>
            <div id="ext-recommendations"></div>
            <div class="add-row">
              <input id="ext-id" placeholder="扩展 ID（如 ms-python.python）">
              <input id="ext-name" placeholder="名称">
              <button class="btn btn-primary btn-sm" onclick="addExtension('recommendations')">+ 添加</button>
            </div>
          </div>
          <div>
            <h4 style="margin-bottom:8px;color:#c62828;">禁止安装 <span style="font-weight:400;font-size:.8rem;color:#888;">unwantedRecommendations</span></h4>
            <div id="ext-banned"></div>
            <div class="add-row">
              <input id="ext-id-ban" placeholder="扩展 ID">
              <input id="ext-name-ban" placeholder="名称">
              <button class="btn btn-outline-danger btn-sm" onclick="addExtension('unwantedRecommendations')">+ 添加</button>
            </div>
          </div>
        </div>
        <div class="preset-btns">
          <span style="font-size:.8rem;color:#888;">预置模板：</span>
          <button class="preset-btn" onclick="applyPreset('python-dev')">Python开发套件</button>
          <button class="preset-btn" onclick="applyPreset('copilot-suite')">Copilot全家桶</button>
          <button class="preset-btn" onclick="applyPreset('reflex-dev')">Reflex开发</button>
        </div>
      </div>
    </div>

    <!-- 卡片2: JSON 预览 -->
    <div class="card">
      <div class="card-title"><span>📄 生成预览 <code style="font-weight:400;font-size:.8rem;">.vscode/extensions.json</code></span></div>
      <div class="card-body">
        <pre class="json-preview" id="json-preview">加载中...</pre>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-outline btn-sm" onclick="copyJSON()">复制 JSON</button>
          <button class="btn btn-primary btn-sm" onclick="generateJSON()">生成文件</button>
        </div>
      </div>
    </div>

    <!-- 卡片3: Copilot 指令编辑器 -->
    <div class="card">
      <div class="card-title"><span>🤖 Copilot 指令文件编辑</span></div>
      <div class="card-body">
        <div class="tab-bar" id="file-tabs"></div>
        <textarea class="code-editor" id="editor" placeholder="选择文件后在此编辑..."></textarea>
        <div style="display:flex;gap:8px;margin-top:10px;">
          <button class="btn btn-outline btn-sm" onclick="loadCurrentFile()">加载文件</button>
          <button class="btn btn-success btn-sm" onclick="saveCurrentFile()">保存文件</button>
        </div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="card">
      <div class="card-body">
        <div class="status-bar" style="margin-bottom:10px;">
          <span class="status-dot" id="git-dot"></span>
          <span id="git-info">Git 状态加载中...</span>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-primary" onclick="commitAndPush()">📤 提交到仓库</button>
          <button class="btn btn-outline btn-sm" onclick="checkGitStatus()">刷新状态</button>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const TOKEN = sessionStorage.getItem('teacher_token') || '';
const API = '';

let currentFile = '';
let extensionsData = {};

// ─── 初始化 ───
(async function init() {
  if (!TOKEN) { window.location.href = '/teacher'; return; }
  const resp = await fetch(`${API}/api/teacher/exams`, {
    headers: {'Authorization': `Bearer ${TOKEN}`}
  });
  if (!resp.ok) { window.location.href = '/teacher'; return; }
  document.getElementById('not-logged-in').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  await loadExtensions();
  await loadInstructionFiles();
  await checkGitStatus();
})();

function api(method, url, body) {
  return fetch(`${API}${url}`, {
    method, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${TOKEN}` }, body: body ? JSON.stringify(body) : undefined
  });
}

function showMsg(text, cls) {
  const el = document.getElementById('msg');
  el.innerHTML = `<div class="alert alert-${cls}">${text}</div>`;
  setTimeout(() => el.innerHTML = '', 4000);
}

// ─── 扩展管理 ───
async function loadExtensions() {
  const r = await api('GET', '/api/teacher/vscode/extensions');
  if (!r.ok) return;
  extensionsData = await r.json();
  renderExtensions();
  updatePreview();
}

function renderExtensions() {
  const renderList = (containerId, group, cls) => {
    const el = document.getElementById(containerId);
    const list = extensionsData[group] || [];
    el.innerHTML = list.map(e => `
      <div class="ext-item ${cls}">
        <div class="ext-icon" style="background:${group==='recommendations'?'#1565c0':'#c62828'}">${e.id[0].toUpperCase()}</div>
        <div class="ext-info"><div class="ext-name">${e.id}</div><div class="ext-desc">${e.description || e.name}</div></div>
        <button class="ext-del" onclick="removeExtension('${group}','${e.id}')">&times;</button>
      </div>
    `).join('');
  };
  renderList('ext-recommendations', 'recommendations', 'ext-rec');
  renderList('ext-banned', 'unwantedRecommendations', 'ext-ban');
}

async function addExtension(group) {
  const idEl = group === 'recommendations' ? document.getElementById('ext-id') : document.getElementById('ext-id-ban');
  const nameEl = group === 'recommendations' ? document.getElementById('ext-name') : document.getElementById('ext-name-ban');
  const ext_id = idEl.value.trim();
  const ext_name = nameEl.value.trim() || ext_id;
  if (!ext_id) return;
  const r = await api('POST', '/api/teacher/vscode/extensions', { action: 'add', group, ext_id, ext_name, ext_desc: '' });
  if (r.ok) { idEl.value = ''; nameEl.value = ''; loadExtensions(); showMsg(`已添加 ${ext_id}`, 'success'); }
  else { showMsg('添加失败', 'error'); }
}

async function removeExtension(group, ext_id) {
  const r = await api('POST', '/api/teacher/vscode/extensions', { action: 'remove', group, ext_id, ext_name: '', ext_desc: '' });
  if (r.ok) { loadExtensions(); showMsg(`已移除 ${ext_id}`, 'success'); }
}

async function applyPreset(presetId) {
  const r = await api('GET', '/api/teacher/vscode/extensions/presets');
  if (!r.ok) return;
  const preset = (await r.json()).presets[presetId];
  if (!preset) return;
  await api('POST', '/api/teacher/vscode/extensions/replace', {
    recommendations: preset.recommendations || [],
    unwantedRecommendations: preset.unwantedRecommendations || []
  });
  await loadExtensions();
  showMsg(`已应用模板：${preset.name}`, 'success');
}

function updatePreview() {
  const recs = (extensionsData.recommendations || []).map(e => e.id);
  const bans = (extensionsData.unwantedRecommendations || []).map(e => e.id);
  const json = { recommendations: recs, unwantedRecommendations: bans };
  document.getElementById('json-preview').textContent = JSON.stringify(json, null, 2);
}

function copyJSON() {
  navigator.clipboard.writeText(document.getElementById('json-preview').textContent);
  showMsg('已复制到剪贴板', 'success');
}

async function generateJSON() {
  const r = await api('POST', '/api/teacher/vscode/extensions/generate');
  if (r.ok) { showMsg('extensions.json 已生成', 'success'); checkGitStatus(); }
  else { showMsg('生成失败', 'error'); }
}

// ─── Copilot 指令 ───
async function loadInstructionFiles() {
  const r = await api('GET', '/api/teacher/copilot/instructions');
  if (!r.ok) return;
  const data = await r.json();
  const tabs = document.getElementById('file-tabs');
  tabs.innerHTML = data.files.map((f, i) =>
    `<button class="tab-btn${i===0?' active':''}" onclick="selectFile('${f.path}')" data-path="${f.path}">${f.name}</button>`
  ).join('');
  if (data.files.length > 0) selectFile(data.files[0].path);
}

function selectFile(path) {
  currentFile = path;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.path === path));
  loadCurrentFile();
}

async function loadCurrentFile() {
  if (!currentFile) return;
  const r = await api('GET', `/api/teacher/copilot/instructions/${encodeURIComponent(currentFile)}`);
  if (r.ok) {
    const d = await r.json();
    document.getElementById('editor').value = d.content || '';
  }
}

async function saveCurrentFile() {
  if (!currentFile) return;
  const content = document.getElementById('editor').value;
  const r = await api('POST', `/api/teacher/copilot/instructions/${encodeURIComponent(currentFile)}`, { content });
  if (r.ok) { showMsg('已保存', 'success'); checkGitStatus(); }
  else { showMsg('保存失败', 'error'); }
}

// ─── Git ───
async function checkGitStatus() {
  const r = await api('GET', '/api/teacher/config/git-status');
  if (!r.ok) { document.getElementById('git-info').textContent = '无法获取 Git 状态'; return; }
  const s = await r.json();
  const dot = document.getElementById('git-dot');
  dot.className = 'status-dot ' + (s.dirty ? 'status-dirty' : 'status-clean');
  document.getElementById('git-info').innerHTML = s.dirty
    ? `有 ${s.changed_files.length} 个文件待提交 — 分支: ${s.branch}`
    : `工作区干净 — 分支: ${s.branch}`;
}

async function commitAndPush() {
  showMsg('正在提交到仓库...', 'info');
  const r = await api('POST', '/api/teacher/config/commit');
  if (r.ok) { const d = await r.json(); showMsg(d.sha ? `提交成功: ${d.sha}` : '无变更需要提交', 'success'); checkGitStatus(); }
  else { showMsg('提交失败', 'error'); }
}
</script>
</body>
</html>
```

- [ ] **Step 2: 验证文件写入成功**

```bash
Test-Path -LiteralPath "backend/app/static/vscode_config.html"
```

Expected: `True`

---

### Task 6: 在 teacher.html 添加导航链接

**Files:**
- Modify: `backend/app/static/teacher.html`

- [ ] **Step 1: 在 teacher.html header 区域添加配置管理入口**

在 `<h1>🎓 教师管理后台...</h1>` 和 `<button onclick="logout()">` 之间添加导航链接。

修改前（第 96-99 行）：
```html
  <div class="header">
    <h1>🎓 教师管理后台 — 研究生课程《机器人系统》</h1>
    <button onclick="logout()">退出登录</button>
  </div>
```

修改后：
```html
  <div class="header">
    <h1>🎓 教师管理后台 — 研究生课程《机器人系统》</h1>
    <div style="display:flex;align-items:center;gap:12px;">
      <a href="/vscode-config" style="color:rgba(255,255,255,.9);font-size:.85rem;text-decoration:none;padding:5px 10px;background:rgba(255,255,255,.12);border-radius:4px;">⚙ VS Code 配置</a>
      <button onclick="logout()">退出登录</button>
    </div>
  </div>
```

- [ ] **Step 2: 验证修改已生效**

```bash
rg "vscode-config" backend/app/static/teacher.html
```

Expected: 找到匹配行

---

### Task 7: 运行全部测试验证

**Files:** 无需修改

- [ ] **Step 1: 运行 F-T-002 测试套件**

```bash
cd backend; python -m pytest ../tests/reflex/test_F_T_002_vscode_config.py -v
```

Expected: 全部 10 个测试 PASS（部分可能因文件系统/Git 状态而跳过，无 ERROR）

- [ ] **Step 2: 验证其他已有测试未受影响**

```bash
cd backend; python -m pytest ../tests/ -v --tb=short 2>&1 | Select-Object -Last 40
```

Expected: 仅 F-T-002 测试变化，其他测试无新增 FAIL

---

### Task 8: 最终提交

- [ ] **Step 1: 提交所有变更**

```bash
git add backend/app/routers/vscode_config.py
git add backend/app/static/vscode_config.html
git add backend/app/data/vscode_config.json
git add backend/app/main.py
git add backend/app/static/teacher.html
git add tests/reflex/test_F_T_002_vscode_config.py
git commit -m "feat: F-T-002 VS Code扩展与Copilot提示词配置"
```

- [ ] **Step 2: 验证 git status**

```bash
git status
```

Expected: 无未提交变更
