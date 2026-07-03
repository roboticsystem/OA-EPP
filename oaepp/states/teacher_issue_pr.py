"""F-T-007 Issue-PR 关联规则 — IssuePRState

规则功能：
- 教师可开启/关闭「Issue 关闭必须关联 PR」规则
- 规则生效后关闭 Issue 时强制弹框填写 PR 编号（实时 GitHub API 校验）
- 未合并 PR 关闭时弹出教师二次确认
- Issue 详情页展示关联 PR 编号及合并状态
- Webhook 监听 GitHub 直接关闭事件，未关联 PR 则生成后台警告记录
- 规则配置按课程独立设置
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import reflex as rx
except Exception:
    rx = None

logger = logging.getLogger("oaepp.states.teacher_issue_pr")


def _github_api_get(path: str) -> dict | None:
    """调用 GitHub API GET 请求，返回 JSON 或 None。"""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB__USER_TOKEN")
    if not token:
        return None
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as e:
        logger.warning("GitHub API 调用失败 %s: %s", path, e)
        return None


def _validate_pr_with_github(pr_number: int) -> dict:
    """通过 GitHub API 校验 PR 是否存在并返回状态信息。

    返回:
        {"valid": True, "state": "open"|"merged"|"closed", "title": "...",
         "html_url": "..."}  或
        {"valid": False, "error": "..."}
    """
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return {"valid": False, "error": "未配置 GITHUB_REPOSITORY"}
    data = _github_api_get(f"/repos/{repo}/pulls/{pr_number}")
    if data is None:
        return {"valid": False, "error": "GitHub API 调用失败，请检查网络或 Token 配置"}
    if "id" not in data:
        return {"valid": False, "error": f"PR #{pr_number} 不存在"}
    state = data.get("state", "unknown")
    merged = data.get("merged", False)
    pr_state = "merged" if merged else state
    return {
        "valid": True,
        "state": pr_state,
        "title": data.get("title", ""),
        "html_url": data.get("html_url", ""),
        "user": (data.get("user") or {}).get("login", ""),
    }


class IssuePRState(rx.State if rx is not None else object):
    """F-T-007：Issue 关闭必须关联 PR 规则状态管理。"""

    # ── 规则开关 ──
    rule_enabled: bool = True
    close_issue_requires_pr: bool = True

    # ── 警告/违规记录 ──
    warning_log: list[dict] = []

    # ── Issue-PR 映射（issue_id → pr_info） ──
    issue_pr_map: dict[int, dict] = {}

    # ── 当前课程配置 ──
    current_course_id: int = 0

    # ── UI 状态 ──
    pr_input_dialog_open: bool = False
    pr_input_value: str = ""
    pr_validation_result: dict = {}
    pr_validation_loading: bool = False
    teacher_confirm_dialog_open: bool = False
    pending_close_issue_id: Optional[int] = None
    pending_close_pr_number: Optional[int] = None
    status_message: str = ""
    courses: list[dict] = []

    # ── 配置页面 UI ──
    config_course_options: list[dict] = []
    selected_course_id: int = 0

    def set_rule_enabled(self, value: bool):
        self.rule_enabled = value
        self.close_issue_requires_pr = value

    def set_pr_input_value(self, value: str):
        self.pr_input_value = value

    def open_pr_input_dialog(self, issue_id: int):
        self.pending_close_issue_id = issue_id
        self.pr_input_value = ""
        self.pr_validation_result = {}
        self.pr_input_dialog_open = True

    def close_pr_input_dialog(self):
        self.pr_input_dialog_open = False
        self.pr_input_value = ""
        self.pr_validation_result = {}
        self.pending_close_issue_id = None
        self.pending_close_pr_number = None

    async def validate_pr_number(self):
        """实时校验用户输入的 PR 编号（通过 GitHub API）。"""
        raw = self.pr_input_value.strip()
        if not raw:
            self.pr_validation_result = {"valid": False, "error": "请输入 PR 编号"}
            return
        try:
            pr_num = int(raw)
        except ValueError:
            self.pr_validation_result = {"valid": False, "error": "PR 编号必须为数字"}
            return
        self.pr_validation_loading = True
        result = _validate_pr_with_github(pr_num)
        self.pr_validation_result = result
        self.pr_validation_loading = False

    async def confirm_close_with_pr(self):
        """确认使用已校验的 PR 编号关闭 Issue。"""
        if not self.pr_validation_result.get("valid"):
            return
        pr_state = self.pr_validation_result.get("state", "")
        # 未合并 PR 关闭时弹出教师二次确认
        if pr_state != "merged":
            self.teacher_confirm_dialog_open = True
            self.pending_close_pr_number = int(self.pr_input_value.strip())
            return
        await self._do_close_issue()

    async def confirm_unmerged_close(self):
        """教师确认关闭未合并 PR 的 Issue。"""
        self.teacher_confirm_dialog_open = False
        await self._do_close_issue()

    def cancel_unmerged_close(self):
        """教师取消关闭未合并 PR 的 Issue。"""
        self.teacher_confirm_dialog_open = False
        self.close_pr_input_dialog()
        self.status_message = "已取消关闭 Issue（未合并 PR）"

    async def _do_close_issue(self):
        """执行 Issue 关闭操作并记录 PR 关联。"""
        issue_id = self.pending_close_issue_id
        pr_number = self.pending_close_pr_number or int(self.pr_input_value.strip())
        if issue_id is not None and pr_number:
            self.issue_pr_map[issue_id] = {
                "pr_number": pr_number,
                "state": self.pr_validation_result.get("state", "open"),
                "title": self.pr_validation_result.get("title", ""),
                "html_url": self.pr_validation_result.get("html_url", ""),
                "closed_at": datetime.now(timezone.utc).isoformat(),
            }
        self.close_pr_input_dialog()
        self.status_message = f"Issue #{issue_id} 已关闭，关联 PR #{pr_number}"

    async def validate_issue_close(
        self, issue_id: int, linked_pr_id: int | None
    ) -> bool | str:
        """校验关闭 Issue 时是否有有效 PR 关联。

        规则启用且无 PR → 返回 False 或 "blocked"
        规则启用且有 PR → 返回 True 或 "allowed"（尽力校验，API 不可达时仍允许）
        规则禁用 → 返回 True 或 "allowed"
        """
        if not self.rule_enabled:
            return "allowed"
        if linked_pr_id is not None:
            result = _validate_pr_with_github(linked_pr_id)
            if result.get("valid"):
                self.issue_pr_map[issue_id] = {
                    "pr_number": linked_pr_id,
                    "state": result.get("state", "open"),
                    "title": result.get("title", ""),
                    "html_url": result.get("html_url", ""),
                }
            return "allowed"
        self.warning_log.append({
            "issue_id": issue_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "关闭 Issue 时未关联有效 PR",
            "source": "platform",
        })
        return "blocked"

    async def handle_issue_closed_webhook(self, payload: dict | None = None):
        """处理 GitHub Issue 关闭 Webhook 事件。

        如果 Issue 是通过 GitHub 网页直接关闭（绕过平台），
        检查是否有关联 PR，没有则生成警告记录。
        """
        if payload is None:
            return
        action = payload.get("action", "")
        if action != "closed":
            return
        issue = payload.get("issue", {})
        issue_id = issue.get("number")
        if issue_id is None:
            return
        # 检查是否已在本平台有关联 PR 记录
        if issue_id in self.issue_pr_map:
            return
        self.warning_log.append({
            "issue_id": issue_id,
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("html_url", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "Issue 被直接关闭（未通过平台，无关联 PR）",
            "source": "webhook",
            "closed_by": (issue.get("user") or {}).get("login", "unknown"),
        })
        logger.warning(
            "Webhook 警告：Issue #%s 被直接关闭，无关联 PR", issue_id
        )

    # ── 课程配置管理 ──

    def load_courses(self):
        try:
            from oaepp.models import Course
            from sqlmodel import select
            with rx.session() as session:
                courses = session.exec(select(Course)).all()
                self.courses = [
                    {"id": c.id, "name": c.name, "code": c.code, "term": c.term}
                    for c in courses
                ]
                self.config_course_options = [
                    {"label": f"{c.code} - {c.name}", "value": str(c.id)}
                    for c in courses
                ]
        except Exception as e:
            logger.warning("加载课程列表失败: %s", e)

    def select_course(self, course_id: str):
        self.selected_course_id = int(course_id)
        self._load_course_config()

    def _load_course_config(self):
        if not self.selected_course_id:
            return
        try:
            from oaepp.models import CourseIssuePrConfig
            from sqlmodel import select
            with rx.session() as session:
                result = session.exec(
                    select(CourseIssuePrConfig).where(
                        CourseIssuePrConfig.course_id == self.selected_course_id
                    )
                ).first()
                if result is not None:
                    self.rule_enabled = result.rule_enabled
                    self.close_issue_requires_pr = result.rule_enabled
                else:
                    self.rule_enabled = True
                    self.close_issue_requires_pr = True
        except Exception as e:
            logger.warning("加载课程规则配置失败: %s", e)

    def toggle_rule(self, enabled: bool):
        self.rule_enabled = enabled
        self.close_issue_requires_pr = enabled

    def save_course_config(self):
        if not self.selected_course_id:
            self.status_message = "请先选择课程"
            return
        try:
            from oaepp.models import CourseIssuePrConfig
            from sqlmodel import select
            current_user = self.get_current_user()
            teacher_user_id = current_user.get("id", 0)
            with rx.session() as session:
                config = session.exec(
                    select(CourseIssuePrConfig).where(
                        CourseIssuePrConfig.course_id == self.selected_course_id
                    )
                ).first()
                if config is None:
                    config = CourseIssuePrConfig(
                        course_id=self.selected_course_id,
                        rule_enabled=self.rule_enabled,
                        updated_by=teacher_user_id,
                    )
                    session.add(config)
                else:
                    config.rule_enabled = self.rule_enabled
                    config.updated_by = teacher_user_id
                    config.updated_at = datetime.now()
                session.commit()
            self.status_message = f"课程规则配置已保存（规则{'开启' if self.rule_enabled else '关闭'}）"
        except Exception as e:
            self.status_message = f"保存失败: {e}"
            logger.warning("保存课程规则配置失败: %s", e)

    def clear_warning_log(self):
        self.warning_log = []

    def on_load(self):
        self.load_courses()


# ═══════════════════════════════════════════════════════════════════════════
#  Webhook HTTP 端点注册（无需修改 app.py）
#  GitHub Issue 关闭事件监听：POST /api/webhook/issue-closed
# ═══════════════════════════════════════════════════════════════════════════

try:
    from oaepp.app import app as _oaepp_app
    from starlette.routing import Route
    from starlette.responses import JSONResponse

    async def _webhook_issue_closed(request):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"status": "error", "message": "invalid payload"}, status_code=400)
        action = payload.get("action", "")
        if action != "closed":
            return JSONResponse({"status": "ignored", "message": f"action={action} 非关闭事件"})
        try:
            state_instance = IssuePRState()
            await state_instance.handle_issue_closed_webhook(payload)
        except Exception as e:
            logger.error("Webhook 处理异常: %s", e)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        return JSONResponse({"status": "ok", "message": "已处理 Issue 关闭事件"})

    if _oaepp_app is not None and hasattr(_oaepp_app, "_api") and _oaepp_app._api is not None:
        _existing = [r.path for r in _oaepp_app._api.routes]
        if "/api/webhook/issue-closed" not in _existing:
            _oaepp_app._api.routes.append(
                Route("/api/webhook/issue-closed", _webhook_issue_closed, methods=["POST"])
            )
except Exception:
    pass
