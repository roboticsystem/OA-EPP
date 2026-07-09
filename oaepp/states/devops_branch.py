"""F-D-002 分支保护 — BranchProtectState

通过 gh api 为 main 配置保护：禁直推、禁 Force Push、至少 1 人 Approve。
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any

try:
    import reflex as rx

    _StateBase = rx.State
except ImportError:  # pragma: no cover — 允许在无 Reflex 环境跑 TDD
    _StateBase = object  # type: ignore[misc, assignment]


class BranchProtectState(_StateBase):
    """开发运维：main 分支保护规则配置。"""

    protected_branch: str = "main"
    require_reviews: bool = True
    min_reviews: int = 1
    allow_force_push: bool = False
    protection_status: str = ""
    last_error: str = ""

    def _protection_payload(self) -> dict[str, Any]:
        return {
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "required_approving_review_count": max(1, self.min_reviews),
                "dismiss_stale_reviews": True,
            },
            "restrictions": None,
            "allow_force_pushes": self.allow_force_push,
            "allow_deletions": False,
        }

    def _repo_slug(self) -> str:
        return os.environ.get("GITHUB_REPOSITORY", "").strip()

    async def set_branch_protection(self) -> None:
        """调用 GitHub API 为 protected_branch 启用分支保护规则。"""
        self.last_error = ""
        self.protection_status = "running"
        repo = self._repo_slug()
        if not repo:
            self.last_error = "GITHUB_REPOSITORY 未设置，无法调用 gh api"
            self.protection_status = "failed"
            return

        payload = self._protection_payload()
        endpoint = f"/repos/{repo}/branches/{self.protected_branch}/protection"
        try:
            proc = subprocess.run(
                [
                    "gh",
                    "api",
                    "--method",
                    "PUT",
                    "-H",
                    "Accept: application/vnd.github+json",
                    endpoint,
                    "--input",
                    "-",
                ],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            self.last_error = "未找到 gh CLI，请先安装并登录 gh auth login"
            self.protection_status = "failed"
            return

        if proc.returncode != 0:
            self.last_error = (proc.stderr or proc.stdout or "gh api 失败").strip()
            self.protection_status = "failed"
            return

        self.protection_status = "ok"
