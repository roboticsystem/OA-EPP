"""F-D-009 Commitlint 配置状态管理 — CommitlintState

教师可通过该 State 在 Reflex 页面上完成：
- 配置规则集（Conventional Commits / 自定义）及参数编辑
- 生成 .commitlintrc.json 和 commitlint.yml
- 通过 GitHub Contents API 推送至仓库
- CI 联动控制（启用=error / 停用=0）
- 查看启用状态、规则版本、最近 5 次校验失败记录

依赖：
  - oaepp.database.transaction_sync — MySQL 数据库访问
  - oaepp.states.commitlint_engine — 配置文件生成引擎
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

import reflex as rx

from oaepp.states.commitlint_engine import build_commitlintrc, generate_workflow_yml

# ── 常量 ────────────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "uwislab/robotics-systems-course")
GIT_BRANCH = os.environ.get("GIT_BRANCH", "F-D-009]-Commit-消息格式自动校验")
_API_BASE = "https://api.github.com"

# 失败记录本地存储
_FAILURES_FILE = Path(
    os.environ.get(
        "FAILURES_FILE",
        str(Path(__file__).resolve().parent.parent.parent / ".local_exam_data" / "commitlint_failures.json"),
    )
)
_MAX_FAILURES = 5

# 列名映射：前端字段名 ↔ MySQL 列名
_FRONTEND_TO_MYSQL = {
    "rule_type": "rule_set",
    "type_enum": "type_enum_json",
    "header_max_length": "header_max_len",
    "subject_min_length": "subject_min_len",
    "rule_version": "config_version",
    "enabled": "enabled",
}
_MYSQL_TO_FRONTEND = {v: k for k, v in _FRONTEND_TO_MYSQL.items()}


def _mysql_row_to_frontend(row: dict) -> dict:
    """MySQL 行数据 → 前端字段名"""
    result = {}
    for mysql_col, value in row.items():
        frontend_col = _MYSQL_TO_FRONTEND.get(mysql_col, mysql_col)
        result[frontend_col] = value
    if result.get("type_enum") and isinstance(result["type_enum"], str):
        try:
            result["type_enum"] = json.loads(result["type_enum"])
        except (json.JSONDecodeError, TypeError):
            result["type_enum"] = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]
    return result


def _github_headers() -> dict:
    """GitHub API 请求头"""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN 未配置")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OA-EPP-commitlint/1.0",
    }


def _github_request(method: str, url: str, data: Optional[dict] = None) -> dict:
    """发送 GitHub API 请求"""
    headers = _github_headers()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(f"GitHub API {method} {url} 失败 (HTTP {e.code}): {detail}")


def _api_url(path: str) -> str:
    return f"{_API_BASE}/repos/{GITHUB_REPO}{path}"


def _get_file_sha(path: str, branch: str) -> Optional[str]:
    """获取仓库中指定文件的 SHA（用于更新时传参）"""
    try:
        resp = _github_request("GET", _api_url(f"/contents/{path}?ref={branch}"))
        return resp.get("sha")
    except RuntimeError:
        return None


def _push_files(files: list[dict], commit_message: str, branch: str) -> dict:
    """通过 Contents API 推送文件到仓库"""
    last_sha = None
    for f in files:
        data = {
            "message": commit_message,
            "content": base64.b64encode(f["content"].encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        sha = _get_file_sha(f["path"], branch)
        if sha:
            data["sha"] = sha
        resp = _github_request("PUT", _api_url(f"/contents/{f['path']}"), data)
        last_sha = resp["commit"]["sha"]
    commit_url = f"https://github.com/{GITHUB_REPO}/commit/{last_sha}"
    return {"commit_sha": last_sha, "commit_url": commit_url}


def _list_branches() -> list[dict]:
    """获取仓库分支列表"""
    try:
        repo = _github_request("GET", _api_url(""))
        default = repo.get("default_branch", "main")
        resp = _github_request("GET", _api_url("/branches?per_page=100"))
        return [{"name": b["name"], "default": b["name"] == default} for b in resp]
    except RuntimeError:
        return []


def _check_token() -> dict:
    """验证 GitHub Token 有效性"""
    try:
        repo = _github_request("GET", _api_url(""))
        return {
            "ok": True,
            "full_name": repo.get("full_name", GITHUB_REPO),
            "html_url": repo.get("html_url", ""),
            "default_branch": repo.get("default_branch", "main"),
        }
    except (ValueError, RuntimeError) as e:
        return {"ok": False, "error": str(e)}


def _file_exists(path: str, branch: str) -> bool:
    """检查仓库中文件是否存在"""
    try:
        _github_request("GET", _api_url(f"/contents/{path}?ref={branch}"))
        return True
    except RuntimeError:
        return False


# ── 失败记录存储 ────────────────────────────────────────────

def _ensure_failures_file():
    _FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _FAILURES_FILE.exists():
        _FAILURES_FILE.write_text("[]", encoding="utf-8")


def _get_failures() -> list:
    _ensure_failures_file()
    try:
        data = json.loads(_FAILURES_FILE.read_text(encoding="utf-8"))
        return data[:_MAX_FAILURES]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _add_failure(commit_sha: str, commit_msg: str, author: str = "",
                 branch: str = "", pr_number: int = 0, error_msg: str = ""):
    _ensure_failures_file()
    records = _get_failures()
    records.insert(0, {
        "id": len(records) + 1,
        "commit_sha": commit_sha,
        "commit_msg": commit_msg,
        "author": author,
        "branch": branch,
        "pr_number": pr_number,
        "failed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error_msg": error_msg,
    })
    _FAILURES_FILE.write_text(
        json.dumps(records[:_MAX_FAILURES], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── CommitlintState ─────────────────────────────────────────

class CommitlintState(rx.State):
    """Commitlint 配置状态管理

    TDD 测试要求（tests/reflex/test_F_D_009_commitlint.py）：
      - rule_set / is_enabled / recent_failures 属性存在
      - save_config() 方法存在
      - type_enum 枚举定义
      - header_max_length 长度限制
      - recent_failures 列表 + MAX_FAILURES 容量限制
    """

    # ── 配置属性 ──
    rule_set: str = "conventional"
    is_enabled: bool = True
    type_enum: list[str] = [
        "feat", "fix", "refactor", "style", "test", "docs", "chore",
    ]
    header_max_length: int = 100
    subject_min_length: int = 5
    config_version: str = "1"

    # ── 状态 UI 属性 ──
    recent_failures: list[dict] = []
    branches: list[dict] = []
    default_branch: str = ""
    selected_branch: str = ""

    repo_status: dict = {}
    preview_workflow: str = ""
    preview_commitlintrc: str = ""
    push_result: dict = {}

    toast_message: str = ""
    toast_type: str = "info"  # info | success | error

    loading_failures: bool = False

    MAX_FAILURES: int = _MAX_FAILURES
    """TDD TC05：容量常量"""

    # ── 内部方法 ──

    def _load_config_from_db(self) -> Optional[dict]:
        """从 MySQL 加载配置行，返回前端字段名的 dict"""
        from oaepp.database import transaction_sync
        try:
            with transaction_sync() as cur:
                cur.execute(
                    "SELECT * FROM commitlint_configs WHERE course_id=1"
                )
                row = cur.fetchone()
        except Exception:
            row = None
        if not row:
            return None
        return _mysql_row_to_frontend(dict(row))

    def _ensure_config_in_db(self):
        """确保 MySQL 中有默认配置行"""
        from oaepp.database import transaction_sync
        try:
            with transaction_sync() as cur:
                cur.execute("SELECT id FROM commitlint_configs WHERE course_id=1")
                if cur.fetchone():
                    return
                cur.execute("SET foreign_key_checks=0")
                cur.execute(
                    """INSERT INTO commitlint_configs
                       (course_id, rule_set, header_max_len, subject_min_len,
                        type_enum_json, enabled, config_version, updated_by)
                       VALUES (1, 'conventional', 100, 5,
                        '["feat","fix","refactor","style","test","docs","chore"]', 1, 1, 1)"""
                )
                cur.execute("SET foreign_key_checks=1")
        except Exception:
            pass

    def _show_toast(self, msg: str, typ: str = "info"):
        self.toast_message = msg
        self.toast_type = typ

    # ── 事件处理器 ──

    def load_config(self):
        """从 MySQL 加载配置到 State 属性"""
        self._ensure_config_in_db()
        cfg = self._load_config_from_db()
        if cfg:
            self.rule_set = cfg.get("rule_type", "conventional")
            self.is_enabled = bool(cfg.get("enabled", True))
            self.header_max_length = cfg.get("header_max_length", 100)
            self.subject_min_length = cfg.get("subject_min_length", 5)
            self.type_enum = cfg.get("type_enum", [])
            self.config_version = str(cfg.get("rule_version", "1"))
        self.recent_failures = _get_failures()
        self.selected_branch = self.selected_branch or GIT_BRANCH

    def load_branches(self):
        """加载 GitHub 分支列表"""
        try:
            branches = _list_branches()
            self.branches = branches
            if branches:
                default = next((b["name"] for b in branches if b["default"]), GIT_BRANCH)
                self.default_branch = default
                if not self.selected_branch:
                    self.selected_branch = default
        except Exception:
            self.branches = []

    def set_branch(self, branch: str):
        self.selected_branch = branch

    def toggle_enabled(self):
        """切换启用/停用状态并保存到数据库"""
        self.is_enabled = not self.is_enabled
        enabled_int = 1 if self.is_enabled else 0
        from oaepp.database import transaction_sync
        try:
            with transaction_sync() as cur:
                cur.execute(
                    "UPDATE commitlint_configs SET enabled=%s, updated_by=1 WHERE course_id=1",
                    (enabled_int,),
                )
            self._show_toast(
                f"Commitlint 已{'启用' if self.is_enabled else '停用'}",
                "success",
            )
        except Exception as e:
            self._show_toast(f"操作失败: {e}", "error")

    def update_config(self, form_data: dict):
        """保存配置到 MySQL"""
        from oaepp.database import transaction_sync
        try:
            with transaction_sync() as cur:
                cur.execute(
                    """UPDATE commitlint_configs SET
                       rule_set=%s, type_enum_json=%s,
                       header_max_len=%s, subject_min_len=%s,
                       config_version=config_version+1, updated_by=1
                       WHERE course_id=1""",
                    (
                        form_data.get("rule_type", self.rule_set),
                        json.dumps(form_data.get("type_enum", self.type_enum), ensure_ascii=False),
                        form_data.get("header_max_length", self.header_max_length),
                        form_data.get("subject_min_length", self.subject_min_length),
                    ),
                )
            # 重新加载配置
            self.load_config()
            self._show_toast(f"✅ 配置已保存，版本 v{self.config_version}", "success")
        except Exception as e:
            self._show_toast(f"保存失败: {e}", "error")

    def generate_config_preview(self):
        """生成配置文件预览（不推送）"""
        cfg = self._load_config_from_db()
        if not cfg:
            self._show_toast("请先保存配置", "error")
            return
        commitlintrc = build_commitlintrc(
            type_enum=self.type_enum,
            header_max_length=self.header_max_length,
            subject_min_length=self.subject_min_length,
            is_enabled=self.is_enabled,
        )
        workflow = generate_workflow_yml()
        self.preview_commitlintrc = commitlintrc
        self.preview_workflow = workflow
        self._show_toast("✅ 配置文件已生成", "success")

    def push_config(self):
        """推送配置文件到 GitHub 仓库"""
        target_branch = self.selected_branch or GIT_BRANCH
        try:
            commitlintrc = build_commitlintrc(
                type_enum=self.type_enum,
                header_max_length=self.header_max_length,
                subject_min_length=self.subject_min_length,
                is_enabled=self.is_enabled,
            )
            workflow = generate_workflow_yml()
            files = [
                {"path": ".github/workflows/commitlint.yml", "content": workflow},
                {"path": ".commitlintrc.json", "content": commitlintrc},
            ]
            status_label = "启用" if self.is_enabled else "停用"
            commit_msg = (
                f"chore(commitlint): {status_label}配置 v{self.config_version}\n\n"
                f"由 OA-EPP 平台自动提交。\n"
                f"规则版本: v{self.config_version}\n"
                f"规则集: {self.rule_set}\n"
                f"启用状态: {status_label}\n"
            )
            result = _push_files(files, commit_msg.strip(), target_branch)
            self.push_result = {
                "commit_sha": result["commit_sha"],
                "commit_url": result["commit_url"],
                "git_history_url": (
                    f"https://github.com/{GITHUB_REPO}/commits/{target_branch}/.commitlintrc.json"
                ),
            }
            self._show_toast(
                f"✅ 已提交至仓库，commit: {result['commit_sha'][:7]}",
                "success",
            )
        except Exception as e:
            self._show_toast(f"提交至仓库失败: {e}", "error")

    def check_repo_status(self):
        """检查仓库和 GitHub Token 状态"""
        try:
            token_info = _check_token()
            if not token_info.get("ok"):
                self.repo_status = {
                    "token_ok": False,
                    "error": token_info.get("error", "GitHub Token 未配置"),
                }
                return
            target_branch = self.selected_branch or GIT_BRANCH
            wf_exists = _file_exists(".github/workflows/commitlint.yml", target_branch)
            rc_exists = _file_exists(".commitlintrc.json", target_branch)
            self.repo_status = {
                "token_ok": True,
                "full_name": token_info.get("full_name"),
                "repo_url": token_info.get("html_url"),
                "default_branch": token_info.get("default_branch"),
                "workflow_in_repo": wf_exists,
                "commitlintrc_in_repo": rc_exists,
            }
        except Exception as e:
            self.repo_status = {"token_ok": False, "error": str(e)}

    def set_rule_set(self, value: str):
        self.rule_set = value

    def set_header_max_length(self, value: int):
        self.header_max_length = value

    def set_subject_min_length(self, value: int):
        self.subject_min_length = value

    def add_type(self, key: str):
        """键盘事件：暂不处理，简化版用 input 配合按钮"""
        pass

    def save_config_to_db(self):
        """从当前 State 属性保存配置到 MySQL"""
        from oaepp.database import transaction_sync
        try:
            with transaction_sync() as cur:
                cur.execute(
                    """UPDATE commitlint_configs SET
                       rule_set=%s, type_enum_json=%s,
                       header_max_len=%s, subject_min_len=%s,
                       config_version=config_version+1, updated_by=1
                       WHERE course_id=1""",
                    (
                        self.rule_set,
                        json.dumps(self.type_enum, ensure_ascii=False),
                        self.header_max_length,
                        self.subject_min_length,
                    ),
                )
            self.load_config()
            self._show_toast(f"✅ 配置已保存，版本 v{self.config_version}", "success")
        except Exception as e:
            self._show_toast(f"保存失败: {e}", "error")

    def save_and_push(self):
        """保存配置到 MySQL 并推送到 GitHub"""
        self.save_config_to_db()
        self.push_config()

    def save_config(self) -> dict:
        """生成配置文件内容（TDD 测试用）"""
        rc = build_commitlintrc(
            type_enum=self.type_enum,
            header_max_length=self.header_max_length,
            subject_min_length=self.subject_min_length,
            is_enabled=self.is_enabled,
        )
        workflow = generate_workflow_yml()
        return {
            "commitlintrc": {"path": ".commitlintrc.json", "content": rc},
            "workflow": {"path": ".github/workflows/commitlint.yml", "content": workflow},
        }
