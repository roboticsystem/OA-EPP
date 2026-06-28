"""F-T-013 进度看板 — ProgressBoardState (TDD GREEN)

满足 TDD 测试要求的接口契约，继承并扩展 ProgressState：
- HEATMAP_STATUS: 热力图状态→颜色映射常量
- heatmap_data: 热力图矩阵数据（rx.var → matrix_cells）
- completion_rate_chart: 完成率柱状图数据（rx.var → completion_trend）
- load_progress(): 加载进度数据（→ load_data）
- filter_by_course(): 按课程筛选（→ set_course）
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx

from oaepp.states.progress import ProgressState, STATUS_COLORS


# ── TDD 要求：热力图状态常量 ──
HEATMAP_STATUS: Dict[str, str] = {
    "submitted":     STATUS_COLORS.get("submitted", "#22c55e"),
    "late":          STATUS_COLORS.get("late", "#eab308"),
    "missing":       STATUS_COLORS.get("not_submitted", "#ef4444"),
    "not_published": STATUS_COLORS.get("not_published", "#d1d5db"),
}


class ProgressBoardState(ProgressState):
    """进度看板 State — TDD F-T-013 GREEN

    继承 ProgressState 的全部数据加载与筛选能力，
    额外暴露 TDD 测试要求的命名接口。
    """

    # ── TDD 要求的常量 ──
    HEATMAP_STATUS: Dict[str, str] = HEATMAP_STATUS

    # ── TDD 要求的属性别名（rx.var 计算属性） ──

    @rx.var
    def heatmap_data(self) -> List[Dict[str, Any]]:
        """TDD 别名 — 热力图矩阵数据（指向 matrix_cells）。"""
        return self.matrix_cells

    @rx.var
    def completion_rate_chart(self) -> List[Dict[str, Any]]:
        """TDD 别名 — 完成率柱状图数据（指向 completion_trend）。"""
        return self.completion_trend

    # ── TDD 要求的方法别名 ──

    def load_progress(self):
        """TDD 别名 — 加载进度看板数据。"""
        return self.load_data()

    def filter_by_course(self, course_id_str: str = ""):
        """TDD 别名 — 按课程筛选。"""
        return self.set_course(course_id_str)
