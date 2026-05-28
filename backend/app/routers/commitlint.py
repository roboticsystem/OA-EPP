from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, field_validator
import json
from app.database import db
from app.auth_utils import verify_teacher_token

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


# ─── 生成 CI 配置文件内容 ────────────────────────────────────────────────────

_COMMITLINT_YML = """name: Commit Message 检查

on: [pull_request]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@v5
        with:
          configFile: .commitlintrc.json
"""


def _build_commitlintrc(config: dict) -> str:
    type_enum = config["type_enum"]
    if isinstance(type_enum, str):
        try:
            type_enum = json.loads(type_enum)
        except json.JSONDecodeError:
            type_enum = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]

    rules = {
        "type-enum": [2, "always", type_enum],
        "subject-min-length": [2, "always", config["subject_min_length"]],
        "header-max-length": [2, "always", config["header_max_length"]]
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

    workflow_yml = _COMMITLINT_YML
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
