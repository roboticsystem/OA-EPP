"""F-T-009 仓库权限配置 — RepoPermState

通过 GitHub Organization + Team 统一管理班级仓库访问权限。

依赖前置：
- F-T-001：学生 GitHub 账号映射表（github_bindings）已完整录入
- F-T-004：GitHub 账号绑定已审核通过

架构说明：
- 教师创建 GitHub Organization（如 oa-epp-2025）
- 在组织内为班级创建 Team（如 class-2025-fall），设定仓库权限为 Write
- 平台根据 github_bindings 批量邀请学生加入 Org 和 Team
- 学期结束一键撤销全班 Team 对仓库的访问

GitHub API 操作：
- 邀请学生加入 Org:  PUT /orgs/{org}/memberships/{username}
- 将学生加入 Team: PUT /orgs/{org}/teams/{team_slug}/memberships/{username}
- 撤销 Team 仓库权限: DELETE /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}

数据来源：
- github_bindings：student_user_id → github_username 映射
- audit_logs：操作审计日志
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

logger = logging.getLogger("oaepp.repo_perm")


class RepoPermState(rx.State if rx is not None else object):
    """仓库权限配置状态管理

    通过 GitHub Organization + Team 模式管理班级仓库访问权限。
    提供批量邀请、状态查看、重新发送邀请、一键撤销等功能。
    """

    # ── 核心状态变量（TDD 测试要求） ──
    org_name: str = ""
    team_name: str = ""
    members: List[dict] = []

    # ── 成员状态枚举 ──
    MEMBER_STATUS = ["accepted", "pending", "left"]

    member_status_options: List[str] = ["accepted", "pending", "left"]

    # ── 业务状态变量 ──
    repo_name: str = ""
    permission_level: str = "write"
    course_id: Optional[int] = None
    teacher_user_id: Optional[int] = None
    invite_result: dict = {}
    revoke_result: dict = {}

    # ── UI 状态变量 ──
    filter_status: str = "all"
    selected_usernames: List[str] = []
    status_message: str = ""
    is_loading: bool = False
    page_ready: bool = False
    total_members: int = 0
    accepted_count: int = 0
    pending_count: int = 0
    left_count: int = 0

    # ── 内部辅助 ──

    def _update_counts(self):
        self.total_members = len(self.members)
        self.accepted_count = sum(1 for m in self.members if m.get("invite_status") == "accepted")
        self.pending_count = sum(1 for m in self.members if m.get("invite_status") == "pending")
        self.left_count = sum(1 for m in self.members if m.get("invite_status") in ("left", ""))

    # ── 配置方法 ──

    def set_org_config(
        self,
        org_name: str,
        team_name: str,
        repo_name: str = "",
        permission_level: str = "write",
    ) -> None:
        """设置 Organization 和 Team 配置。

        Args:
            org_name: GitHub 组织名称（如 oa-epp-2025）
            team_name: 班级 Team 名称（如 class-2025-fall）
            repo_name: 课程仓库名称
            permission_level: 仓库权限级别（write / read / triage）
        """
        self.org_name = org_name
        self.team_name = team_name
        self.repo_name = repo_name
        self.permission_level = permission_level

    # ── 成员加载 ──

    async def load_members(self, course_id: Optional[int] = None) -> None:
        """从数据库加载班级学生及其 GitHub 绑定状态。

        查询 github_bindings 获取已绑定学生，标记未绑定学生。
        通过 GitHub API 查询团队中成员的当前状态。

        Args:
            course_id: 课程 ID，用于筛选特定班级学生
        """
        if course_id is not None:
            self.course_id = course_id

        try:
            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                if self.course_id:
                    cur.execute(
                        """
                        SELECT
                            u.id AS user_id,
                            u.student_no,
                            u.full_name,
                            gb.github_username,
                            gb.github_name,
                            gb.verify_status
                        FROM enrollments e
                        JOIN users u ON u.id = e.student_user_id
                        LEFT JOIN github_bindings gb ON gb.student_user_id = u.id
                        WHERE e.course_id = %s AND u.role = 'student'
                        ORDER BY u.student_no
                        """,
                        (self.course_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            u.id AS user_id,
                            u.student_no,
                            u.full_name,
                            gb.github_username,
                            gb.github_name,
                            gb.verify_status
                        FROM users u
                        LEFT JOIN github_bindings gb ON gb.student_user_id = u.id
                        WHERE u.role = 'student'
                        ORDER BY u.student_no
                        """
                    )

                rows = cur.fetchall()
            conn.close()

            self.members = []
            for row in rows:
                github_username = row.get("github_username")
                verify_status = row.get("verify_status")
                is_bound = bool(github_username and verify_status == "approved")

                member = {
                    "user_id": row["user_id"],
                    "student_no": row["student_no"],
                    "full_name": row["full_name"],
                    "github_username": github_username or "",
                    "github_name": row.get("github_name") or "",
                    "is_bound": is_bound,
                    "verify_status": verify_status or "",
                    "invite_status": "pending",  # 初始状态，后续由 API 刷新
                }
                self.members.append(member)

            # 如果已配置 org/team，尝试通过 GitHub API 刷新成员状态
            if self.org_name and self.team_name:
                await self._refresh_member_status_from_github()
            self._update_counts()

        except Exception as e:
            logger.error(f"加载班级成员失败: {e}")
            self.members = []
            self._update_counts()

    # ── 批量邀请 ──

    async def invite_all_students(
        self,
        course_id: Optional[int] = None,
        teacher_user_id: Optional[int] = None,
    ) -> dict:
        """批量邀请全班已绑定 GitHub 的学生加入 Organization 和 Team。

        流程：
        1. 加载成员列表（若未加载）
        2. 筛选已验证绑定 GitHub 的学生
        3. 通过 GitHub API 邀请加入 Organization
        4. 通过 GitHub API 添加到 Team
        5. 写入审计日志

        Args:
            course_id: 课程 ID
            teacher_user_id: 执行操作的教师用户 ID

        Returns:
            dict: {
                "success": bool,
                "success_count": int,
                "fail_count": int,
                "skip_count": int,
                "total": int,
                "failed_students": list,
                "message": str,
            }
        """
        if teacher_user_id is not None:
            self.teacher_user_id = teacher_user_id

        # 确保成员已加载
        if not self.members or (course_id and course_id != self.course_id):
            await self.load_members(course_id)

        if not self.org_name or not self.team_name:
            self.invite_result = {
                "success": False,
                "success_count": 0,
                "fail_count": 0,
                "skip_count": 0,
                "total": len(self.members),
                "failed_students": [],
                "message": "请先配置 Organization 和 Team 信息",
            }
            return self.invite_result

        bound = [m for m in self.members if m["is_bound"]]
        unbound = [m for m in self.members if not m["is_bound"]]

        success_count = 0
        fail_count = 0
        skip_count = len(unbound)
        failed_students: List[dict] = []

        now = datetime.datetime.now()

        for member in bound:
            github_username = member["github_username"]
            try:
                # 1) 邀请加入 Organization
                org_ok, org_msg = self._gh_api_put(
                    f"/orgs/{self.org_name}/memberships/{github_username}",
                    json_body={"role": "member"},
                )

                # 2) 加入 Team
                team_ok, team_msg = self._gh_api_put(
                    f"/orgs/{self.org_name}/teams/{self.team_name}/memberships/{github_username}",
                )

                if org_ok and team_ok:
                    member["invite_status"] = "pending"
                    success_count += 1
                else:
                    fail_count += 1
                    failed_students.append({
                        "student_no": member["student_no"],
                        "full_name": member["full_name"],
                        "github_username": github_username,
                        "reason": f"Org: {org_msg}, Team: {team_msg}",
                    })

            except Exception as e:
                fail_count += 1
                failed_students.append({
                    "student_no": member["student_no"],
                    "full_name": member["full_name"],
                    "github_username": github_username,
                    "reason": str(e),
                })

        # 标记未绑定学生
        for m in unbound:
            m["invite_status"] = "left"

        self.invite_result = {
            "success": fail_count == 0 and success_count > 0,
            "success_count": success_count,
            "fail_count": fail_count,
            "skip_count": skip_count,
            "total": len(self.members),
            "failed_students": failed_students,
            "message": (
                f"邀请完成：成功 {success_count}，失败 {fail_count}，跳过（未绑定）{skip_count}"
            ),
        }

        # 记录审计日志
        await self._write_audit_log(
            action="invite_all_students",
            detail={
                "org_name": self.org_name,
                "team_name": self.team_name,
                "course_id": self.course_id,
                "success_count": success_count,
                "fail_count": fail_count,
                "skip_count": skip_count,
                "total": len(self.members),
                "action_at": now.isoformat(),
            },
        )
        self._update_counts()

        return self.invite_result

    # ── 重新发送邀请 ──

    async def resend_invite(self, github_username: str) -> dict:
        """重新发送邀请给指定学生。

        Args:
            github_username: 学生的 GitHub 用户名

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self.org_name or not self.team_name:
            return {"success": False, "message": "请先配置 Organization 和 Team 信息"}

        try:
            org_ok, org_msg = self._gh_api_put(
                f"/orgs/{self.org_name}/memberships/{github_username}",
                json_body={"role": "member"},
            )
            team_ok, team_msg = self._gh_api_put(
                f"/orgs/{self.org_name}/teams/{self.team_name}/memberships/{github_username}",
            )

            if org_ok and team_ok:
                # 更新本地成员状态
                for m in self.members:
                    if m.get("github_username") == github_username:
                        m["invite_status"] = "pending"
                        break

                await self._write_audit_log(
                    action="resend_invite",
                    detail={
                        "github_username": github_username,
                        "org_name": self.org_name,
                        "team_name": self.team_name,
                    },
                )
                return {"success": True, "message": f"已重新发送邀请给 {github_username}"}
            else:
                return {
                    "success": False,
                    "message": f"重新发送失败: Org={org_msg}, Team={team_msg}",
                }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── 一键撤销 ──

    async def revoke_team_access(
        self,
        course_id: Optional[int] = None,
        teacher_user_id: Optional[int] = None,
    ) -> dict:
        """一键撤销班级 Team 对仓库的访问权限。

        通过 GitHub API 将 Team 从仓库移除，撤销整个班级的访问权限。

        Args:
            course_id: 课程 ID（可选）
            teacher_user_id: 执行操作的教师用户 ID

        Returns:
            dict: {
                "success": bool,
                "message": str,
            }
        """
        if teacher_user_id is not None:
            self.teacher_user_id = teacher_user_id
        if course_id is not None:
            self.course_id = course_id

        if not self.org_name or not self.team_name:
            self.revoke_result = {
                "success": False,
                "message": "请先配置 Organization 和 Team 信息",
            }
            return self.revoke_result

        # 获取仓库 owner（组织名即为 owner）
        owner = self.org_name
        repo = self.repo_name

        if not repo:
            self.revoke_result = {
                "success": False,
                "message": "请先配置仓库名称（repo_name）",
            }
            return self.revoke_result

        try:
            ok, message = self._gh_api_delete(
                f"/orgs/{self.org_name}/teams/{self.team_name}/repos/{owner}/{repo}"
            )
        except Exception as e:
            ok, message = False, str(e)

        now = datetime.datetime.now()
        self.revoke_result = {
            "success": ok,
            "message": message if not ok else f"已撤销 {self.team_name} 对 {repo} 的访问权限",
        }

        # 更新本地成员状态
        for m in self.members:
            m["invite_status"] = "left"

        await self._write_audit_log(
            action="revoke_team_access",
            detail={
                "org_name": self.org_name,
                "team_name": self.team_name,
                "repo_name": repo,
                "course_id": self.course_id,
                "member_count": len(self.members),
                "action_at": now.isoformat(),
            },
        )
        self._update_counts()

        return self.revoke_result

    # ── 过滤与查询 ──

    def filter_by_status(self, status: str) -> List[dict]:
        """按邀请状态筛选成员列表。

        Args:
            status: accepted | pending | left
        """
        if status == "all":
            return list(self.members)
        return [m for m in self.members if m.get("invite_status") == status]

    def get_status_counts(self) -> dict:
        """获取各状态成员统计。

        Returns:
            dict: {"accepted": int, "pending": int, "left": int, "total": int}
        """
        counts = {"accepted": 0, "pending": 0, "left": 0, "total": len(self.members)}
        for m in self.members:
            status = m.get("invite_status", "pending")
            if status in counts:
                counts[status] += 1
        return counts

    # ── UI 绑定方法 ──

    def set_org_name(self, val: str):
        self.org_name = val

    def set_team_name(self, val: str):
        self.team_name = val

    def set_repo_name(self, val: str):
        self.repo_name = val

    def set_permission_level(self, val: str):
        self.permission_level = val

    def set_filter_status(self, val: str):
        self.filter_status = val

    def toggle_select(self, username: str):
        if username in self.selected_usernames:
            self.selected_usernames = [u for u in self.selected_usernames if u != username]
        else:
            self.selected_usernames = self.selected_usernames + [username]

    def select_all_pending(self):
        self.selected_usernames = [
            m.get("github_username", "") for m in self.members
            if m.get("invite_status") == "pending" and m.get("github_username")
        ]

    def clear_selection(self):
        self.selected_usernames = []

    async def handle_invite_all(self):
        self.is_loading = True
        self.status_message = ""
        try:
            result = await self.invite_all_students()
            self.status_message = result.get("message", "")
        except Exception as e:
            self.status_message = f"邀请失败: {e}"
        self.is_loading = False

    async def handle_revoke(self):
        self.is_loading = True
        self.status_message = ""
        try:
            result = await self.revoke_team_access()
            self.status_message = result.get("message", "")
        except Exception as e:
            self.status_message = f"撤销失败: {e}"
        self.is_loading = False

    async def handle_resend(self, github_username: str):
        self.status_message = ""
        result = await self.resend_invite(github_username)
        self.status_message = result.get("message", "")

    async def handle_load_members(self):
        self.is_loading = True
        self.status_message = ""
        try:
            await self.load_members(self.course_id)
            self.page_ready = True
        except Exception as e:
            self.status_message = f"加载失败: {e}"
        self.is_loading = False

    def _get_token(self) -> Optional[str]:
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    # ── 内部方法 ──

    def _gh_api_put(self, endpoint: str, json_body: Optional[dict] = None) -> tuple:
        """通过 gh CLI 调用 GitHub API PUT 请求。

        Args:
            endpoint: API 路径（如 /orgs/{org}/memberships/{username}）
            json_body: 请求体（可选）

        Returns:
            (success: bool, message: str)
        """
        try:
            cmd = ["gh", "api", "--method", "PUT", endpoint]
            if json_body:
                cmd.extend(["-f", f"role={json_body.get('role', 'member')}"])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, "success"
            else:
                return False, result.stderr.strip() or result.stdout.strip()
        except FileNotFoundError:
            return self._requests_put(endpoint, json_body)
        except subprocess.TimeoutExpired:
            return False, "GitHub API 请求超时"
        except Exception as e:
            return False, str(e)

    def _gh_api_delete(self, endpoint: str) -> tuple:
        """通过 gh CLI 调用 GitHub API DELETE 请求。

        Returns:
            (success: bool, message: str)
        """
        try:
            cmd = ["gh", "api", "--method", "DELETE", endpoint]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, "success"
            else:
                return False, result.stderr.strip() or result.stdout.strip()
        except FileNotFoundError:
            return self._requests_delete(endpoint)
        except subprocess.TimeoutExpired:
            return False, "GitHub API 请求超时"
        except Exception as e:
            return False, str(e)

    def _requests_put(self, endpoint: str, json_body: Optional[dict] = None) -> tuple:
        """通过 requests 库调用 GitHub API PUT 请求（gh CLI 不可用时的回退方案）。"""
        try:
            import requests
        except ImportError:
            return False, "gh CLI 和 requests 库均不可用"

        token = self._get_token()
        if not token:
            return False, "未配置 GITHUB_TOKEN 环境变量"

        url = f"https://api.github.com{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            resp = requests.put(url, headers=headers, json=json_body or {}, timeout=30)
            if resp.status_code in (200, 201, 204):
                return True, "success"
            else:
                return False, resp.text[:200]
        except Exception as e:
            return False, str(e)

    def _requests_delete(self, endpoint: str) -> tuple:
        """通过 requests 库调用 GitHub API DELETE 请求（回退方案）。"""
        try:
            import requests
        except ImportError:
            return False, "gh CLI 和 requests 库均不可用"

        token = self._get_token()
        if not token:
            return False, "未配置 GITHUB_TOKEN 环境变量"

        url = f"https://api.github.com{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            if resp.status_code in (200, 204):
                return True, "success"
            else:
                return False, resp.text[:200]
        except Exception as e:
            return False, str(e)

    async def _refresh_member_status_from_github(self) -> None:
        """通过 GitHub API 查询团队中成员的实际加入状态，刷新本地 members 列表。"""
        for member in self.members:
            github_username = member.get("github_username")
            if not github_username:
                continue

            try:
                cmd = [
                    "gh", "api",
                    f"/orgs/{self.org_name}/teams/{self.team_name}/memberships/{github_username}",
                ]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=15,
                )
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        state = data.get("state", "pending")
                        member["invite_status"] = "accepted" if state == "active" else "pending"
                    except json.JSONDecodeError:
                        pass
                else:
                    # 不在团队中，状态为 pending 或 left
                    pass
            except Exception:
                pass

    async def _write_audit_log(self, action: str, detail: dict) -> None:
        """写入审计日志到 audit_logs 表。

        Args:
            action: 操作名称
            detail: 操作详情字典
        """
        try:
            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail_json, action_at)
                       VALUES (%s, %s, %s, %s, %s, NOW())""",
                    (
                        self.teacher_user_id,
                        action,
                        "repo_permission",
                        self.course_id or 0,
                        json.dumps(detail, ensure_ascii=False),
                    ),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    @staticmethod
    def _get_mysql_connection():
        """获取 MySQL 连接。"""
        import pymysql
        from urllib.parse import urlparse, unquote

        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            parsed = urlparse(db_url)
            return pymysql.connect(
                host=parsed.hostname or "127.0.0.1",
                port=parsed.port or 3306,
                user=parsed.username or "root",
                password=unquote(parsed.password) if parsed.password else "",
                database=parsed.path.lstrip("/") or "oaepp_dev",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        else:
            return pymysql.connect(
                host=os.environ.get("DB_HOST", "156.239.252.40"),
                port=int(os.environ.get("DB_PORT", "13306")),
                user=os.environ.get("DB_USER", "student_dev"),
                password=os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
                database=os.environ.get("DB_NAME", "oaepp_dev"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
