from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, field_validator
import json
from app.database import db
from app.auth_utils import verify_teacher_token
from app.github_client import push_files, check_token, get_repo_file_content, file_exists

router = APIRouter()


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _bump_version(current: str) -> str:
    parts = current.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except (IndexError, ValueError):
        return "1.0.0"
    return ".".join(parts)


# ─── 请求/响应模型 ───────────────────────────────────────────────────────────

class CommitlintConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    rule_type: Optional[str] = None
    type_enum: Optional[list[str]] = None
    header_max_length: Optional[int] = None
    subject_min_length: Optional[int] = None

    @field_validator("header_max_length", "subject_min_length")
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("必须为正整数")
        return v

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        if v is not None and v not in ("conventional", "custom"):
            raise ValueError('rule_type 必须为 "conventional" 或 "custom"')
        return v

    @field_validator("type_enum")
    @classmethod
    def validate_type_enum(cls, v):
        if v is not None and not v:
            raise ValueError("type_enum 不能为空列表")
        return v


class ToggleRequest(BaseModel):
    enabled: bool


# ─── 获取当前配置 ────────────────────────────────────────────────────────────

@router.get("/api/teacher/commitlint/config")
def get_commitlint_config(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        row = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="配置不存在")
    result = dict(row)
    try:
        result["type_enum"] = json.loads(result["type_enum"])
    except (json.JSONDecodeError, TypeError):
        pass
    return result


# ─── 更新配置 ────────────────────────────────────────────────────────────────

