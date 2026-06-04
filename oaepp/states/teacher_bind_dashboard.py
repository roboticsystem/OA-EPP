"""F-T-004 GitHub 账号绑定状态看板 — Reflex State

BindDashboardState 负责教师端绑定状态看板的查询与批量操作。
数据来源：MySQL 数据库 (oaepp_dev)，通过 backend.app.database 模块连接。
"""
import sys
import os

# 确保 backend 包可导入
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from app.database import db as _get_db


class BindDashboardState:
    """教师端 GitHub 账号绑定状态看板 State。

    Reflex 事件处理器实现 F-T-004 四项验收标准：
    - 展示已绑定/未绑定/待审核人数统计
    - 未绑定学生红色高亮 + 按未绑定先排序
    - 一键批量通过待审核请求
    - 向未绑定学生批量发送提醒
    """

    # ── 状态变量（Reflex var） ──
    total_students: int = 0
    bound_count: int = 0
    unbound_count: int = 0
    pending_count: int = 0

    # ── 列表数据 ──
    students: list = []

    @classmethod
    def load_summary(cls):
        """从数据库加载全班绑定状态汇总，更新状态变量。"""
        with _get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM students s JOIN users u ON s.user_id=u.id "
                "WHERE u.role='student'"
            ).fetchone()[0]
            bound = conn.execute(
                "SELECT COUNT(*) FROM github_bindings WHERE verify_status='approved'"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM github_bindings WHERE verify_status='pending'"
            ).fetchone()[0]
        cls.total_students = total or 0
        cls.bound_count = bound or 0
        cls.pending_count = pending or 0
        cls.unbound_count = max(cls.total_students - cls.bound_count - cls.pending_count, 0)

    @classmethod
    def batch_approve(cls, student_ids: list[str]) -> int:
        """批量通过待审核的绑定请求。返回实际通过的数量。"""
        if not student_ids:
            return 0
        placeholders = ",".join(["%s"] * len(student_ids))
        with _get_db() as conn:
            conn.execute(
                f"UPDATE github_bindings g JOIN users u ON g.student_user_id=u.id "
                f"SET g.verify_status='approved', g.verified_at=NOW() "
                f"WHERE u.student_no IN ({placeholders}) "
                f"AND g.verify_status='pending'",
                student_ids,
            )
        result = conn.rowcount
        cls.load_summary()
        return result

    @classmethod
    def send_reminder_to_unbound(cls, student_ids: list[str]) -> tuple[int, list[str]]:
        """向未绑定学生批量发送提醒。返回 (通知人数, 学生姓名列表)。"""
        if not student_ids:
            return 0, []
        placeholders = ",".join(["%s"] * len(student_ids))
        with _get_db() as conn:
            rows = conn.execute(
                f"SELECT u.full_name AS name FROM users u "
                f"JOIN students s ON s.user_id=u.id "
                f"LEFT JOIN github_bindings g ON g.student_user_id=u.id "
                f"WHERE u.student_no IN ({placeholders}) "
                f"AND (g.verify_status IS NULL OR g.verify_status NOT IN ('approved','pending'))",
                student_ids,
            ).fetchall()
        names = [r["name"] for r in rows]
        return len(names), names
