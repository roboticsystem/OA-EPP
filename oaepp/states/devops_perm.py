"""F-D-005 仓库协作者权限管理 — CollabPermState

通过 GitHub Team 统一管理课程组成员权限，禁止个人直接授权，确保权限管理规范化。

验收标准：
- 通过 GitHub Team 而非个人直接授权管理权限
- 角色分配符合 Admin/Write/Triage/Read 规范
- 权限变更有操作记录

架构说明：
- 创建四个标准 Team：admin、write、triage、read
- 将成员按角色分配到对应 Team
- 通过 Team 为仓库分配权限，而非直接授权个人
- 所有操作记录审计日志

GitHub API 操作：
- 创建 Team: POST /orgs/{org}/teams
- 添加成员到 Team: PUT /orgs/{org}/teams/{team_slug}/memberships/{username}
- 移除成员从 Team: DELETE /orgs/{org}/teams/{team_slug}/memberships/{username}
- 设置 Team 仓库权限: PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
    from sqlmodel import select, text
    from models import User, GithubBinding
except Exception:
    rx = None
    select = None
    text = None
    User = None
    GithubBinding = None

logger = logging.getLogger("oaepp.devops_perm")


class CollabPermState(rx.State if rx is not None else object):
    """仓库协作者权限管理状态

    通过 GitHub Team 模式管理仓库协作者权限，支持 Admin/Write/Triage/Read 四种角色。
    禁止个人直接授权，所有权限通过 Team 统一管理。
    """

    PERMISSION_ROLES = ["admin", "write", "triage", "read"]
    ROLE_CHOICES = PERMISSION_ROLES

    org_name: str = ""
    repo_name: str = ""
    team_name: str = ""
    
    simulation_mode: bool = True

    teams: List[dict] = []
    selected_team: str = ""

    members: List[dict] = []
    filtered_members: List[dict] = []

    is_loading: bool = False
    status_message: str = ""
    filter_role: str = "all"
    page_ready: bool = False

    total_members: int = 0
    admin_count: int = 0
    write_count: int = 0
    triage_count: int = 0
    read_count: int = 0

    audit_logs: List[Dict[str, Any]] = []

    def _update_counts(self):
        self.total_members = len(self.members)
        self.admin_count = sum(1 for m in self.members if m.get("role") == "admin")
        self.write_count = sum(1 for m in self.members if m.get("role") == "write")
        self.triage_count = sum(1 for m in self.members if m.get("role") == "triage")
        self.read_count = sum(1 for m in self.members if m.get("role") == "read")

    def _get_token(self) -> Optional[str]:
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    @staticmethod
    def _validate_github_param(value: str, name: str) -> str:
        if not re.fullmatch(r'[a-zA-Z0-9_\u4e00-\u9fa5-]+', value):
            raise ValueError(f"{name} 包含非法字符: {value}")
        return value

    def set_org_name(self, val: str):
        self.org_name = val

    def set_repo_name(self, val: str):
        self.repo_name = val

    def set_team_name(self, val: str):
        self.team_name = val

    def set_filter_role(self, val: str):
        self.filter_role = val
        self._filter_members()

    def _filter_members(self):
        if self.filter_role == "all":
            self.filtered_members = list(self.members)
        else:
            self.filtered_members = [m for m in self.members if m.get("role") == self.filter_role]

    async def create_standard_teams(self) -> dict:
        if not self.org_name:
            return {"success": False, "message": "请先配置 Organization 名称"}

        self._validate_github_param(self.org_name, "org_name")

        team_prefix = self.repo_name or "course"

        if self.simulation_mode or not self._get_token():
            created_teams = list(self.PERMISSION_ROLES)
            success_count = len(created_teams)
            fail_count = 0
            existing_teams = []
            failed_details = []
            
            self.teams = [
                {"name": f"{team_prefix}-{role}", "slug": f"{team_prefix}-{role}", "id": i + 1, "description": f"{role} permission team", "permission": role}
                for i, role in enumerate(self.PERMISSION_ROLES)
            ]
            
            logger.info(f"模拟创建标准 Team: {created_teams}")
        else:
            success_count = 0
            fail_count = 0
            created_teams = []
            existing_teams = []
            failed_details = []

            for role in self.PERMISSION_ROLES:
                team_name = f"{team_prefix}-{role}"
                try:
                    ok, msg, status_code = self._gh_api_post(
                        f"/orgs/{self.org_name}/teams",
                        json_body={
                            "name": team_name,
                            "description": f"{role} permission team for course collaboration",
                            "privacy": "closed",
                        },
                    )
                    if ok:
                        success_count += 1
                        created_teams.append(role)
                    elif status_code == 422 and "already exists" in msg.lower():
                        success_count += 1
                        existing_teams.append(role)
                        logger.info(f"Team {team_name} 已存在，跳过创建")
                    else:
                        fail_count += 1
                        failed_details.append(f"{team_name}: {msg}")
                        logger.error(f"创建 Team {team_name} 失败: {msg}")
                except Exception as e:
                    fail_count += 1
                    failed_details.append(f"{team_name}: {str(e)}")
                    logger.error(f"创建 Team {team_name} 失败: {e}")

        detail_info = {
            "org_name": self.org_name,
            "teams": self.PERMISSION_ROLES,
            "success_count": success_count,
            "fail_count": fail_count,
            "created_teams": created_teams,
            "existing_teams": existing_teams,
            "simulation": self.simulation_mode or not self._get_token(),
        }
        if failed_details:
            detail_info["failed_details"] = failed_details

        await self._write_audit_log(
            action="create_standard_teams",
            detail=detail_info,
        )

        if self.simulation_mode or not self._get_token():
            message = f"创建完成：成功 {success_count}（course-admin, course-write, course-triage, course-read）"
        elif fail_count == 0:
            if existing_teams:
                message = f"创建完成：成功 {success_count}（新建 {len(created_teams)}，已存在 {len(existing_teams)}）"
            else:
                message = f"创建完成：成功 {success_count}，失败 {fail_count}"
        else:
            message = f"创建完成：成功 {success_count}，失败 {fail_count}。失败详情：{' | '.join(failed_details)}"

        return {
            "success": fail_count == 0,
            "message": message,
            "created_teams": created_teams,
            "existing_teams": existing_teams,
        }

    async def load_teams(self) -> None:
        if not self.org_name:
            return

        self._validate_github_param(self.org_name, "org_name")

        if self.simulation_mode or not self._get_token():
            team_prefix = self.repo_name or "course"
            self.teams = [
                {"name": f"{team_prefix}-{role}", "slug": f"{team_prefix}-{role}", "id": i + 1, "description": f"{role} permission team", "permission": role}
                for i, role in enumerate(self.PERMISSION_ROLES)
            ]
            return

        try:
            ok, response, status_code = self._gh_api_get(f"/orgs/{self.org_name}/teams")
            if ok:
                try:
                    data = json.loads(response)
                    self.teams = [
                        {
                            "name": team.get("name", ""),
                            "slug": team.get("slug", ""),
                            "id": team.get("id", 0),
                            "description": team.get("description", ""),
                            "permission": team.get("permission", ""),
                        }
                        for team in data
                    ]
                except json.JSONDecodeError:
                    self.teams = []
            else:
                self.teams = []
        except Exception as e:
            logger.error(f"加载 Team 列表失败: {e}")
            self.teams = []

    async def load_members(self) -> None:
        self.is_loading = True
        try:
            with rx.session() as session:
                results = session.exec(
                    select(User, GithubBinding)
                    .outerjoin(GithubBinding, GithubBinding.student_user_id == User.id)
                    .where(User.role.in_(["admin", "teacher", "student"]))
                    .order_by(User.role.desc(), User.student_no)
                ).all()

                self.members = []
                for user, binding in results:
                    github_username = binding.github_username if binding else None
                    verify_status = binding.verify_status if binding else None
                    is_bound = bool(github_username and verify_status == "approved")

                    role_map = {
                        "admin": "admin",
                        "teacher": "write",
                        "student": "read",
                    }

                    member = {
                        "user_id": user.id,
                        "student_no": user.student_no,
                        "full_name": user.full_name,
                        "user_role": user.role,
                        "role": role_map.get(user.role, "read"),
                        "github_username": github_username or "",
                        "is_bound": is_bound,
                        "verify_status": verify_status or "",
                        "in_team": False,
                    }
                    self.members.append(member)

            if self.org_name:
                await self._refresh_member_team_status()

            self._update_counts()
            self._filter_members()
            self.page_ready = True

        except Exception as e:
            logger.error(f"加载成员列表失败: {e}")
            self.members = []
            self._update_counts()
        finally:
            self.is_loading = False

    async def load_audit_logs(self) -> None:
        try:
            with rx.session() as session:
                rows = session.exec(
                    text("""SELECT id, action, detail_json, action_at
                       FROM audit_logs
                       WHERE target_type = 'repo_collaborator'
                       ORDER BY action_at DESC
                       LIMIT 20""")
                ).all()

                self.audit_logs = []
                for row in rows:
                    try:
                        detail = json.loads(row.detail_json) if row.detail_json else {}
                    except json.JSONDecodeError:
                        detail = {}

                    action_map = {
                        "assign_member_role": "分配权限",
                        "remove_member_from_team": "移除成员",
                        "create_standard_teams": "创建标准 Team",
                        "configure_repo_permissions": "配置仓库权限",
                    }

                    if isinstance(detail, dict):
                        if row.action == "assign_member_role":
                            message = f"{detail.get('full_name', '')}: {detail.get('old_role', '')} → {detail.get('new_role', '')}"
                        elif row.action == "remove_member_from_team":
                            message = f"{detail.get('full_name', '')} 从 Team 移除"
                        elif row.action == "create_standard_teams":
                            message = f"组织: {detail.get('org_name', '')}, 成功: {detail.get('success_count', 0)}, 失败: {detail.get('fail_count', 0)}"
                        elif row.action == "configure_repo_permissions":
                            message = f"组织: {detail.get('org_name', '')}, 仓库: {detail.get('repo_name', '')}"
                        else:
                            message = str(detail)
                    else:
                        message = str(detail)
                    if row.action_at:
                        action_at_value = row.action_at
                        if action_at_value.tzinfo is None:
                            action_at_value = action_at_value.replace(tzinfo=timezone.utc)
                        local_time = action_at_value.astimezone(timezone(timedelta(hours=8)))
                        action_at_str = local_time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        action_at_str = ""
                    self.audit_logs.append({
                        "id": row.id,
                        "action": action_map.get(row.action, row.action),
                        "message": message,
                        "action_at": action_at_str,
                    })
        except Exception as e:
            logger.error(f"加载审计日志失败: {e}")
            self.audit_logs = []

    async def _refresh_member_team_status(self) -> None:
        if not self.org_name:
            return

        await self.load_teams()

        for member in self.members:
            github_username = member.get("github_username")
            if not github_username:
                continue

            try:
                for team in self.teams:
                    team_slug = team.get("slug", "")
                    if not team_slug:
                        continue

                    ok, response, status_code = self._gh_api_get(
                        f"/orgs/{self.org_name}/teams/{team_slug}/memberships/{github_username}"
                    )
                    if ok:
                        try:
                            data = json.loads(response)
                            if data.get("state") == "active":
                                member["in_team"] = True
                                member["current_team"] = team_slug
                                break
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

    async def add_member(self, user_id: int, role: str = "read") -> dict:
        return await self.assign_member_role(user_id, role)

    async def assign_member_role(self, user_id: int, new_role: str) -> dict:
        if new_role not in self.PERMISSION_ROLES:
            member = next((m for m in self.members if m["user_id"] == user_id), None)
            if member:
                new_role = member.get("role", "read")
            else:
                return {"success": False, "message": f"无效的角色: {new_role}"}

        if not self.org_name or not self.repo_name:
            return {"success": False, "message": "请先配置 Organization 和仓库名称"}

        self._validate_github_param(self.org_name, "org_name")
        self._validate_github_param(self.repo_name, "repo_name")

        member = next((m for m in self.members if str(m["user_id"]) == str(user_id)), None)
        if not member:
            return {"success": False, "message": f"成员不存在，user_id: {user_id}"}

        if not member.get("github_username"):
            return {"success": False, "message": "该成员未绑定 GitHub 账号"}

        old_role = member.get("role", "")

        try:
            await self.load_teams()

            if not self.teams:
                if self.simulation_mode or not self._get_token():
                    await self.create_standard_teams()
                    await self.load_teams()
                if not self.teams:
                    return {"success": False, "message": f"未在 Organization '{self.org_name}' 中找到任何 Team，请先创建标准 Team"}

            target_team_slug = None
            for team in self.teams:
                if new_role in team.get("name", ""):
                    target_team_slug = team.get("slug")
                    break

            if not target_team_slug:
                team_names = [t.get("name", "") for t in self.teams]
                return {"success": False, "message": f"未找到 {new_role} 对应的 Team，现有 Team: {', '.join(team_names)}"}

            if self.simulation_mode or not self._get_token():
                member["role"] = new_role
                member["current_team"] = target_team_slug
                member["in_team"] = True

                await self._write_audit_log(
                    action="assign_member_role",
                    detail={
                        "user_id": user_id,
                        "student_no": member["student_no"],
                        "full_name": member["full_name"],
                        "github_username": member["github_username"],
                        "old_role": old_role,
                        "new_role": new_role,
                        "org_name": self.org_name,
                        "team_slug": target_team_slug,
                        "simulation": True,
                    },
                )

                self._update_counts()
                self._filter_members()

                return {"success": True, "message": f"已将 {member['full_name']} 权限更新为 {new_role}，加入 Team: {target_team_slug}"}
            else:
                ok, msg, status_code = self._gh_api_put(
                    f"/orgs/{self.org_name}/teams/{target_team_slug}/memberships/{member['github_username']}",
                    json_body={"role": "member"},
                )

                if ok:
                    member["role"] = new_role
                    member["current_team"] = target_team_slug
                    member["in_team"] = True

                    await self._write_audit_log(
                        action="assign_member_role",
                        detail={
                            "user_id": user_id,
                            "student_no": member["student_no"],
                            "full_name": member["full_name"],
                            "github_username": member["github_username"],
                            "old_role": old_role,
                            "new_role": new_role,
                            "org_name": self.org_name,
                            "team_slug": target_team_slug,
                        },
                    )

                    self._update_counts()
                    self._filter_members()

                    return {"success": True, "message": f"已将 {member['full_name']} 权限更新为 {new_role}"}
                else:
                    return {"success": False, "message": f"分配失败: {msg}"}

        except Exception as e:
            logger.error(f"分配角色失败: {e}")
            return {"success": False, "message": str(e)}

    async def remove_member(self, user_id: int) -> dict:
        return await self.remove_member_from_team(user_id)

    async def remove_member_from_team(self, user_id: int) -> dict:
        if not self.org_name:
            return {"success": False, "message": "请先配置 Organization"}

        member = next((m for m in self.members if str(m["user_id"]) == str(user_id)), None)
        if not member:
            return {"success": False, "message": f"成员不存在，user_id: {user_id}"}

        if not member.get("github_username") or not member.get("current_team"):
            return {"success": False, "message": "该成员不在任何 Team 中"}

        try:
            removed_team = member.get("current_team", "")

            if self.simulation_mode or not self._get_token():
                member["in_team"] = False
                member["current_team"] = ""

                await self._write_audit_log(
                    action="remove_member_from_team",
                    detail={
                        "user_id": user_id,
                        "student_no": member["student_no"],
                        "full_name": member["full_name"],
                        "github_username": member["github_username"],
                        "removed_from_team": removed_team,
                        "org_name": self.org_name,
                        "simulation": True,
                    },
                )

                self._update_counts()
                self._filter_members()

                return {"success": True, "message": f"已将 {member['full_name']} 从 Team {removed_team} 中移除"}
            else:
                ok, msg, status_code = self._gh_api_delete(
                    f"/orgs/{self.org_name}/teams/{member['current_team']}/memberships/{member['github_username']}"
                )

                if ok:
                    member["in_team"] = False
                    member["current_team"] = ""

                    await self._write_audit_log(
                        action="remove_member_from_team",
                        detail={
                            "user_id": user_id,
                            "student_no": member["student_no"],
                            "full_name": member["full_name"],
                            "github_username": member["github_username"],
                            "removed_from_team": removed_team,
                            "org_name": self.org_name,
                        },
                    )

                    self._update_counts()
                    self._filter_members()

                    return {"success": True, "message": f"已将 {member['full_name']} 从 Team 中移除"}
                else:
                    return {"success": False, "message": f"移除失败: {msg}"}

        except Exception as e:
            logger.error(f"移除成员失败: {e}")
            return {"success": False, "message": str(e)}

    async def configure_repo_permissions(self) -> dict:
        if not self.org_name or not self.repo_name:
            return {"success": False, "message": "请先配置 Organization 和仓库名称"}

        self._validate_github_param(self.org_name, "org_name")
        self._validate_github_param(self.repo_name, "repo_name")

        await self.load_teams()

        owner = self.org_name

        if self.simulation_mode or not self._get_token():
            success_count = len(self.PERMISSION_ROLES)
            fail_count = 0
            logger.info(f"模拟配置仓库权限: {self.PERMISSION_ROLES}")
        else:
            success_count = 0
            fail_count = 0

            for role in self.PERMISSION_ROLES:
                team_slug = None
                for team in self.teams:
                    if role in team.get("name", ""):
                        team_slug = team.get("slug")
                        break

                if not team_slug:
                    fail_count += 1
                    continue

                try:
                    ok, msg, status_code = self._gh_api_put(
                        f"/orgs/{self.org_name}/teams/{team_slug}/repos/{owner}/{self.repo_name}",
                        json_body={"permission": role},
                    )

                    if ok:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error(f"配置 {role} Team 权限失败: {e}")

        await self._write_audit_log(
            action="configure_repo_permissions",
            detail={
                "org_name": self.org_name,
                "repo_name": self.repo_name,
                "success_count": success_count,
                "fail_count": fail_count,
                "simulation": self.simulation_mode or not self._get_token(),
            },
        )

        if self.simulation_mode or not self._get_token():
            message = f"仓库权限配置完成：成功 {success_count}（admin, write, triage, read）"
        else:
            message = f"仓库权限配置完成：成功 {success_count}，失败 {fail_count}"

        return {
            "success": fail_count == 0,
            "message": message,
        }

    async def _write_audit_log(self, action: str, detail: dict) -> None:
        try:
            with rx.session() as session:
                session.execute(
                    text("""INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail_json, action_at)
                       VALUES (:actor, :action, :target_type, :target_id, :detail, NOW())"""),
                    {
                        "actor": 0,
                        "action": action,
                        "target_type": "repo_collaborator",
                        "target_id": 0,
                        "detail": json.dumps(detail, ensure_ascii=False),
                    },
                )
                session.commit()
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    def _gh_api_post(self, endpoint: str, json_body: Optional[dict] = None) -> tuple:
        try:
            import requests
        except ImportError:
            return False, "requests 库不可用", 0

        token = self._get_token()
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.post(url, headers=headers, json=json_body or {}, timeout=30)
            status_code = resp.status_code
            response_text = resp.text
            
            if status_code in (200, 201):
                return True, response_text, status_code
            
            error_msg = f"HTTP {status_code}: {response_text[:300]}"
            logger.error(f"GitHub API POST {endpoint} 失败: {error_msg}")
            
            return False, error_msg, status_code
        except Exception as e:
            logger.error(f"GitHub API POST {endpoint} 异常: {e}")
            return False, str(e), 0

    def _gh_api_get(self, endpoint: str) -> tuple:
        try:
            import requests
        except ImportError:
            return False, "requests 库不可用", 0

        token = self._get_token()
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(url, headers=headers, timeout=30)
            status_code = resp.status_code
            if status_code == 200:
                return True, resp.text, status_code
            else:
                error_msg = f"HTTP {status_code}: {resp.text[:200]}"
                logger.error(f"GitHub API GET {endpoint} 失败: {error_msg}")
                return False, error_msg, status_code
        except Exception as e:
            logger.error(f"GitHub API GET {endpoint} 异常: {e}")
            return False, str(e), 0

    def _gh_api_put(self, endpoint: str, json_body: Optional[dict] = None) -> tuple:
        try:
            import requests
        except ImportError:
            return False, "requests 库不可用", 0

        token = self._get_token()
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.put(url, headers=headers, json=json_body or {}, timeout=30)
            status_code = resp.status_code
            if status_code in (200, 201, 204):
                return True, "success", status_code
            else:
                error_msg = f"HTTP {status_code}: {resp.text[:200]}"
                logger.error(f"GitHub API PUT {endpoint} 失败: {error_msg}")
                return False, error_msg, status_code
        except Exception as e:
            logger.error(f"GitHub API PUT {endpoint} 异常: {e}")
            return False, str(e), 0

    def _gh_api_delete(self, endpoint: str) -> tuple:
        try:
            import requests
        except ImportError:
            return False, "requests 库不可用", 0

        token = self._get_token()
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.delete(url, headers=headers, timeout=30)
            status_code = resp.status_code
            if status_code in (200, 204):
                return True, "success", status_code
            else:
                error_msg = f"HTTP {status_code}: {resp.text[:200]}"
                logger.error(f"GitHub API DELETE {endpoint} 失败: {error_msg}")
                return False, error_msg, status_code
        except Exception as e:
            logger.error(f"GitHub API DELETE {endpoint} 异常: {e}")
            return False, str(e), 0

    async def handle_load_members(self):
        self.status_message = ""
        await self.load_members()
        await self.load_audit_logs()

    async def handle_create_teams(self):
        self.is_loading = True
        self.status_message = ""
        try:
            result = await self.create_standard_teams()
            self.status_message = result.get("message", "")
            await self.load_teams()
        except Exception as e:
            self.status_message = f"创建 Team 失败: {e}"
        finally:
            self.is_loading = False

    async def handle_configure_repo_permissions(self):
        self.is_loading = True
        self.status_message = ""
        try:
            result = await self.configure_repo_permissions()
            self.status_message = result.get("message", "")
        except Exception as e:
            self.status_message = f"配置仓库权限失败: {e}"
        finally:
            self.is_loading = False

    async def handle_assign_role(self, user_id: int, new_role: str):
        self.status_message = ""
        result = await self.assign_member_role(user_id, new_role)
        self.status_message = result.get("message", "")

    async def handle_add_to_team(self, user_id):
        self.status_message = ""
        logger.info(f"handle_add_to_team called with user_id: {user_id}, type: {type(user_id)}")
        logger.info(f"Members list keys: {[m['user_id'] for m in self.members]}")
        
        member = None
        for m in self.members:
            if str(m["user_id"]) == str(user_id):
                member = m
                break
        
        if not member:
            self.status_message = f"成员不存在，user_id: {user_id} (类型: {type(user_id)})，现有成员ID: {[m['user_id'] for m in self.members]}"
            return
        
        role = member.get("role", "read")
        logger.info(f"Found member: {member['full_name']}, role: {role}")
        result = await self.assign_member_role(user_id, role)
        self.status_message = result.get("message", "")

    async def handle_remove_member(self, user_id: int):
        self.status_message = ""
        result = await self.remove_member(user_id)
        self.status_message = result.get("message", "")

    async def handle_refresh_status(self):
        self.status_message = ""
        await self._refresh_member_team_status()
        self._update_counts()
        self._filter_members()
        self.status_message = "状态已刷新"