@router.put("/api/teacher/commitlint/config")
def update_commitlint_config(
    req: CommitlintConfigUpdate,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    fields = []
    values = []

    if req.enabled is not None:
        fields.append("enabled=?")
        values.append(1 if req.enabled else 0)
    if req.rule_type is not None:
        fields.append("rule_type=?")
        values.append(req.rule_type)
    if req.type_enum is not None:
        fields.append("type_enum=?")
        values.append(json.dumps(req.type_enum, ensure_ascii=False))
    if req.header_max_length is not None:
        fields.append("header_max_length=?")
        values.append(req.header_max_length)
    if req.subject_min_length is not None:
        fields.append("subject_min_length=?")
        values.append(req.subject_min_length)

    if not fields:
        raise HTTPException(status_code=422, detail="未提供任何需要更新的字段")

    with db() as conn:
        old = conn.execute("SELECT rule_version FROM commitlint_config WHERE id=1").fetchone()
        new_version = _bump_version(old["rule_version"]) if old else "1.0.0"
        fields.append("rule_version=?")
        values.append(new_version)
        fields.append("updated_at=datetime('now','localtime')")

        conn.execute(
            f"UPDATE commitlint_config SET {', '.join(fields)} WHERE id=1",
            values
        )
        row = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()

    result = dict(row)
    try:
        result["type_enum"] = json.loads(result["type_enum"])
    except (json.JSONDecodeError, TypeError):
        pass
    return result


# ─── 启用/禁用切换 ───────────────────────────────────────────────────────────

@router.post("/api/teacher/commitlint/toggle")
def toggle_commitlint(
    req: ToggleRequest,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    with db() as conn:
        conn.execute(
            "UPDATE commitlint_config SET enabled=?, rule_version=rule_version, updated_at=datetime('now','localtime') WHERE id=1",
            (1 if req.enabled else 0,)
        )
        row = conn.execute("SELECT enabled FROM commitlint_config WHERE id=1").fetchone()
    return {"enabled": bool(row["enabled"])}


# ─── 获取状态总览 ────────────────────────────────────────────────────────────

@router.get("/api/teacher/commitlint/status")
def get_commitlint_status(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        config = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()
        failures = conn.execute(
            "SELECT * FROM commitlint_failures ORDER BY failed_at DESC LIMIT 5"
        ).fetchall()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    result = dict(config)
    try:
        result["type_enum"] = json.loads(result["type_enum"])
    except (json.JSONDecodeError, TypeError):
        pass
    result["recent_failures"] = [dict(f) for f in failures]
    return result


# ─── 获取最近校验失败记录 ────────────────────────────────────────────────────

@router.get("/api/teacher/commitlint/failures")
def get_commitlint_failures(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM commitlint_failures ORDER BY failed_at DESC LIMIT 5"
        ).fetchall()
    return [dict(r) for r in rows]


# ─── 生成 CI 配置文件内容（CI 联动：根据 enabled 状态决定规则级别）────────────

def _build_commitlintrc(config: dict, force_enabled: Optional[bool] = None) -> str:
    is_enabled = force_enabled if force_enabled is not None else (config["enabled"] in (1, True))
    type_enum = config["type_enum"]
    if isinstance(type_enum, str):
        try:
            type_enum = json.loads(type_enum)
        except json.JSONDecodeError:
            type_enum = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]

    # 规则级别：enabled=2(error 导致CI失败), disabled=0(关闭)
    level = 2 if is_enabled else 0

    rules = {
        "type-enum": [level, "always", type_enum],
        "subject-min-length": [level, "always", config["subject_min_length"]],
        "header-max-length": [level, "always", config["header_max_length"]]
    }

    rc = {
        "extends": ["@commitlint/config-conventional"],
        "rules": rules
    }
    return json.dumps(rc, indent=2, ensure_ascii=False)


@router.post("/api/teacher/commitlint/generate")
def generate_commitlint_config(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        config = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()
    if not config:
        raise HTTPException(status_code=404, detail="请先保存配置")

    workflow_yml = "name: Commit Message 检查\n\non: [pull_request]\n\njobs:\n  commitlint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n      - uses: wagoid/commitlint-github-action@v5\n        with:\n          configFile: .commitlintrc.json\n"
    commitlintrc = _build_commitlintrc(config)

    return {
        "workflow": {
            "path": ".github/workflows/commitlint.yml",
            "content": workflow_yml
        },
        "commitlintrc": {
            "path": ".commitlintrc.json",
            "content": commitlintrc
        },
        "files": [
            {"path": ".github/workflows/commitlint.yml", "content": workflow_yml},
            {"path": ".commitlintrc.json", "content": commitlintrc}
        ]
    }


# ─── 一键提交至仓库（Git 版本控制）──────────────────────────────────────────

@router.post("/api/teacher/commitlint/push")
def push_commitlint_config(authorization: Optional[str] = Header(None)):
    """
    将当前 commitlint 配置生成的文件一键提交至 GitHub 仓库，
    纳入 Git 版本控制，自动触发 CI。
    """
    _require_teacher(authorization)

    with db() as conn:
        config = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()
    if not config:
        raise HTTPException(status_code=404, detail="请先保存配置")

    workflow_yml = "name: Commit Message 检查\n\non: [pull_request]\n\njobs:\n  commitlint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n      - uses: wagoid/commitlint-github-action@v5\n        with:\n          configFile: .commitlintrc.json\n"
    commitlintrc = _build_commitlintrc(config)

    is_enabled = config["enabled"] in (1, True)
    status_label = "启用" if is_enabled else "停用"
    version = config["rule_version"]

    files = [
        {"path": ".github/workflows/commitlint.yml", "content": workflow_yml},
        {"path": ".commitlintrc.json", "content": commitlintrc},
    ]

    commit_message = (
        f"chore(commitlint): {status_label}配置 v{version}\n\n"
        f"由 OA-EPP 平台自动提交。\n"
        f"规则版本: v{version}\n"
        f"规则类型: {config['rule_type']}\n"
        f"启用状态: {status_label}\n"
    )

    try:
        result = push_files(files, commit_message.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"提交至仓库失败: {e}")

    return {
        "ok": True,
        "commit_sha": result["commit_sha"],
        "commit_url": result["commit_url"],
        "version": version,
        "enabled": is_enabled,
        "files": [
            {"path": ".github/workflows/commitlint.yml", "status": "已提交"},
            {"path": ".commitlintrc.json", "status": "已提交"},
        ],
    }


# ─── 保存配置并自动提交至仓库 ──────────────────────────────────────────────

class SaveAndPushRequest(BaseModel):
    rule_type: str = "conventional"
    type_enum: list[str] = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]
    header_max_length: int = 100
    subject_min_length: int = 5


@router.post("/api/teacher/commitlint/save-and-push")
def save_and_push_commitlint(
    req: SaveAndPushRequest,
    authorization: Optional[str] = Header(None)
):
    """
    保存配置到数据库，自动升级版本号，并将配置文件一键提交至 GitHub 仓库。
    提交后自动触发 CI，版本变更纳入 Git 历史可回溯。
    """
    _require_teacher(authorization)

    with db() as conn:
        old = conn.execute("SELECT rule_version, enabled FROM commitlint_config WHERE id=1").fetchone()
        new_version = _bump_version(old["rule_version"]) if old else "1.0.0"
        old_enabled = old["enabled"] in (1, True) if old else True

        conn.execute(
            """UPDATE commitlint_config SET
                rule_type=?, type_enum=?, header_max_length=?,
                subject_min_length=?, rule_version=?,
                updated_at=datetime('now','localtime')
               WHERE id=1""",
            (
                req.rule_type,
                json.dumps(req.type_enum, ensure_ascii=False),
                req.header_max_length,
                req.subject_min_length,
                new_version,
            ),
        )
        config = conn.execute("SELECT * FROM commitlint_config WHERE id=1").fetchone()

    is_enabled = config["enabled"] in (1, True)
    commitlintrc = _build_commitlintrc(config, force_enabled=is_enabled)
    workflow_yml = "name: Commit Message 检查\n\non: [pull_request]\n\njobs:\n  commitlint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n      - uses: wagoid/commitlint-github-action@v5\n        with:\n          configFile: .commitlintrc.json\n"

    files = [
        {"path": ".github/workflows/commitlint.yml", "content": workflow_yml},
        {"path": ".commitlintrc.json", "content": commitlintrc},
    ]

    status_label = "启用" if is_enabled else "停用"
    commit_message = (
        f"chore(commitlint): {status_label}配置 v{new_version}\n\n"
        f"由 OA-EPP 平台自动提交。\n"
        f"规则版本: v{new_version}\n"
        f"规则类型: {req.rule_type}\n"
        f"启用状态: {status_label}\n"
    )

    try:
        push_result = push_files(files, commit_message.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"提交至仓库失败: {e}")

    result = dict(config)
    try:
        result["type_enum"] = json.loads(result["type_enum"])
    except (json.JSONDecodeError, TypeError):
        pass
    result["commit_sha"] = push_result["commit_sha"]
    result["commit_url"] = push_result["commit_url"]
    result["git_history_url"] = f"https://github.com/uwislab/robotics-systems-course/commits/main/.commitlintrc.json"

    return result


# ─── 检查仓库中配置文件的同步状态 ─────────────────────────────────────────

@router.get("/api/teacher/commitlint/repo-status")
def check_repo_status(authorization: Optional[str] = Header(None)):
    """检查 GitHub Token 有效性及仓库中 commitlint 配置文件是否存在。"""
    _require_teacher(authorization)

    token_ok = check_token()

    if not token_ok.get("ok"):
        return {
            "token_ok": False,
            "error": token_ok.get("error", "GitHub Token 未配置"),
            "workflow_in_repo": None,
            "commitlintrc_in_repo": None,
        }

    try:
        workflow_exists = file_exists(".github/workflows/commitlint.yml")
        commitlintrc_exists = file_exists(".commitlintrc.json")
    except Exception:
        workflow_exists = None
        commitlintrc_exists = None

    return {
        "token_ok": True,
        "repo_full_name": token_ok.get("full_name"),
        "repo_url": token_ok.get("html_url"),
        "default_branch": token_ok.get("default_branch"),
        "workflow_in_repo": workflow_exists,
        "commitlintrc_in_repo": commitlintrc_exists,
    }
