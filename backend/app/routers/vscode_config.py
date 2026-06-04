import os
import json
import subprocess
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List

from app.routers.teacher import _require_teacher

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "vscode_config.json")
REPO_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

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
                       cwd=REPO_ROOT, capture_output=True)

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
            subprocess.run(
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
