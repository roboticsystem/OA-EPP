"""
F-S-003 教师审核端 — GitHubBindAdminState

功能：
- 教师查看待审核的 GitHub 账号绑定申请
- 批准 / 拒绝绑定申请
"""

from typing import Dict, List

try:
    import reflex as rx
except Exception:
    rx = None

# ── 双路径导入 GlobalState ─────────────────────────────────────────────
try:
    from oaepp.states import GlobalState
except Exception:
    from states import GlobalState  # type: ignore[no-redef]

# ── 双路径导入 db / transaction ──────────────────────────────────────────
try:
    from oaepp.database import db, transaction
except Exception:
    from database import db, transaction  # type: ignore[no-redef]

# ── 双路径导入 AuthState（用于获取当前登录用户） ───────────────────────
try:
    from oaepp.states.auth import AuthState
except Exception:
    from states.auth import AuthState  # type: ignore[no-redef]


class GitHubBindAdminState(GlobalState if GlobalState else rx.State if rx else object):
    """GitHub 绑定审核管理状态"""

    # ── 列表数据 ──
    pending_list: List[Dict] = []
    """待审核的绑定申请列表"""

    # ── 审核操作状态 ──
    is_loading: bool = False
    action_message: str = ""

    # ═════════════════════════════════════════════════════════════════════
    # 获取当前教师用户信息（优先 GlobalState，回退到 AuthState）
    # ═════════════════════════════════════════════════════════════════════

    async def _get_teacher_id(self) -> int:
        """获取当前登录教师的 user_id，验证其确实在 teachers 表中"""
        # 1) 尝试从当前用户获取
        candidate_id = None
        if self.current_user and self.current_user.get("user_id"):
            candidate_id = int(self.current_user.get("user_id", 0))
        if not candidate_id:
            try:
                auth = await self.get_state(AuthState)
                if auth.is_authenticated and auth.current_user_id:
                    candidate_id = int(auth.current_user_id)
            except Exception:
                pass

        # 2) 验证 candidate 是否确实是教师
        if candidate_id:
            try:
                async with db() as cur:
                    await cur.execute(
                        "SELECT user_id FROM teachers WHERE user_id = %s", (candidate_id,)
                    )
                    if await cur.fetchone():
                        return candidate_id
            except Exception:
                pass

        # 3) 回退：查询任意一个教师
        try:
            async with db() as cur:
                await cur.execute(
                    "SELECT u.id FROM users u JOIN teachers t ON u.id = t.user_id WHERE u.role='teacher' LIMIT 1"
                )
                row = await cur.fetchone()
                if row:
                    return int(row["id"])
        except Exception:
            pass
        return 1

    # ═════════════════════════════════════════════════════════════════════
    # 加载待审核列表
    # ═════════════════════════════════════════════════════════════════════

    async def load_pending_list(self):
        """加载所有待审核的 GitHub 绑定申请"""
        self.is_loading = True
        try:
            async with db() as cur:
                # 终结可能残留的隐式事务，确保读到最新快照
                await cur.execute("ROLLBACK")
                await cur.execute(
                    """
                    SELECT 
                        gb.id,
                        u.student_no,
                        u.full_name AS student_name,
                        gb.github_username,
                        gb.github_name,
                        gb.verify_status,
                        gb.verified_by
                    FROM github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    ORDER BY gb.id DESC
                    """
                )
                rows = await cur.fetchall()
                self.pending_list = [
                    {
                        "id": r["id"],
                        "student_no": r["student_no"],
                        "student_name": r["student_name"],
                        "github_username": r["github_username"],
                        "github_name": r["github_name"] or "",
                        "verify_status": r["verify_status"],
                        "verified_by": r.get("verified_by"),
                        "is_pending_release": (
                            r["verify_status"] == "approved"
                            and r.get("verified_by") is None
                        ),
                    }
                    for r in rows
                ]
        except Exception as e:
            self.show_toast(f"加载失败：{e}", "error")
        finally:
            self.is_loading = False

    # ═════════════════════════════════════════════════════════════════════
    # 审核操作
    # ═════════════════════════════════════════════════════════════════════

    async def approve_binding(self, binding_id: int):
        """批准 GitHub 绑定申请"""
        teacher_id = await self._get_teacher_id()
        if not teacher_id:
            return rx.toast("请先登录教师账号", level="warning")

        success = False
        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET verify_status = 'approved', verified_at = NOW(), verified_by = %s
                    WHERE id = %s AND verify_status = 'pending'
                    """,
                    (teacher_id, binding_id),
                )
                if cur.rowcount == 0:
                    await self.load_pending_list()
                    return rx.toast("该申请已处理或不存在", level="warning")
                success = True
        except Exception as e:
            await self.load_pending_list()
            return rx.toast(f"操作失败：{e}", level="error")

        await self.load_pending_list()
        if success:
            return rx.toast("✅ 已批准绑定申请", level="success")

    async def reject_binding(self, binding_id: int):
        """拒绝 GitHub 绑定申请"""
        teacher_id = await self._get_teacher_id()
        if not teacher_id:
            return rx.toast("请先登录教师账号", level="warning")

        success = False
        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET verify_status = 'rejected', verified_at = NOW(), verified_by = %s
                    WHERE id = %s AND verify_status = 'pending'
                    """,
                    (teacher_id, binding_id),
                )
                if cur.rowcount == 0:
                    await self.load_pending_list()
                    return rx.toast("该申请已处理或不存在", level="warning")
                success = True
        except Exception as e:
            await self.load_pending_list()
            return rx.toast(f"操作失败：{e}", level="error")

        await self.load_pending_list()
        if success:
            return rx.toast("已拒绝绑定申请", level="warning")

    # ═════════════════════════════════════════════════════════════════════
    # 解除绑定审核
    # ═════════════════════════════════════════════════════════════════════

    async def approve_unbind(self, binding_id: int):
        """同意解除绑定 — 删除绑定记录"""
        teacher_id = await self._get_teacher_id()
        if not teacher_id:
            return rx.toast("请先登录教师账号", level="warning")

        try:
            async with transaction() as cur:
                await cur.execute(
                    "DELETE FROM github_bindings WHERE id = %s AND verify_status = 'approved' AND verified_by IS NULL",
                    (binding_id,),
                )
                if cur.rowcount == 0:
                    await self.load_pending_list()
                    return rx.toast("该申请已处理或不存在", level="warning")
        except Exception as e:
            await self.load_pending_list()
            return rx.toast(f"操作失败：{e}", level="error")

        await self.load_pending_list()
        return rx.toast("✅ 已同意解除绑定", level="success")

    async def reject_unbind(self, binding_id: int):
        """拒绝解除绑定 — 恢复 verified_by 为教师 ID"""
        teacher_id = await self._get_teacher_id()
        if not teacher_id:
            return rx.toast("请先登录教师账号", level="warning")

        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET verified_by = %s, verified_at = NOW()
                    WHERE id = %s AND verify_status = 'approved' AND verified_by IS NULL
                    """,
                    (teacher_id, binding_id),
                )
                if cur.rowcount == 0:
                    await self.load_pending_list()
                    return rx.toast("该申请已处理或不存在", level="warning")
        except Exception as e:
            await self.load_pending_list()
            return rx.toast(f"操作失败：{e}", level="error")

        await self.load_pending_list()
        return rx.toast("已拒绝解除绑定申请", level="warning")
