"""F-D-009 Commitlint 配置状态管理 — CommitlintState

教师可通过该 State 在 Reflex 页面上完成：
- 配置规则集（Conventional Commits / 自定义）及参数编辑
- 生成 .commitlintrc.json 和 commitlint.yml
- 通过本地 Git 操作写入仓库并推送
- CI 联动控制（启用=error / 停用=0）
- 查看启用状态、规则版本、最近 5 次校验失败记录

不使用 GitHub API，改用本地 git 命令（subprocess）操作仓库。

依赖：
  - oaepp.database.transaction_sync — MySQL 数据库访问
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import reflex as rx

# ── 配置文件生成引擎（内联，无需独立模块） ─────────────────

def _build_commitlintrc(
    type_enum: list,
    header_max_length: int,
    subject_min_length: int,
    is_enabled: bool = True,
) -> str:
    """生成 .commitlintrc.json 内容。enabled 时规则级别 2（error），disabled 时 0（关闭）。"""
    level = 2 if is_enabled else 0
    rules = {
        "type-enum": [level, "always", sorted(set(type_enum))],
        "subject-min-length": [level, "always", subject_min_length],
        "header-max-length": [level, "always", header_max_length],
    }
    rc = {
        "extends": ["@commitlint/config-conventional"],
        "rules": rules,
    }
    return json.dumps(rc, indent=2, ensure_ascii=False)


def _generate_workflow_yml() -> str:
    """生成 .github/workflows/commitlint.yml 内容。"""
    return (
        "name: Commit Message 检查\n\n"
        "on: [pull_request]\n\n"
        "jobs:\n"
        "  commitlint:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "        with:\n"
        "          fetch-depth: 0\n"
        "      - uses: wagoid/commitlint-github-action@v5\n"
        "        with:\n"
        "          configFile: .commitlintrc.json\n"
    )


# ── 常量 ────────────────────────────────────────────────────

GITHUB_REPO = os.environ.get("GITHUB_REPO", "roboticsystem/OA-EPP")

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


# ── 本地 Git 操作 ───────────────────────────────────────────

def _get_repo_root() -> Path:
    """获取 Git 仓库根目录"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent,
            timeout=15,
        )
        if result.returncode != 0:
            raise RuntimeError(f"无法确定 Git 仓库根目录: {result.stderr.strip()}")
        return Path(result.stdout.strip())
    except FileNotFoundError:
        raise RuntimeError("Git 命令不可用，请确保 Git 已安装且在 PATH 中")


def _git_run(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """运行 git 命令，返回 CompletedProcess。失败时抛出 RuntimeError。"""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True, text=True,
            cwd=cwd or _get_repo_root(),
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)} 失败 (exit {result.returncode}): {result.stderr.strip()}"
            )
        return result
    except FileNotFoundError:
        raise RuntimeError("Git 命令不可用，请确保 Git 已安装且在 PATH 中")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"git {' '.join(args)} 超时")


def _list_remote_branches() -> list[dict]:
    """通过 git ls-remote 获取远程分支列表"""
    try:
        result = _git_run("ls-remote", "--heads", "origin")
        branches = []
        default_branch = ""
        # 同时获取默认分支（HEAD 指向）
        try:
            head_result = _git_run("ls-remote", "--symref", "origin", "HEAD")
            for line in head_result.stdout.splitlines():
                if "refs/heads/" in line and "HEAD" in line:
                    # ref: refs/heads/main	HEAD
                    default_branch = line.split("refs/heads/")[-1].split("\t")[0].strip()
                    break
        except RuntimeError:
            default_branch = "main"

        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) == 2:
                ref = parts[1]
                branch_name = ref.replace("refs/heads/", "")
                branches.append({
                    "name": branch_name,
                    "default": branch_name == default_branch,
                })
        return branches
    except RuntimeError:
        return []


def _check_git_remote() -> dict:
    """验证 Git 远程仓库可访问，返回仓库信息。"""
    try:
        # 先检查 remote 配置
        remote_result = _git_run("remote", "get-url", "origin")
        remote_url = remote_result.stdout.strip()

        # 尝试获取仓库信息
        result = _git_run("ls-remote", "origin", "HEAD")
        if not result.stdout.strip():
            return {"ok": False, "error": "远程仓库为空或无法访问"}

        # 获取默认分支
        default_branch = "main"
        for line in result.stdout.splitlines():
            if line.strip().endswith("HEAD"):
                # 通过 symref 确定默认分支
                pass
        try:
            symref_result = _git_run("ls-remote", "--symref", "origin", "HEAD")
            for line in symref_result.stdout.splitlines():
                if "refs/heads/" in line and "HEAD" in line:
                    default_branch = line.split("refs/heads/")[-1].split("\t")[0].strip()
                    break
        except RuntimeError:
            pass

        return {
            "ok": True,
            "full_name": GITHUB_REPO,
            "html_url": f"https://github.com/{GITHUB_REPO}",
            "default_branch": default_branch,
            "remote_url": remote_url,
        }
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}


def _file_exists_in_git(path: str) -> bool:
    """检查仓库中指定路径是否已被 Git 跟踪（已提交或已暂存）。"""
    try:
        # git ls-files 检查是否被跟踪
        result = _git_run("ls-files", path)
        return bool(result.stdout.strip())
    except RuntimeError:
        return False


