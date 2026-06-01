from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, field_validator
import json
from app.auth_utils import verify_teacher_token
from app.github_client import push_files, check_token, file_exists
from app.mysql_db import mysql_db, COMMITLINT_COURSE_ID, COMMITLINT_UPDATED_BY
from app.failures_store import get_failures, add_failure
from oaepp.states.commitlint_engine import build_commitlintrc, generate_workflow_yml

router = APIRouter()


def ensure_mysql_row():
    """确保 commitlint_configs 表中存在当前 course_id 的配置行，不存在则自动创建。"""
    try:
        with mysql_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM commitlint_configs WHERE course_id=%s",
                    (COMMITLINT_COURSE_ID,)
                )
                if cur.fetchone():
                    return
                cur.execute("SET foreign_key_checks=0")
                cur.execute(
                    """INSERT INTO commitlint_configs
                       (course_id, rule_set, header_max_len, subject_min_len,
                        type_enum_json, enabled, config_version, updated_by)
                       VALUES (%s, 'conventional', 100, 5,
                        '["feat","fix","refactor","style","test","docs","chore"]', 1, 1, %s)""",
                    (COMMITLINT_COURSE_ID, COMMITLINT_UPDATED_BY)
                )
                conn.commit()
                cur.execute("SET foreign_key_checks=1")
                print(f"[commitlint] 已自动创建默认配置行 (course_id={COMMITLINT_COURSE_ID})")
    except Exception as e:
        print(f"[commitlint] 初始化 MySQL 配置行失败: {e}")


ensure_mysql_row()


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ─── 列名映射：前端字段名 → MySQL 列名 ──────────────────────────────────────

_FRONTEND_TO_MYSQL = {
    "rule_type": "rule_set",
    "type_enum": "type_enum_json",
    "header_max_length": "header_max_len",
    "subject_min_length": "subject_min_len",
    "rule_version": "config_version",
    "enabled": "enabled",
}

_MYSQL_TO_FRONTEND = {v: k for k, v in _FRONTEND_TO_MYSQL.items()}


def _row_to_frontend(row: dict) -> dict:
    """将 MySQL 行数据转换为前端 API 的一致字段名"""
    result = {}
    for mysql_col, value in row.items():
        frontend_col = _MYSQL_TO_FRONTEND.get(mysql_col, mysql_col)
        result[frontend_col] = value
    # 解析 JSON 字段
    if result.get("type_enum") and isinstance(result["type_enum"], str):
        try:
            result["type_enum"] = json.loads(result["type_enum"])
        except (json.JSONDecodeError, TypeError):
            result["type_enum"] = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]
    return result


def _frontend_to_mysql_for_update(data: dict) -> tuple[list[str], list]:
    """将前端字段映射回 MySQL 列名，返回 (fields_list, values_list) 用于 UPDATE"""
    mapping = {
        "enabled": ("enabled", lambda v: 1 if v else 0),
        "rule_type": ("rule_set", lambda v: v),
        "type_enum": ("type_enum_json", lambda v: json.dumps(v, ensure_ascii=False)),
        "header_max_length": ("header_max_len", lambda v: v),
        "subject_min_length": ("subject_min_len", lambda v: v),
    }
    fields = []
    values = []
    for frontend_key, (mysql_col, transform) in mapping.items():
        if frontend_key in data:
            fields.append(f"{mysql_col}=%s")
            values.append(transform(data[frontend_key]))
    return fields, values


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
    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="配置不存在")
    return _row_to_frontend(row)


# ─── 更新配置 ────────────────────────────────────────────────────────────────

@router.put("/api/teacher/commitlint/config")
def update_commitlint_config(
    req: CommitlintConfigUpdate,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    update_data = req.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail="未提供任何需要更新的字段")

    fields, values = _frontend_to_mysql_for_update(update_data)
    fields.append("config_version=config_version+1")
    fields.append("updated_by=%s")
    values.append(COMMITLINT_UPDATED_BY)

    values.append(COMMITLINT_COURSE_ID)

    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE commitlint_configs SET {', '.join(fields)} WHERE course_id=%s",
                values
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="配置记录不存在，请联系管理员初始化")
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            row = cur.fetchone()

    return _row_to_frontend(row)


# ─── 启用/禁用切换 ───────────────────────────────────────────────────────────

