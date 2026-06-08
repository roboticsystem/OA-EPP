"""F-T-007 Issue关闭必填PR编号 — IssuePRState

提供 Issue-PR 关联规则的状态管理：
- require_pr_on_close: 是否要求关闭 Issue 时关联 PR（默认开启）
- require_merged_pr: 是否要求 PR 已合并才能关闭 Issue
- course_rules: 各课程的独立规则配置
- issue_pr_associations: Issue-PR 关联记录
- warnings: 未关联 PR 直接关闭的警告记录
- pr_validation_result: PR 验证结果
"""

import datetime
from typing import Any, Dict, List, Optional


class IssuePRState:
    """Issue-PR 关联规则状态管理

    对齐需求 F-T-007：
    - 教师可开启/关闭 Issue 必须关联 PR 规则
    - 规则生效后在平台内关闭 Issue 时强制弹框要求填写已存在 PR 编号
    - 实时 GitHub API 校验 PR 编号
    - 支持 Webhook 监听 GitHub 直接关闭事件
    - 未关联 PR 则生成后台警告记录
    - 规则配置按课程独立设置
    """

    # ── 核心状态变量 ──
    require_pr_on_close: bool = True
    """关闭 Issue 时是否必须关联 PR（默认开启）"""

    require_merged_pr: bool = False
    """是否要求 PR 已合并才能关闭 Issue"""

    course_rules: Dict[str, Dict[str, Any]] = {}
    """各课程的独立规则配置：{course_id: {require_pr_on_close, require_merged_pr}}"""

    issue_pr_associations: List[Dict[str, Any]] = []
    """Issue-PR 关联记录列表"""

    warnings: List[Dict[str, Any]] = []
    """未关联 PR 直接关闭的警告记录"""

    pr_validation_result: Dict[str, Any] = {}
    """当前 PR 验证结果"""

    # ── UI 状态变量 ──
    pr_number_input: str = ""
    """用户输入的 PR 编号"""

    show_pr_modal: bool = False
    """是否显示 PR 输入弹窗"""

    current_issue: Optional[Dict[str, Any]] = None
    """当前正在处理的 Issue"""

    # ── 私有属性 ──
    _db_session: Any = None
    _github_token: Optional[str] = None

    def __init__(self):
        self.require_pr_on_close = True
        self.require_merged_pr = False
        self.course_rules = {}
        self.issue_pr_associations = []
        self.warnings = []
        self.pr_validation_result = {}
        self.pr_number_input = ""
        self.show_pr_modal = False
        self.current_issue = None

    # ── 规则配置方法 ──

    def set_global_rule(self, require_pr_on_close: bool, require_merged_pr: bool) -> None:
        """设置全局规则配置

        Args:
            require_pr_on_close: 关闭 Issue 时是否必须关联 PR
            require_merged_pr: 是否要求 PR 已合并
        """
        self.require_pr_on_close = require_pr_on_close
        self.require_merged_pr = require_merged_pr

    def set_course_rule(self, course_id: str, require_pr_on_close: bool, require_merged_pr: bool) -> None:
        """设置特定课程的规则配置

        Args:
            course_id: 课程 ID
            require_pr_on_close: 关闭 Issue 时是否必须关联 PR
            require_merged_pr: 是否要求 PR 已合并
        """
        self.course_rules[course_id] = {
            "course_id": course_id,
            "require_pr_on_close": require_pr_on_close,
            "require_merged_pr": require_merged_pr,
            "updated_at": datetime.datetime.now().isoformat(),
        }

    def get_course_rule(self, course_id: str) -> Dict[str, Any]:
        """获取特定课程的规则配置，如果不存在则返回全局配置

        Args:
            course_id: 课程 ID

        Returns:
            课程规则配置
        """
        if course_id in self.course_rules:
            return self.course_rules[course_id]
        return {
            "course_id": course_id,
            "require_pr_on_close": self.require_pr_on_close,
            "require_merged_pr": self.require_merged_pr,
        }

    # ── PR 验证方法 ──

    async def validate_pr_number(self, pr_number: int, owner: str = "roboticsystem", repo: str = "OA-EPP") -> Dict[str, Any]:
        """验证 PR 编号是否存在，并返回 PR 状态信息

        Args:
            pr_number: PR 编号
            owner: GitHub 仓库所有者
            repo: GitHub 仓库名称

        Returns:
            验证结果：{valid, exists, number, title, state, is_merged, message}
        """
        self.pr_validation_result = await self._validate_pr_via_api(owner, repo, pr_number)
        return self.pr_validation_result

    async def _validate_pr_via_api(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """通过 GitHub API 验证 PR"""
        try:
            import os
            import httpx

            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            headers = {}
            
            if self._github_token or os.environ.get("GITHUB_TOKEN"):
                token = self._github_token or os.environ.get("GITHUB_TOKEN")
                headers["Authorization"] = f"token {token}"

            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers, timeout=10)

            if response.status_code == 404:
                return {
                    "valid": False,
                    "exists": False,
                    "message": f"PR #{pr_number} 不存在",
                }

            if response.status_code != 200:
                return {
                    "valid": False,
                    "exists": False,
                    "message": f"GitHub API 请求失败: {response.status_code}",
                }

            data = response.json()
            is_merged = data.get("merged", False) or (data.get("merged_at") is not None)

            return {
                "valid": True,
                "exists": True,
                "number": data.get("number", 0),
                "title": data.get("title", ""),
                "state": data.get("state", ""),
                "is_merged": is_merged,
                "merged_at": data.get("merged_at"),
                "user_login": data.get("user", {}).get("login", ""),
                "url": data.get("html_url", ""),
                "message": f"PR #{pr_number} 验证成功",
            }

        except Exception as e:
            return {
                "valid": False,
                "exists": False,
                "message": f"验证失败: {str(e)}",
            }

    # ── Issue 关闭方法 ──

    async def close_issue_with_pr(
        self,
        issue_number: int,
        pr_number: int,
        course_id: str,
        closed_by: str,
        owner: str = "roboticsystem",
        repo: str = "OA-EPP",
    ) -> Dict[str, Any]:
        """关闭 Issue 并关联 PR

        Args:
            issue_number: Issue 编号
            pr_number: PR 编号
            course_id: 课程 ID
            closed_by: 关闭 Issue 的用户
            owner: GitHub 仓库所有者
            repo: GitHub 仓库名称

        Returns:
            操作结果
        """
        # 获取课程规则
        rule = self.get_course_rule(course_id)

        # 验证规则是否要求关联 PR
        if not rule.get("require_pr_on_close", True):
            # 规则未启用，直接关闭
            await self._record_close_action(issue_number, None, course_id, closed_by)
            return {
                "success": True,
                "message": "Issue 已关闭（规则未启用）",
                "requires_pr": False,
            }

        # 验证 PR
        validation = await self.validate_pr_number(pr_number, owner, repo)
        if not validation.get("valid"):
            return {
                "success": False,
                "message": validation.get("message", "PR 验证失败"),
                "requires_pr": True,
            }

        # 如果要求 PR 已合并
        if rule.get("require_merged_pr", False) and not validation.get("is_merged"):
            return {
                "success": False,
                "message": "请先合并 PR 后再关闭 Issue",
                "requires_pr": True,
                "pr_info": validation,
            }

        # 记录关联
        await self._record_association(issue_number, pr_number, validation, course_id, closed_by)

        return {
            "success": True,
            "message": f"Issue #{issue_number} 已关闭，关联 PR #{pr_number}",
            "requires_pr": True,
            "pr_info": validation,
        }

    async def handle_github_webhook(self, event_data: Dict[str, Any]) -> None:
        """处理 GitHub Webhook 事件（监听直接关闭 Issue 的情况）

        Args:
            event_data: GitHub Webhook 事件数据
        """
        try:
            # 检查是否是 Issue 关闭事件
            if event_data.get("action") != "closed":
                return

            issue = event_data.get("issue", {})
            if not issue:
                return

            issue_number = issue.get("number")
            issue_title = issue.get("title", "")
            closed_by = issue.get("closed_by", {}).get("login", "")
            closed_at = issue.get("closed_at")

            if not issue_number:
                return

            # 检查是否有关联的 PR（通过事件数据或 body 中的关键词）
            has_pr_link = False
            
            # 检查 body 中是否有 PR 引用
            body = issue.get("body", "")
            if body and ("#" in body or "pull/" in body):
                has_pr_link = True

            # 检查关闭评论中是否有 PR 引用
            for comment in event_data.get("comments", []):
                if "#" in comment.get("body", ""):
                    has_pr_link = True

            # 如果没有关联 PR，生成警告
            if not has_pr_link:
                await self._generate_warning(issue_number, issue_title, closed_by, closed_at)

        except Exception:
            pass

    # ── 记录管理方法 ──

    async def _record_association(
        self,
        issue_number: int,
        pr_number: int,
        pr_info: Dict[str, Any],
        course_id: str,
        closed_by: str,
    ) -> None:
        """记录 Issue-PR 关联"""
        association = {
            "id": len(self.issue_pr_associations) + 1,
            "course_id": course_id,
            "issue_number": issue_number,
            "pr_number": pr_number,
            "pr_title": pr_info.get("title", ""),
            "pr_state": pr_info.get("state", ""),
            "pr_merged_at": pr_info.get("merged_at"),
            "closed_by": closed_by,
            "closed_at": datetime.datetime.now().isoformat(),
        }
        self.issue_pr_associations.append(association)

        # 持久化到数据库
        if hasattr(self, "_db_session") and self._db_session is not None:
            await self._save_association_to_db(association)

    async def _record_close_action(self, issue_number: int, pr_number: Optional[int], course_id: str, closed_by: str) -> None:
        """记录 Issue 关闭操作"""
        if pr_number:
            await self._record_association(issue_number, pr_number, {}, course_id, closed_by)

    async def _generate_warning(
        self, issue_number: int, issue_title: str, closed_by: str, closed_at: Optional[str]
    ) -> None:
        """生成未关联 PR 关闭的警告记录"""
        warning = {
            "id": len(self.warnings) + 1,
            "issue_number": issue_number,
            "issue_title": issue_title,
            "closed_by": closed_by,
            "closed_at": closed_at or datetime.datetime.now().isoformat(),
            "warning_type": "no_pr_associated",
            "warning_message": f"Issue #{issue_number} 被直接关闭，未关联 PR",
            "resolved": False,
            "resolved_at": None,
            "created_at": datetime.datetime.now().isoformat(),
        }
        self.warnings.append(warning)

        # 持久化到数据库
        if hasattr(self, "_db_session") and self._db_session is not None:
            await self._save_warning_to_db(warning)

    async def resolve_warning(self, warning_id: int) -> None:
        """标记警告已处理"""
        for warning in self.warnings:
            if warning.get("id") == warning_id:
                warning["resolved"] = True
                warning["resolved_at"] = datetime.datetime.now().isoformat()
                break

    async def load_associations(self, course_id: Optional[str] = None) -> None:
        """加载 Issue-PR 关联记录"""
        if hasattr(self, "_db_session") and self._db_session is not None:
            await self._load_associations_from_db(course_id)
        else:
            self.issue_pr_associations = []

    async def load_warnings(self, course_id: Optional[str] = None, resolved: Optional[bool] = None) -> None:
        """加载警告记录"""
        if hasattr(self, "_db_session") and self._db_session is not None:
            await self._load_warnings_from_db(course_id, resolved)
        else:
            self.warnings = []

    # ── UI 交互方法 ──

    def open_pr_modal(self, issue: Dict[str, Any]) -> None:
        """打开 PR 输入弹窗"""
        self.current_issue = issue
        self.pr_number_input = ""
        self.pr_validation_result = {}
        self.show_pr_modal = True

    def close_pr_modal(self) -> None:
        """关闭 PR 输入弹窗"""
        self.show_pr_modal = False
        self.current_issue = None
        self.pr_number_input = ""
        self.pr_validation_result = {}

    def update_pr_input(self, value: str) -> None:
        """更新 PR 编号输入"""
        self.pr_number_input = value
        # 实时验证
        if value.isdigit():
            import asyncio
            asyncio.create_task(self.validate_pr_number(int(value)))

    # ── 数据库操作（内部方法） ──

    async def _save_association_to_db(self, association: Dict[str, Any]) -> None:
        """保存关联记录到数据库"""
        try:
            from sqlmodel import text as sql_text

            session = self._db_session
            session.execute(
                sql_text("""
                    INSERT INTO issue_pr_associations 
                    (course_id, issue_number, pr_number, pr_title, pr_state, pr_merged_at, closed_by, closed_at)
                    VALUES (:course_id, :issue_number, :pr_number, :pr_title, :pr_state, :pr_merged_at, :closed_by, :closed_at)
                    ON DUPLICATE KEY UPDATE
                        pr_number = VALUES(pr_number),
                        pr_title = VALUES(pr_title),
                        pr_state = VALUES(pr_state),
                        pr_merged_at = VALUES(pr_merged_at),
                        closed_by = VALUES(closed_by),
                        closed_at = VALUES(closed_at)
                """),
                {
                    "course_id": association["course_id"],
                    "issue_number": association["issue_number"],
                    "pr_number": association["pr_number"],
                    "pr_title": association["pr_title"],
                    "pr_state": association["pr_state"],
                    "pr_merged_at": association["pr_merged_at"],
                    "closed_by": association["closed_by"],
                    "closed_at": association["closed_at"],
                },
            )
            session.commit()
        except Exception:
            pass

    async def _save_warning_to_db(self, warning: Dict[str, Any]) -> None:
        """保存警告记录到数据库"""
        try:
            from sqlmodel import text as sql_text

            session = self._db_session
            session.execute(
                sql_text("""
                    INSERT INTO issue_close_warnings
                    (issue_number, issue_title, closed_by, closed_at, warning_type, warning_message, resolved, created_at)
                    VALUES (:issue_number, :issue_title, :closed_by, :closed_at, :warning_type, :warning_message, :resolved, :created_at)
                """),
                {
                    "issue_number": warning["issue_number"],
                    "issue_title": warning["issue_title"],
                    "closed_by": warning["closed_by"],
                    "closed_at": warning["closed_at"],
                    "warning_type": warning["warning_type"],
                    "warning_message": warning["warning_message"],
                    "resolved": warning["resolved"],
                    "created_at": warning["created_at"],
                },
            )
            session.commit()
        except Exception:
            pass

    async def _load_associations_from_db(self, course_id: Optional[str] = None) -> None:
        """从数据库加载关联记录"""
        try:
            from sqlmodel import text as sql_text

            session = self._db_session
            if course_id:
                result = session.execute(
                    sql_text("SELECT * FROM issue_pr_associations WHERE course_id = :course_id ORDER BY closed_at DESC"),
                    {"course_id": course_id},
                )
            else:
                result = session.execute(
                    sql_text("SELECT * FROM issue_pr_associations ORDER BY closed_at DESC")
                )

            rows = result.fetchall()
            self.issue_pr_associations = []
            for row in rows:
                self.issue_pr_associations.append({
                    "id": row.id,
                    "course_id": row.course_id,
                    "issue_number": row.issue_number,
                    "pr_number": row.pr_number,
                    "pr_title": row.pr_title,
                    "pr_state": row.pr_state,
                    "pr_merged_at": row.pr_merged_at.isoformat() if row.pr_merged_at else None,
                    "closed_by": row.closed_by,
                    "closed_at": row.closed_at.isoformat() if row.closed_at else None,
                })
        except Exception:
            self.issue_pr_associations = []

    async def _load_warnings_from_db(self, course_id: Optional[str] = None, resolved: Optional[bool] = None) -> None:
        """从数据库加载警告记录"""
        try:
            from sqlmodel import text as sql_text

            session = self._db_session
            query = "SELECT * FROM issue_close_warnings"
            params = {}

            conditions = []
            if course_id:
                conditions.append("course_id = :course_id")
                params["course_id"] = course_id
            if resolved is not None:
                conditions.append("resolved = :resolved")
                params["resolved"] = resolved

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            result = session.execute(sql_text(query), params)
            rows = result.fetchall()

            self.warnings = []
            for row in rows:
                self.warnings.append({
                    "id": row.id,
                    "course_id": row.course_id,
                    "issue_number": row.issue_number,
                    "issue_title": row.issue_title,
                    "closed_by": row.closed_by,
                    "closed_at": row.closed_at.isoformat() if row.closed_at else None,
                    "warning_type": row.warning_type,
                    "warning_message": row.warning_message,
                    "resolved": bool(row.resolved),
                    "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
        except Exception:
            self.warnings = []