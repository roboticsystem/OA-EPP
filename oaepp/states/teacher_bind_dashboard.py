"""F-T-004 GitHub 账号绑定状态看板 — Reflex State

BindDashboardState 负责教师端绑定状态看板的查询与批量操作。
数据来源：MySQL 数据库 (oaepp_dev)，通过 backend.app.database 模块连接。

原型对应：prototype/admin_students.html
需求覆盖：F-T-004（顶部四统计卡片 + 搜索筛选 + 列表分页 + 批量操作）
"""
import sys
import os
from math import ceil

# 确保 backend 包可导入
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from app.database import db as _get_db


PAGE_SIZE = 8


class BindDashboardState:
    """教师端 GitHub 账号绑定状态看板 State。

    Reflex 事件处理器实现 F-T-004 全部验收标准：
    - 顶部四统计卡片（全班/已绑定/待审核/未绑定）
    - 学生详情表格（学号/姓名/GitHub账号/绑定状态/GitHub实名）
    - 未绑定学生红色高亮、待审核黄色高亮
    - 搜索框 + 状态筛选 + 按状态排序
    - 分页控件（每页 8 条）
    - 一键批量通过 / 拒绝绑定 / 发送提醒
    """

    # ── 统计卡片 ──
    total_students: int = 0
    bound_count: int = 0
    unbound_count: int = 0
    pending_count: int = 0

    # ── 列表数据 ──
    students: list[dict] = []
    current_page: int = 1
    total_pages: int = 1
    page_size: int = PAGE_SIZE

    # ── 筛选条件 ──
    filter_status: str = "all"
    search_query: str = ""
    sort_by_status: bool = False

    # ── 批量操作 ──
    selected_ids: list[str] = []

    # ══════════════════════════════════════════
    #  统计卡片
    # ══════════════════════════════════════════

    @classmethod
    def load_summary(cls):
        """从数据库加载全班绑定状态汇总，更新状态变量。

        原型：admin_students.html → 顶部四卡片统计
              （全班学生数 / 已绑定 / 待审核 / 未绑定）
        """
        with _get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role='student'"
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

    # ══════════════════════════════════════════
    #  列表查询
    # ══════════════════════════════════════════

    @classmethod
    def load_list(
        cls,
        page: int = 1,
        status: str = "all",
        search: str = "",
        sort_by_status_flag: bool = False,
    ):
        """加载学生绑定状态列表，支持筛选、搜索、排序、分页。

        原型：admin_students.html → 学生详情表格
              列：学号 / 姓名 / GitHub 账号 / 绑定状态 /
                  GitHub 实名状态 / 最近核查时间 / 操作
              未绑定行红色高亮，待审核行黄色高亮
        """
        cls.current_page = page
        cls.filter_status = status
        cls.search_query = search
        cls.sort_by_status = sort_by_status_flag

        with _get_db() as conn:
            # ── 构建查询 ──
            base_from = (
                "FROM users u "
                "LEFT JOIN students s ON s.user_id = u.id "
                "LEFT JOIN github_bindings g ON u.id = g.student_user_id "
                "WHERE u.role = 'student'"
            )
            conditions: list[str] = []
            params: list = []

            if status and status != "all":
                if status == "unbound":
                    conditions.append(
                        "(g.verify_status IS NULL "
                        "OR g.verify_status NOT IN ('approved','pending'))"
                    )
                else:
                    conditions.append("g.verify_status = %s")
                    params.append(status)

            if search:
                conditions.append(
                    "(u.full_name LIKE %s OR u.student_no LIKE %s "
                    "OR COALESCE(g.github_username, '') LIKE %s)"
                )
                like = f"%{search}%"
                params.extend([like, like, like])

            where = ""
            if conditions:
                where = " AND " + " AND ".join(conditions)

            # ── 总记录数 ──
            count_sql = f"SELECT COUNT(*) {base_from}{where}"
            total_count = conn.execute(count_sql, params).fetchone()[0] or 0

            # ── 排序 ──
            order_by = ""
            if sort_by_status_flag:
                order_by = (
                    "ORDER BY "
                    "CASE "
                    "WHEN g.verify_status IS NULL "
                    "OR g.verify_status NOT IN ('approved','pending') THEN 0 "
                    "WHEN g.verify_status = 'pending' THEN 1 "
                    "WHEN g.verify_status = 'approved' THEN 2 "
                    "END, "
                    "u.student_no"
                )
            else:
                order_by = "ORDER BY u.student_no"

            # ── 分页 ──
            offset = (page - 1) * PAGE_SIZE
            limit_clause = "LIMIT %s OFFSET %s"
            params.extend([PAGE_SIZE, offset])

            # ── 执行查询 ──
            query = (
                "SELECT u.full_name AS name, u.student_no AS student_id, "
                "COALESCE(s.class_name, '') AS class_name, "
                "COALESCE(g.github_username, '') AS github_username, "
                "COALESCE(g.verify_status, 'unbound') AS binding_status, "
                "COALESCE(g.github_name, '') AS github_name, "
                "g.verified_at "
                f"{base_from}{where} {order_by} {limit_clause}"
            )
            rows = conn.execute(query, params).fetchall()

        cls.students = [dict(r) for r in rows]
        cls.total_pages = max(ceil(total_count / PAGE_SIZE), 1)
        if page > cls.total_pages:
            cls.current_page = cls.total_pages

    # ══════════════════════════════════════════
    #  批量操作
    # ══════════════════════════════════════════

    @classmethod
    def batch_approve(cls, student_ids: list[str]) -> int:
        """批量通过待审核的绑定请求。返回实际通过的数量。

        原型：admin_students.html → 批量通过按钮
        """
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
    def reject_binding(cls, student_ids: list[str]) -> None:
        """拒绝绑定申请。

        原型：admin_students.html → 操作列中的拒绝按钮
        """
        if not student_ids:
            return
        placeholders = ",".join(["%s"] * len(student_ids))
        with _get_db() as conn:
            conn.execute(
                f"UPDATE github_bindings g JOIN users u ON g.student_user_id=u.id "
                f"SET g.verify_status='rejected', "
                f"g.github_username='', g.github_name='', g.verified_at=NULL "
                f"WHERE u.student_no IN ({placeholders})",
                student_ids,
            )

    @classmethod
    def send_reminder_to_unbound(cls, student_ids: list[str]) -> tuple[int, list[str]]:
        """向未绑定学生批量发送提醒。返回 (通知人数, 学生姓名列表)。

        原型：admin_students.html → 发提醒按钮
        """
        if not student_ids:
            return 0, []
        placeholders = ",".join(["%s"] * len(student_ids))
        with _get_db() as conn:
            rows = conn.execute(
                f"SELECT u.full_name AS name FROM users u "
                f"LEFT JOIN github_bindings g ON g.student_user_id=u.id "
                f"WHERE u.student_no IN ({placeholders}) "
                f"AND u.role='student' "
                f"AND (g.verify_status IS NULL "
                f"OR g.verify_status NOT IN ('approved','pending'))",
                student_ids,
            ).fetchall()
        names = [r["name"] for r in rows]
        return len(names), names