@router.post("/api/teacher/commitlint/toggle")
def toggle_commitlint(
    req: ToggleRequest,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    enabled_int = 1 if req.enabled else 0
    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE commitlint_configs SET enabled=%s, updated_by=%s WHERE course_id=%s",
                (enabled_int, COMMITLINT_UPDATED_BY, COMMITLINT_COURSE_ID)
            )
            cur.execute(
                "SELECT enabled FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            row = cur.fetchone()
    return {"enabled": bool(row["enabled"])}


# ─── 获取状态总览 ────────────────────────────────────────────────────────────

@router.get("/api/teacher/commitlint/status")
def get_commitlint_status(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            config = cur.fetchone()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    result = _row_to_frontend(config)
    result["recent_failures"] = get_failures()
    return result


# ─── 获取最近校验失败记录 ────────────────────────────────────────────────────

@router.get("/api/teacher/commitlint/failures")
def get_commitlint_failures(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return get_failures()


# ─── 生成 CI 配置文件内容（CI 联动：根据 enabled 状态决定规则级别）────────────

def _load_config(row: dict) -> dict:
    """将 MySQL 行转换为 build_commitlintrc 可接受的字典"""
    type_enum = row.get("type_enum_json") or row.get("type_enum")
    if isinstance(type_enum, str):
        try:
            type_enum = json.loads(type_enum)
        except (json.JSONDecodeError, TypeError):
            type_enum = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]
    return {
        "type_enum": type_enum,
        "header_max_length": row["header_max_len"],
        "subject_min_length": row["subject_min_len"],
        "is_enabled": bool(row["enabled"]),
    }


@router.post("/api/teacher/commitlint/generate")
def generate_commitlint_config(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            config = cur.fetchone()
    if not config:
        raise HTTPException(status_code=404, detail="请先保存配置")

    cfg = _load_config(config)
    commitlintrc = build_commitlintrc(**cfg)
    workflow_yml = generate_workflow_yml()

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
    _require_teacher(authorization)

    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            config = cur.fetchone()
    if not config:
        raise HTTPException(status_code=404, detail="请先保存配置")

    cfg = _load_config(config)
    commitlintrc = build_commitlintrc(**cfg)
    workflow_yml = generate_workflow_yml()

    is_enabled = bool(config["enabled"])
    status_label = "启用" if is_enabled else "停用"
    version = config["config_version"]

    files = [
        {"path": ".github/workflows/commitlint.yml", "content": workflow_yml},
        {"path": ".commitlintrc.json", "content": commitlintrc},
    ]

    commit_message = (
        f"chore(commitlint): {status_label}配置 v{version}\n\n"
        f"由 OA-EPP 平台自动提交。\n"
        f"规则版本: v{version}\n"
        f"规则集: {config['rule_set']}\n"
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
        "version": str(version),
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
    _require_teacher(authorization)

    with mysql_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE commitlint_configs SET"
                " rule_set=%s, type_enum_json=%s,"
                " header_max_len=%s, subject_min_len=%s,"
                " config_version=config_version+1, updated_by=%s"
                " WHERE course_id=%s",
                (
                    req.rule_type,
                    json.dumps(req.type_enum, ensure_ascii=False),
                    req.header_max_length,
                    req.subject_min_length,
                    COMMITLINT_UPDATED_BY,
                    COMMITLINT_COURSE_ID,
                )
            )
            cur.execute(
                "SELECT * FROM commitlint_configs WHERE course_id=%s",
                (COMMITLINT_COURSE_ID,)
            )
            config = cur.fetchone()

    if not config:
        raise HTTPException(status_code=404, detail="配置记录不存在")

    is_enabled = bool(config["enabled"])
    cfg = _load_config(config)
    commitlintrc = build_commitlintrc(**cfg)
    workflow_yml = generate_workflow_yml()

    files = [
        {"path": ".github/workflows/commitlint.yml", "content": workflow_yml},
        {"path": ".commitlintrc.json", "content": commitlintrc},
    ]

    new_version = config["config_version"]
    status_label = "启用" if is_enabled else "停用"
    commit_message = (
        f"chore(commitlint): {status_label}配置 v{new_version}\n\n"
        f"由 OA-EPP 平台自动提交。\n"
        f"规则版本: v{new_version}\n"
        f"规则集: {req.rule_type}\n"
        f"启用状态: {status_label}\n"
    )

    try:
        push_result = push_files(files, commit_message.strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"提交至仓库失败: {e}")

    result = _row_to_frontend(config)
    result["commit_sha"] = push_result["commit_sha"]
    result["commit_url"] = push_result["commit_url"]
    result["git_history_url"] = (
        f"https://github.com/uwislab/robotics-systems-course/"
        f"commits/main/.commitlintrc.json"
    )

    return result


# ─── 检查仓库中配置文件的同步状态 ─────────────────────────────────────────

@router.get("/api/teacher/commitlint/repo-status")
def check_repo_status(authorization: Optional[str] = Header(None)):
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