def _get_current_branch() -> str:
    """获取当前 Git 分支名称。"""
    try:
        result = _git_run("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()
    except RuntimeError:
        return "main"


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

    # 新增：type 输入框绑定
    new_type_input: str = ""

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
        if not self.selected_branch:
            self.selected_branch = _get_current_branch()

    def load_branches(self):
        """加载远程分支列表（通过 git ls-remote）"""
        try:
            branches = _list_remote_branches()
            self.branches = branches
            if branches:
                default = next((b["name"] for b in branches if b["default"]), "main")
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
        commitlintrc = _build_commitlintrc(
            type_enum=self.type_enum,
            header_max_length=self.header_max_length,
            subject_min_length=self.subject_min_length,
            is_enabled=self.is_enabled,
        )
        workflow = _generate_workflow_yml()
        self.preview_commitlintrc = commitlintrc
        self.preview_workflow = workflow
        self._show_toast("✅ 配置文件已生成", "success")

    def push_config(self):
        """写入配置文件到本地仓库并通过 Git 推送到远程。

        不再使用 GitHub Contents API，改用本地 Git 命令：
          1. 写 .commitlintrc.json 到仓库根目录
          2. 写 .github/workflows/commitlint.yml 到仓库
          3. git add → git commit → git push
        """
        repo_root = _get_repo_root()
        target_branch = self.selected_branch or _get_current_branch()

        try:
            commitlintrc = _build_commitlintrc(
                type_enum=self.type_enum,
                header_max_length=self.header_max_length,
                subject_min_length=self.subject_min_length,
                is_enabled=self.is_enabled,
            )
            workflow = _generate_workflow_yml()

            # 1. 写入文件
            commitlintrc_path = repo_root / ".commitlintrc.json"
            workflow_dir = repo_root / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            workflow_path = workflow_dir / "commitlint.yml"

            commitlintrc_path.write_text(commitlintrc, encoding="utf-8")
            workflow_path.write_text(workflow, encoding="utf-8")

            # 2. Git 操作：add → commit → push
            status_label = "启用" if self.is_enabled else "停用"
            commit_msg = (
                f"chore(commitlint): {status_label}配置 v{self.config_version}\n\n"
                f"由 OA-EPP 平台自动提交。\n"
                f"规则版本: v{self.config_version}\n"
                f"规则集: {self.rule_set}\n"
                f"启用状态: {status_label}\n"
            )

            _git_run("add", ".commitlintrc.json", ".github/workflows/commitlint.yml")
            _git_run("commit", "-m", commit_msg.strip())
            _git_run("push", "origin", f"HEAD:{target_branch}")

            # 3. 获取提交 SHA
            sha_result = _git_run("rev-parse", "HEAD")
            commit_sha = sha_result.stdout.strip()

            self.push_result = {
                "commit_sha": commit_sha,
                "commit_url": f"https://github.com/{GITHUB_REPO}/commit/{commit_sha}",
                "git_history_url": (
                    f"https://github.com/{GITHUB_REPO}/commits/{target_branch}/.commitlintrc.json"
                ),
            }
            self._show_toast(
                f"✅ 已提交至仓库，commit: {commit_sha[:7]}",
                "success",
            )
        except Exception as e:
            self._show_toast(f"提交至仓库失败: {e}", "error")

    def check_repo_status(self):
        """检查 Git 仓库状态（使用本地 git 命令）。"""
        try:
            remote_info = _check_git_remote()
            if not remote_info.get("ok"):
                self.repo_status = {
                    "token_ok": False,
                    "error": remote_info.get("error", "远程仓库不可达"),
                }
                return

            # 检查文件是否已被 Git 跟踪
            wf_exists = _file_exists_in_git(".github/workflows/commitlint.yml")
            rc_exists = _file_exists_in_git(".commitlintrc.json")

            self.repo_status = {
                "token_ok": True,
                "full_name": remote_info.get("full_name"),
                "repo_url": remote_info.get("html_url"),
                "default_branch": remote_info.get("default_branch"),
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

    def set_new_type_input(self, value: str):
        """绑定 type 输入框的 on_change"""
        self.new_type_input = value

    def add_type(self, key: str):
        """键盘事件：按 Enter 时将输入框内容添加到 type_enum。

        参数 key 为 on_key_down 事件传入的按键名，
        同时支持按钮点击时传入 "click" 触发。
        """
        if key in ("Enter", "click") and self.new_type_input.strip():
            new_val = self.new_type_input.strip()
            if new_val not in self.type_enum:
                self.type_enum = [*self.type_enum, new_val]
            self.new_type_input = ""

    def add_type_by_button(self):
        """按钮点击添加 type（委托给 add_type）。"""
        self.add_type("click")

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
        rc = _build_commitlintrc(
            type_enum=self.type_enum,
            header_max_length=self.header_max_length,
            subject_min_length=self.subject_min_length,
            is_enabled=self.is_enabled,
        )
        workflow = _generate_workflow_yml()
        return {
            "commitlintrc": {"path": ".commitlintrc.json", "content": rc},
            "workflow": {"path": ".github/workflows/commitlint.yml", "content": workflow},
        }
