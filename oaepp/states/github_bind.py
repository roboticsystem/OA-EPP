"""GitHub 账号绑定状态（独立 State）

实现要点：
- 独立继承 `rx.State`，**不** 继承或修改 `GlobalState`。
- 使用安全的 `httpx.AsyncClient`（不绕过 SSL），并添加超时与异常处理。
- 保持行为最小化以便 TDD 测试通过；数据库写入留为后续步骤/管理员操作。
"""
from __future__ import annotations

import reflex as rx
import httpx
from typing import Optional


class GitHubBindState(rx.State):
    """管理 GitHub 绑定前端交互状态（不直接操作全局状态）。

    设计遵循 PR 审核意见：此 State 为独立 `rx.State`，读取全局信息
    应通过 `GlobalState` 的公开方法（由页面/调用方传入或读取）。
    """

    github_username: str = ""
    bind_status: str = "unbound"  # allowed: bound | unbound | pending
    error_message: str = ""

    async def bind_github(self) -> None:
        """尝试绑定当前 `github_username`。

        验证步骤：
        - 非空校验
        - 通过 GitHub API 验证用户是否存在（不跳过 SSL）
        - 当前实现不直接写入数据库（避免越权）；若验证通过将 `bind_status` 置为 `pending`。
        """
        self.error_message = ""
        username = (self.github_username or "").strip()
        if not username:
            self.error_message = "GitHub 用户名不能为空"
            self.bind_status = "unbound"
            return

        # 使用安全默认设置的 AsyncClient（不使用 verify=False）
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://api.github.com/users/{username}"
                resp = await client.get(url, headers={"Accept": "application/vnd.github.v3+json"})
                if resp.status_code == 200:
                    # 用户存在；将状态设为 pending（等待管理员/自动审批流程）
                    self.bind_status = "pending"
                    self.error_message = ""
                    return
                elif resp.status_code == 404:
                    self.error_message = "GitHub 用户未找到"
                    self.bind_status = "unbound"
                    return
                else:
                    self.error_message = f"GitHub API 返回 {resp.status_code}"
                    self.bind_status = "unbound"
                    return
        except httpx.HTTPError as exc:
            self.error_message = f"验证 GitHub 用户时出错：{exc}"
            self.bind_status = "unbound"
            return

    async def unbind(self) -> None:
        """前端触发的解绑动作（仅更新 State）。真正的数据移除需后台/管理员执行。"""
        self.github_username = ""
        self.bind_status = "unbound"
        self.error_message = ""
