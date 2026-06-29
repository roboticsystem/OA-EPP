"""F-T-013 进度看板 — ProgressState

以热力图与柱状图展示全班「学生 × 任务」二维完成状态矩阵，
帮助教师快速识别进度落后的学生与完成率偏低的任务。
数据基于 Reflex State 自动刷新（JS 轮询 + 手动刷新）。

数据库：enrollments / assignments / submissions / users / students / courses
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import reflex as rx

from oaepp.database import db_sync

logger = logging.getLogger("oaepp.states.progress")

# ── 颜色映射 ────────────────────────────────────────────────────
STATUS_COLORS: Dict[str, str] = {
    "submitted":     "#22c55e",   # 绿 — 已按时提交
    "late":          "#eab308",   # 黄 — 迟交
    "not_submitted": "#ef4444",   # 红 — 未提交（已截止）
    "not_published": "#d1d5db",   # 灰 — 任务未发布 / 未截止
}

STATUS_LABELS: Dict[str, str] = {
    "submitted":     "已提交",
    "late":          "迟交",
    "not_submitted": "未提交",
    "not_published": "未发布",
}

_STATUS_EMOJI: Dict[str, str] = {
    "submitted":     "✓",
    "late":          "⚠",
    "not_submitted": "✗",
    "not_published": "·",
}


class ProgressState(rx.State):
    """进度看板 — 教师端统计分析"""

    # ── 筛选条件 ────────────────────────────────────────────────
    available_courses: List[Dict[str, Any]] = []
    selected_course_id: int = 0
    selected_term: str = ""  # 学期筛选（可为空，表示全部）
    bottom_n: int = 5         # 完成率最低前 N 名置顶高亮

    # ── 热力图数据 ──────────────────────────────────────────────
    students: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    matrix_cells: List[Dict[str, Any]] = []

    # ── 柱状图数据 ──────────────────────────────────────────────
    completion_trend: List[Dict[str, Any]] = []

    # ── 提交详情弹窗 ────────────────────────────────────────────
    detail_open: bool = False
    detail_data: Dict[str, Any] = {}

    # ── UI 状态 ─────────────────────────────────────────────────
    loading: bool = True
    error: str = ""
    last_refresh: str = ""
    # 概览统计（使用独立变量以兼容 Reflex 模板编译）
    summary_total_students: int = 0
    summary_total_assignments: int = 0
    summary_total_submissions: int = 0
    summary_overall_rate: float = 0.0

    # ── 课程选择 UI 辅助 ─────────────────────────────────────────
    selected_course_label: str = ""  # 当前选中课程的标签（用于 select 组件展示）

    # ── 计算属性 ────────────────────────────────────────────────

    @rx.var
    def has_data(self) -> bool:
        return bool(self.students and self.assignments)

    @rx.var
    def has_error(self) -> bool:
        return bool(self.error)

    @rx.var
    def course_labels(self) -> List[str]:
        """课程下拉选项标签列表。"""
        return [
            f"{c.get('code','')} — {c.get('term','')}"
            for c in self.available_courses
        ]

    @rx.var
    def heatmap_rows(self) -> List[Dict[str, Any]]:
        """热力图行数据（预计算，供模板直接渲染）。

        每行包含学生信息 + 该学生所有任务单元格的状态数据。
        按完成率升序排列，前 bottom_n 名标记 is_highlight。
        """
        rows: List[Dict[str, Any]] = []
        if not self.students or not self.assignments:
            return rows

        for idx, s in enumerate(self.students):
            cells: List[Dict[str, Any]] = []
            for a in self.assignments:
                cell = next(
                    (
                        c
                        for c in self.matrix_cells
                        if c["student_id"] == s["user_id"]
                        and c["assignment_id"] == a["id"]
                    ),
                    None,
                )
                status = cell["status"] if cell else "not_published"
                cells.append(
                    {
                        "student_id": s["user_id"],
                        "assignment_id": a["id"],
                        "status": status,
                        "color": STATUS_COLORS.get(status, "#d1d5db"),
                        "emoji": _STATUS_EMOJI.get(status, "·"),
                        "label": STATUS_LABELS.get(status, "未发布"),
                        "tooltip": (
                            f"{s.get('full_name','')} — {a.get('title','')}: "
                            f"{STATUS_LABELS.get(status, status)}"
                        ),
                        "submission_id": cell.get("submission_id") if cell else None,
                    }
                )
            rows.append(
                {
                    "student": s,
                    "cells": cells,
                    "is_highlight": idx < self.bottom_n,
                }
            )
        return rows

    # ── 事件处理器 ──────────────────────────────────────────────

    def on_mount(self):
        """页面挂载时加载课程列表和初始数据。"""
        return self.load_courses()

    def load_courses(self):
        """加载可选课程列表，并自动选中第一个加载数据。"""
        self.loading = True
        self.error = ""
        yield

        try:
            with db_sync() as cur:
                cur.execute(
                    "SELECT id, code, name, term FROM courses "
                    "WHERE status = 'open' ORDER BY term DESC, code"
                )
                rows = cur.fetchall()
        except Exception as e:
            logger.error("加载课程列表失败: %s", e)
            self.error = f"数据库连接失败: {e}"
            self.loading = False
            return

        self.available_courses = [dict(r) for r in rows]
        if self.available_courses and self.selected_course_id <= 0:
            self.selected_course_id = self.available_courses[0]["id"]
        if self.selected_course_id > 0:
            return self.load_data()

        self.loading = False
        self.error = "暂无可用课程数据"

    def set_course(self, course_id_str: str):
        """切换课程后重新加载看板数据。"""
        try:
            self.selected_course_id = int(course_id_str) if course_id_str else 0
        except (ValueError, TypeError):
            self.selected_course_id = 0
        # 更新标签
        self.selected_course_label = self._label_for_id(self.selected_course_id)
        return self.load_data()

    def select_course_by_label(self, label: str):
        """根据课程标签（如 "CS2026-PYTHON — 2026-春"）选择课程。"""
        self.selected_course_label = label
        for c in self.available_courses:
            c_label = f"{c.get('code','')} — {c.get('term','')}"
            if c_label == label:
                self.selected_course_id = c["id"]
                return self.load_data()
        # 如果没匹配到，尝试直接解析
        if label and self.available_courses:
            self.selected_course_id = self.available_courses[0]["id"]
            return self.load_data()
        return ProgressState.load_data  # 不触发重新加载

    def _label_for_id(self, course_id: int) -> str:
        """根据课程 ID 返回对应的标签。"""
        for c in self.available_courses:
            if c["id"] == course_id:
                return f"{c.get('code','')} — {c.get('term','')}"
        return ""

    def set_term(self, term: str):
        """按学期筛选。"""
        self.selected_term = term
        return self.load_data()

    def set_bottom_n_str(self, n_str: str):
        """设置底部高亮人数（从输入框字符串解析）。"""
        try:
            n = int(n_str)
            self.bottom_n = max(1, min(20, n))
        except (ValueError, TypeError):
            self.bottom_n = 5
        return self.load_data()

    def manual_refresh(self):
        """手动刷新数据。"""
        return self.load_data()

    def load_data(self):
        """核心数据加载：学生列表 + 作业列表 + 提交矩阵 + 完成率趋势。"""
        if self.available_courses:
            course_id = self.selected_course_id or self.available_courses[0]["id"]
        else:
            self.loading = False
            self.error = "暂无可用课程"
            return

        self.selected_course_id = course_id
        self.selected_course_label = self._label_for_id(course_id)
        self.loading = True
        self.error = ""
        yield

        term_filter = (self.selected_term or "").strip()

        try:
            with db_sync() as cur:
                # ── 1. 加载作业列表 ──
                cur.execute(
                    "SELECT id, title, deadline, created_at FROM assignments "
                    "WHERE course_id = %s ORDER BY deadline ASC, id ASC",
                    (course_id,),
                )
                raw_assignments = cur.fetchall()
                self.assignments = []
                for a in raw_assignments:
                    d = dict(a)
                    if d.get("deadline"):
                        d["deadline"] = self._fmt_dt(d["deadline"])
                    if d.get("created_at"):
                        d["created_at"] = self._fmt_dt(d["created_at"])
                    self.assignments.append(d)

                if not self.assignments:
                    self.students, self.matrix_cells, self.completion_trend = [], [], []
                    self.summary_total_students = 0
                    self.summary_total_assignments = 0
                    self.summary_total_submissions = 0
                    self.summary_overall_rate = 0.0
                    self.last_refresh = datetime.now().strftime("%H:%M:%S")
                    self.loading = False
                    return

                assignment_ids = [a["id"] for a in self.assignments]

                # ── 2. 加载选课学生（含学期筛选） ──
                if term_filter:
                    cur.execute(
                        "SELECT u.id AS user_id, u.student_no, u.full_name, s.class_name "
                        "FROM enrollments e "
                        "JOIN users u ON u.id = e.student_user_id AND u.role = 'student' "
                        "JOIN students s ON s.user_id = u.id "
                        "JOIN courses c ON c.id = e.course_id "
                        "WHERE e.course_id = %s AND c.term = %s "
                        "ORDER BY u.full_name",
                        (course_id, term_filter),
                    )
                else:
                    cur.execute(
                        "SELECT u.id AS user_id, u.student_no, u.full_name, s.class_name "
                        "FROM enrollments e "
                        "JOIN users u ON u.id = e.student_user_id AND u.role = 'student' "
                        "JOIN students s ON s.user_id = u.id "
                        "WHERE e.course_id = %s "
                        "ORDER BY u.full_name",
                        (course_id,),
                    )
                self.students = [dict(r) for r in cur.fetchall()]

                if not self.students:
                    self.matrix_cells, self.completion_trend = [], []
                    self.summary_total_students = 0
                    self.summary_total_assignments = len(self.assignments)
                    self.summary_total_submissions = 0
                    self.summary_overall_rate = 0.0
                    self.last_refresh = datetime.now().strftime("%H:%M:%S")
                    self.loading = False
                    return

                # ── 3. 加载所有提交（只取每个学生×作业的最新版本） ──
                student_ids = [s["user_id"] for s in self.students]
                sub_lookup: Dict[str, Dict] = {}
                if student_ids and assignment_ids:
                    cur.execute(
                        self._build_submission_sql(len(assignment_ids), len(student_ids)),
                        assignment_ids + student_ids + assignment_ids + student_ids,
                    )
                    for row in cur.fetchall():
                        r = dict(row)
                        key = f"{r['student_user_id']}_{r['assignment_id']}"
                        if r.get("submitted_at"):
                            r["submitted_at"] = self._fmt_dt(r["submitted_at"])
                        sub_lookup[key] = r

                # ── 4. 构建矩阵 & 统计 ──
                now = datetime.now()
                self.matrix_cells = []
                student_stats: List[Dict] = []
                asgn_stats: Dict[int, Dict] = {}

                for a in self.assignments:
                    asgn_stats[a["id"]] = {"submitted": 0, "late": 0}

                for s in self.students:
                    sid = s["user_id"]
                    sub_count = 0
                    total = len(self.assignments)
                    late_count = 0
                    for a in self.assignments:
                        aid = a["id"]
                        key = f"{sid}_{aid}"
                        sub = sub_lookup.get(key)
                        status = self._classify(sub, a.get("deadline"), now)

                        cell = {
                            "student_id": sid,
                            "assignment_id": aid,
                            "status": status,
                            "color": STATUS_COLORS.get(status, "#d1d5db"),
                            "submission_id": sub.get("submission_id") if sub else None,
                            "version_no": sub.get("version_no") if sub else None,
                            "submitted_at": sub.get("submitted_at") if sub else "",
                            "is_late": bool(sub.get("is_late")) if sub else False,
                            "grading_status": sub.get("grading_status") if sub else "",
                        }
                        self.matrix_cells.append(cell)

                        if status in ("submitted", "late"):
                            sub_count += 1
                            asgn_stats[aid]["submitted"] += 1
                        if status == "late":
                            late_count += 1
                            asgn_stats[aid]["late"] += 1

                    rate = round(sub_count / total * 100, 1) if total > 0 else 0.0
                    s["completion_rate"] = rate
                    s["submission_count"] = sub_count
                    s["total_count"] = total
                    s["late_count"] = late_count
                    s["is_highlight"] = False
                    student_stats.append(s)

                # 按完成率升序 → 最低排前面
                student_stats.sort(key=lambda x: x["completion_rate"])
                # 前 bottom_n 名高亮
                for i in range(min(self.bottom_n, len(student_stats))):
                    student_stats[i]["is_highlight"] = True
                self.students = student_stats

                # 统计概览
                total_subs = sum(a["submitted"] for a in asgn_stats.values())
                total_cells = len(self.students) * len(self.assignments)
                self.summary_total_students = len(self.students)
                self.summary_total_assignments = len(self.assignments)
                self.summary_total_submissions = total_subs
                self.summary_overall_rate = (
                    round(total_subs / total_cells * 100, 1) if total_cells else 0.0
                )

                # ── 5. 柱状图数据 ──
                self.completion_trend = []
                total_stu = len(self.students)
                for a in self.assignments:
                    aid = a["id"]
                    st = asgn_stats.get(aid, {"submitted": 0, "late": 0})
                    rate = round(st["submitted"] / total_stu * 100, 1) if total_stu else 0
                    self.completion_trend.append({
                        "assignment_id": aid,
                        "label": a.get("title", f"任务{aid}"),
                        "rate": rate,
                        "submitted": st["submitted"],
                        "late": st["late"],
                        "total": total_stu,
                        "deadline": a.get("deadline", ""),
                    })

                self.last_refresh = datetime.now().strftime("%H:%M:%S")
                self.error = ""

        except Exception as e:
            logger.exception("加载进度看板数据失败")
            self.error = f"数据加载失败: {e}"
            self.students, self.assignments, self.matrix_cells = [], [], []
            self.completion_trend = []
            self.summary_total_students = 0
            self.summary_total_assignments = 0
            self.summary_total_submissions = 0
            self.summary_overall_rate = 0.0

        self.loading = False

    # ── 提交详情弹窗 ────────────────────────────────────────────

    def show_cell_detail(self, sid: int = 0, aid: int = 0):
        """点击热力图单元格 → 弹出提交详情。"""
        sid, aid = int(sid), int(aid)
        if not sid or not aid:
            self.detail_open = False
            self.detail_data = {}
            return

        row = next((s for s in self.students if s["user_id"] == sid), None)
        col = next((a for a in self.assignments if a["id"] == aid), None)
        cell = next(
            (c for c in self.matrix_cells
             if c["student_id"] == sid and c["assignment_id"] == aid),
            None,
        )

        self.detail_data = {
            "student_name": row.get("full_name", "") if row else "",
            "student_no": row.get("student_no", "") if row else "",
            "class_name": row.get("class_name", "") if row else "",
            "assignment_title": col.get("title", "") if col else "",
            "assignment_deadline": col.get("deadline", "") if col else "",
            "status_label": STATUS_LABELS.get(cell["status"], cell["status"]) if cell else "未知",
            "status_color": cell.get("color", "#d1d5db") if cell else "#d1d5db",
            "submission_id": cell.get("submission_id") if cell else None,
            "version_no": cell.get("version_no", "-") if cell else "-",
            "submitted_at": cell.get("submitted_at", "无提交记录") if cell else "无提交记录",
            "is_late": cell.get("is_late", False) if cell else False,
            "grading_status": cell.get("grading_status", "-") if cell else "-",
        }
        self.detail_open = True

    def close_detail(self):
        """关闭提交详情弹窗。"""
        self.detail_open = False
        self.detail_data = {}

    # ── 静态辅助方法 ────────────────────────────────────────────

    @staticmethod
    def _classify(sub: Optional[Dict], deadline: Any, now: datetime) -> str:
        """根据提交记录和截止时间判断状态。

        - 已提交且未迟到 → submitted（绿）
        - 已提交但迟到   → late（黄）
        - 未提交 & 已截止 → not_submitted（红）
        - 未提交 & 未截止 → not_published（灰）
        """
        if sub:
            if sub.get("is_late"):
                return "late"
            return "submitted"
        if deadline:
            try:
                dl = datetime.fromisoformat(str(deadline)) if isinstance(deadline, str) else deadline
                if now > dl:
                    return "not_submitted"
            except (ValueError, TypeError):
                pass
        return "not_published"

    @staticmethod
    def _build_submission_sql(n_assignments: int, n_students: int) -> str:
        """构建获取最新提交的 SQL（带参数占位符）。"""
        a_phs = ",".join(["%s"] * n_assignments)
        s_phs = ",".join(["%s"] * n_students)
        return (
            f"SELECT s.assignment_id, s.student_user_id, s.id AS submission_id, "
            f"s.version_no, s.is_late, s.grading_status, s.submitted_at "
            f"FROM submissions s "
            f"WHERE s.assignment_id IN ({a_phs}) "
            f"AND s.student_user_id IN ({s_phs}) "
            f"AND s.id = ("
            f"  SELECT MAX(id) FROM submissions "
            f"  WHERE assignment_id = s.assignment_id "
            f"    AND student_user_id = s.student_user_id"
            f")"
        )

    @staticmethod
    def _fmt_dt(val: Any) -> str:
        """安全地将数据库时间对象转为 ISO 字符串。"""
        if val is None:
            return ""
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)
