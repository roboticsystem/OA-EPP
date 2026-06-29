"""
F-S-003 GitHub 账号绑定功能 — GitHubBindState

功能概述：
- 学生可填写 GitHub 用户名，系统通过 GitHub API 校验账号有效性
- 绑定申请需教师审核，每个学生只允许绑定一个账号
- 已绑定账号修改需向教师申请解除旧绑定

继承关系：GitHubBindState → GlobalState → rx.State
  GlobalState 提供 current_user、show_toast 等公共能力。
"""

import httpx
import logging

_log = logging.getLogger(__name__)

try:
    import reflex as rx
except Exception:
    rx = None

# Dual-path import GlobalState
try:
    from oaepp.states import GlobalState
except Exception:
    from states import GlobalState  # type: ignore[no-redef]

# Dual-path import db / transaction
try:
    from oaepp.database import db, transaction
except Exception:
    from database import db, transaction  # type: ignore[no-redef]

# Dual-path import AuthState
try:
    from oaepp.states.auth import AuthState
except Exception:
    from states.auth import AuthState  # type: ignore[no-redef]


class GitHubBindState(GlobalState if GlobalState else rx.State if rx else object):
    """GitHub 账号绑定状态管理（继承 GlobalState，复用 current_user / show_toast）"""

    # ── 表单数据 ──
    github_username: str = ""
    """用户输入的 GitHub 用户名"""

    # ── 绑定状态信息 ──
    bind_status: str = "unbound"
    """当前绑定状态：unbound / pending / approved / rejected / pending_release"""

    github_info: dict = {}
    """GitHub API 返回的用户信息：{"username","name","avatar_url","exists"}"""

    # ── UI 状态 ──
    is_validating: bool = False
    is_submitting: bool = False
    validation_message: str = ""

    # ── Setter 方法 ──
    def set_github_username(self, username: str):
        """设置 GitHub 用户名"""
        self.github_username = username

    # ═════════════════════════════════════════════════════════════════════
    # 获取当前学生信息（优先 GlobalState，回退到 AuthState）
    # ═════════════════════════════════════════════════════════════════════

    async def _get_student_no(self) -> str:
        """获取当前登录学生的学号"""
        if self.current_user and self.current_user.get("student_no"):
            return self.current_user.get("student_no", "")
        try:
            auth = await self.get_state(AuthState)
            if auth.is_authenticated and auth.current_student_no:
                return auth.current_student_no
        except Exception:
            pass
        # 最终回退：开发模式默认学生账号
        return "2024000001"

    async def _get_user_id(self) -> int:
        """获取当前登录学生的 user_id"""
        if self.current_user and self.current_user.get("user_id"):
            return int(self.current_user.get("user_id", 0))
        try:
            auth = await self.get_state(AuthState)
            if auth.is_authenticated and auth.current_user_id:
                return int(auth.current_user_id)
        except Exception:
            pass
        return 0

    # ═════════════════════════════════════════════════════════════════════
    # 查询绑定状态
    # ═════════════════════════════════════════════════════════════════════

    async def load_bind_status(self):
        """从数据库加载当前用户的 GitHub 绑定状态（静默加载，不显示 toast）"""
        student_no = await self._get_student_no()
        _log.info("load_bind_status called, student_no=%s", student_no)
        if not student_no:
            _log.warning("load_bind_status: no student_no, returning")
            return

        try:
            async with db() as cur:
                # 终结可能残留的隐式事务，确保读到最新快照
                await cur.execute("ROLLBACK")
                await cur.execute(
                    """
                    SELECT gb.verify_status, gb.github_username, gb.github_name, gb.verified_by
                    FROM github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.student_no = %s
                    """,
                    (student_no,),
                )
                row = await cur.fetchone()
                _log.info("load_bind_status query result: %s", row)
                if row:
                    self.bind_status = row["verify_status"]
                    self.github_username = row["github_username"] or ""
                    self.github_info = {
                        "username": row["github_username"] or "",
                        "name": row.get("github_name") or "",
                        "exists": True,
                    }
                    # approved + verified_by IS NULL = 待解除绑定
                    if row["verify_status"] == "approved" and row.get("verified_by") is None:
                        self.bind_status = "pending_release"
                else:
                    self.bind_status = "unbound"
                    self.github_username = ""
                    self.github_info = {}
        except Exception as e:
            _log.exception("load_bind_status failed: %s", e)
            pass  # 静默失败，用户可手动刷新

    async def refresh_bind_status(self):
        """刷新绑定状态并显示 toast 提示（供用户手动点击按钮调用）"""
        student_no = await self._get_student_no()
        if not student_no:
            return rx.toast("请先登录", level="warning")

        await self.load_bind_status()

        if self.bind_status == "unbound":
            return rx.toast("暂无绑定记录", level="info")
        elif self.bind_status == "pending":
            return rx.toast(f"当前状态：待审核（{self.github_username}）", level="info")
        elif self.bind_status == "approved":
            return rx.toast(f"✅ 已绑定 {self.github_username}", level="success")
        elif self.bind_status == "pending_release":
            return rx.toast(f"⏳ 解除绑定申请审核中（{self.github_username}）", level="info")
        elif self.bind_status == "rejected":
            return rx.toast("绑定申请已被拒绝，可重新提交", level="warning")

    # =====================================================================
    # 验证 GitHub 用户名（调用 GitHub API）
    # =====================================================================

    async def validate_github_username(self):
        """通过 GitHub API 验证用户名是否存在"""
        if not self.github_username or not self.github_username.strip():
            self.validation_message = "请输入 GitHub 用户名"
            self.github_info = {"exists": False}
            return

        self.is_validating = True
        username = self.github_username.strip()

        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"https://api.github.com/users/{username}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.github_info = {
                        "username": data.get("login", username),
                        "name": data.get("name", ""),
                        "avatar_url": data.get("avatar_url", ""),
                        "exists": True,
                    }
                    self.validation_message = (
                        f"✅ GitHub 账号存在：{data.get('login', username)}"
                    )
                elif resp.status_code == 404:
                    self.github_info = {"exists": False}
                    self.validation_message = (
                        "❌ GitHub 账号不存在，请检查用户名是否正确"
                    )
                else:
                    self.validation_message = (
                        f"⚠️ GitHub API 请求失败（状态码：{resp.status_code}）"
                    )
                    self.github_info = {"exists": False}
        except httpx.TimeoutException:
            self.validation_message = "⚠️ GitHub API 请求超时，请检查网络连接"
            self.github_info = {"exists": False}
        except Exception as e:
            self.validation_message = f"⚠️ 验证失败：{e}"
            self.github_info = {"exists": False}
        finally:
            self.is_validating = False

    # =====================================================================
    # 提交绑定申请
    # =====================================================================

    async def submit_bind_request(self):
        """提交 GitHub 账号绑定申请（需教师审核）"""
        student_no = await self._get_student_no()
        if not student_no:
            return rx.toast("请先登录", level="warning")
        if not self.github_info.get("exists"):
            return rx.toast("请先验证 GitHub 用户名", level="warning")

        username = self.github_info["username"]
        name = self.github_info.get("name", "")
        self.is_submitting = True

        try:
            async with transaction() as cur:
                # 查询已有绑定记录
                await cur.execute(
                    """
                    SELECT gb.id, gb.verify_status, gb.verified_by
                    FROM github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.student_no = %s
                    """,
                    (student_no,),
                )
                existing = await cur.fetchone()

                if existing:
                    if existing["verify_status"] == "approved" and existing.get("verified_by") is not None:
                        self.is_submitting = False
                        return rx.toast("您已绑定 GitHub 账号，如需修改请先申请解除绑定", level="warning")
                    elif existing["verify_status"] == "pending":
                        self.is_submitting = False
                        return rx.toast("您的绑定申请正在审核中，请耐心等待", level="warning")
                    elif existing["verify_status"] == "approved" and existing.get("verified_by") is None:
                        self.is_submitting = False
                        return rx.toast("您的解除绑定申请正在审核中，请等待教师处理", level="warning")
                    else:
                        # rejected → 重新申请
                        await cur.execute(
                            """
                            UPDATE github_bindings
                            SET github_username=%s, github_name=%s,
                                verify_status='pending', verified_at=NULL, verified_by=NULL
                            WHERE id=%s
                            """,
                            (username, name, existing["id"]),
                        )
                        self.bind_status = "pending"
                        return rx.toast("绑定申请已重新提交，等待教师审核", level="success")
                else:
                    # 获取 user_id，并确保 students 表有对应记录
                    await cur.execute(
                        "SELECT id FROM users WHERE student_no=%s",
                        (student_no,),
                    )
                    usr = await cur.fetchone()
                    if not usr:
                        self.is_submitting = False
                        return rx.toast("学生账号不存在，请联系管理员", level="error")
                    user_id = usr["id"]

                    # 确保 students 表中有对应记录（外键约束要求）
                    await cur.execute(
                        "SELECT user_id FROM students WHERE user_id=%s",
                        (user_id,),
                    )
                    if not await cur.fetchone():
                        await cur.execute(
                            "SELECT full_name FROM users WHERE id=%s",
                            (user_id,),
                        )
                        u = await cur.fetchone()
                        class_name = u.get("full_name", "") if u else ""
                        await cur.execute(
                            "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
                            (user_id, class_name),
                        )

                    await cur.execute(
                        """
                        INSERT INTO github_bindings
                            (student_user_id, github_username, github_name, verify_status)
                        VALUES (%s, %s, %s, 'pending')
                        """,
                        (user_id, username, name),
                    )
                    self.bind_status = "pending"
                    return rx.toast("绑定申请已提交，等待教师审核", level="success")
        except Exception as e:
            em = str(e)
            if "doesn't exist" in em or "1146" in em:
                return rx.toast("数据库表不存在，请联系管理员创建 github_bindings 表", level="error")
            else:
                return rx.toast(f"提交失败：{em}", level="error")
        finally:
            self.is_submitting = False

    # =====================================================================
    # 申请解除绑定
    # =====================================================================

    async def request_unbind(self):
        """申请解除当前 GitHub 绑定（需教师审核）"""
        student_no = await self._get_student_no()
        if not student_no:
            return rx.toast("请先登录", level="warning")
        if self.bind_status != "approved":
            return rx.toast("当前无需解除绑定", level="warning")

        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    SET gb.verified_by = NULL
                    WHERE u.student_no = %s AND gb.verify_status = 'approved' AND gb.verified_by IS NOT NULL
                    """,
                    (student_no,),
                )
                if cur.rowcount == 0:
                    return rx.toast("未找到已绑定记录或已申请解除", level="warning")
        except Exception as e:
            return rx.toast(f"申请失败：{e}", level="error")

        self.bind_status = "pending_release"
        return rx.toast("解除绑定申请已提交，等待教师审核", level="success")
