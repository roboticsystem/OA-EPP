"""F-S-040 得分看板与可视化 — 学生端 State

提供学生个人得分看板的全部数据：
  - 四维度雷达图（出勤/考试/代码/PR）
  - 历次考试柱状图
  - 全期总分折线图
  - 任务完成率与即将到期任务
  - 按工程实践 1-4 课程筛选

需求对齐：
  - F-S-040 得分看板与可视化
  - 雷达图展示出勤/考试/代码/PR 四维度得分
  - 柱状图展示各次考试历史趋势
  - 折线图展示全期总得分时间曲线
  - 展示任务完成率和即将到期任务
  - 支持按工程实践 1-4 筛选
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

import reflex as rx

from oaepp.database import db_sync

logger = logging.getLogger("oaepp.states.score_dashboard")

# ── 四维度定义 ──────────────────────────────────────────────────
RADAR_DIMENSIONS = ["出勤", "考试", "代码", "PR"]

DIMENSION_COLORS: Dict[str, str] = {
    "attendance": "#22c55e",  # 绿 — 出勤
    "exam":       "#a855f7",  # 紫 — 考试
    "code":       "#f97316",  # 橙 — 代码
    "pr":         "#3b82f6",  # 蓝 — PR
}

DIMENSION_LABELS: Dict[str, str] = {
    "attendance": "出勤",
    "exam":       "考试",
    "code":       "代码",
    "pr":         "PR",
}

# 各维度满分（默认值，可由 grade_weight_configs 覆写）
DEFAULT_MAX_SCORES: Dict[str, float] = {
    "attendance": 20.0,
    "exam":       30.0,
    "code":       30.0,
    "pr":         20.0,
}


class ScoreDashboardState(rx.State):
    """学生得分看板 — 个人成绩可视化"""

    # ── 课程筛选 ────────────────────────────────────────────────
    available_courses: List[Dict[str, Any]] = []
    selected_course_id: int = 0
    selected_course_label: str = ""

    # ── 学生信息 ────────────────────────────────────────────────
    student_no: str = ""
    student_user_id: int = 0
    student_name: str = ""

    # ── 雷达图数据（四维度得分） ────────────────────────────────
    radar_data: List[Dict[str, Any]] = []

    # ── 柱状图数据（历次考试得分） ──────────────────────────────
    exam_history: List[Dict[str, Any]] = []

    # ── 折线图数据（全期总得分趋势） ────────────────────────────
    total_score_trend: List[Dict[str, Any]] = []

    # ── 任务完成率 ──────────────────────────────────────────────
    completion_rate: float = 0.0
    completed_count: int = 0
    total_tasks: int = 0

    # ── 即将到期任务 ────────────────────────────────────────────
    upcoming_deadlines: List[Dict[str, Any]] = []

    # ── UI 状态 ─────────────────────────────────────────────────
    loading: bool = True
    error: str = ""

    # ── 课程选择 UI 辅助 ─────────────────────────────────────────

    @rx.var
    def course_labels(self) -> List[str]:
        """课程下拉选项标签列表。"""
        return [
            f"{c.get('code', '')} — {c.get('term', '')}"
            for c in self.available_courses
        ]

    @rx.var
    def has_data(self) -> bool:
        """是否有数据可展示。"""
        return bool(self.radar_data or self.exam_history)

    @rx.var
    def has_error(self) -> bool:
        return bool(self.error)

    # ── 计算属性：四维度得分汇总 ─────────────────────────────────

    @rx.var
    def attendance_score(self) -> float:
        """出勤得分。"""
        for d in self.radar_data:
            if d.get("dimension") == "出勤":
                return float(d.get("score", 0))
        return 0.0

    @rx.var
    def exam_score(self) -> float:
        """考试得分。"""
        for d in self.radar_data:
            if d.get("dimension") == "考试":
                return float(d.get("score", 0))
        return 0.0

    @rx.var
    def code_score(self) -> float:
        """代码得分。"""
        for d in self.radar_data:
            if d.get("dimension") == "代码":
                return float(d.get("score", 0))
        return 0.0

    @rx.var
    def pr_score(self) -> float:
        """PR 得分。"""
        for d in self.radar_data:
            if d.get("dimension") == "PR":
                return float(d.get("score", 0))
        return 0.0

    @rx.var
    def total_score(self) -> float:
        """综合总分。"""
        return round(
            self.attendance_score + self.exam_score
            + self.code_score + self.pr_score, 1
        )

    @rx.var
    def attendance_max(self) -> float:
        for d in self.radar_data:
            if d.get("dimension") == "出勤":
                return float(d.get("max_score", 20))
        return 20.0

    @rx.var
    def exam_max(self) -> float:
        for d in self.radar_data:
            if d.get("dimension") == "考试":
                return float(d.get("max_score", 30))
        return 30.0

    @rx.var
    def code_max(self) -> float:
        for d in self.radar_data:
            if d.get("dimension") == "代码":
                return float(d.get("max_score", 30))
        return 30.0

    @rx.var
    def pr_max(self) -> float:
        for d in self.radar_data:
            if d.get("dimension") == "PR":
                return float(d.get("max_score", 20))
        return 20.0

    # ── 事件处理器 ──────────────────────────────────────────────

    def on_mount(self):
        """页面挂载时加载课程列表和初始数据。"""
        # 尝试从 GlobalState 获取当前登录学生信息
        try:
            gs = self.get_state(
                __import__("oaepp.states", fromlist=["GlobalState"]).GlobalState
            )
        except Exception:
            gs = None

        if gs is not None and hasattr(gs, "current_user"):
            user = gs.current_user or {}
            self.student_no = user.get("student_no", "")
            self.student_name = user.get("full_name", "")

        return self.load_courses()

    def load_courses(self):
        """加载可选课程列表（工程实践1-4）。"""
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

        # 查找当前学生 user_id
        if self.student_no:
            try:
                with db_sync() as cur:
                    cur.execute(
                        "SELECT id, full_name FROM users "
                        "WHERE student_no = %s AND role = 'student'",
                        (self.student_no,)
                    )
                    user_row = cur.fetchone()
                    if user_row:
                        self.student_user_id = user_row["id"]
                        if not self.student_name:
                            self.student_name = user_row.get("full_name", "")
            except Exception as e:
                logger.warning("查找学生用户失败: %s", e)

        # 自动选中第一个课程
        if self.available_courses and self.selected_course_id <= 0:
            self.selected_course_id = self.available_courses[0]["id"]
            self.selected_course_label = (
                f"{self.available_courses[0].get('code','')} — "
                f"{self.available_courses[0].get('term','')}"
            )

        if self.selected_course_id > 0:
            return self.load_dashboard()

        self.loading = False
        self.error = "暂无可用课程数据"

    def select_course_by_label(self, label: str):
        """根据课程标签（如 "EP4 — 2026-春"）选择课程。"""
        self.selected_course_label = label
        for c in self.available_courses:
            c_label = f"{c.get('code','')} — {c.get('term','')}"
            if c_label == label:
                self.selected_course_id = c["id"]
                return self.load_dashboard()
        # 未匹配时默认使用第一个
        if label and self.available_courses:
            self.selected_course_id = self.available_courses[0]["id"]
            return self.load_dashboard()

    def _label_for_id(self, course_id: int) -> str:
        """根据课程 ID 返回对应的标签。"""
        for c in self.available_courses:
            if c["id"] == course_id:
                return f"{c.get('code','')} — {c.get('term','')}"
        return ""

    def load_dashboard(self):
        """核心数据加载：雷达图 + 柱状图 + 折线图 + 任务完成率 + 即将到期。"""
        course_id = self.selected_course_id
        if not course_id or not self.available_courses:
            course_id = self.available_courses[0]["id"] if self.available_courses else 0
            self.selected_course_id = course_id

        if not course_id:
            self.loading = False
            self.error = "请先选择课程"
            return

        self.selected_course_label = self._label_for_id(course_id)
        self.loading = True
        self.error = ""
        yield

        uid = self.student_user_id

        try:
            with db_sync() as cur:
                # ── 1. 加载权重配置 & 四维度得分 ──
                cur.execute(
                    "SELECT attendance_weight, exam_weight, code_weight, pr_weight "
                    "FROM grade_weight_configs WHERE course_id = %s",
                    (course_id,)
                )
                weight_row = cur.fetchone()

                max_scores = dict(DEFAULT_MAX_SCORES)
                if weight_row:
                    w = dict(weight_row)
                    max_scores["attendance"] = float(w.get("attendance_weight", 20))
                    max_scores["exam"] = float(w.get("exam_weight", 30))
                    max_scores["code"] = float(w.get("code_weight", 30))
                    max_scores["pr"] = float(w.get("pr_weight", 20))

                # 查询四维度得分
                radar_data = []
                for score_type in ["attendance", "exam", "code", "pr"]:
                    if uid:
                        cur.execute(
                            "SELECT score FROM score_items "
                            "WHERE course_id = %s AND student_user_id = %s "
                            "AND score_type = %s "
                            "ORDER BY scored_at DESC LIMIT 1",
                            (course_id, uid, score_type)
                        )
                        row = cur.fetchone()
                        score_val = float(row["score"]) if row else 0.0
                    else:
                        score_val = 0.0

                    radar_data.append({
                        "dimension": DIMENSION_LABELS.get(score_type, score_type),
                        "score": score_val,
                        "max_score": max_scores.get(score_type, 20.0),
                        "color": DIMENSION_COLORS.get(score_type, "#6b7280"),
                    })
                self.radar_data = radar_data

                # ── 2. 历次考试得分（柱状图） ──
                exam_history = []
                if uid:
                    cur.execute(
                        "SELECT e.title AS exam_title, ea.total_score, "
                        "ea.submitted_at, e.exam_type "
                        "FROM exam_attempts ea "
                        "JOIN exams e ON e.id = ea.exam_id "
                        "WHERE e.course_id = %s AND ea.student_user_id = %s "
                        "AND ea.status = 'graded' "
                        "ORDER BY ea.submitted_at ASC",
                        (course_id, uid)
                    )
                    for row in cur.fetchall():
                        r = dict(row)
                        exam_history.append({
                            "exam_title": r.get("exam_title", ""),
                            "score": float(r.get("total_score", 0) or 0),
                            "submitted_at": self._fmt_dt(r.get("submitted_at")),
                            "exam_type": r.get("exam_type", ""),
                        })
                self.exam_history = exam_history

                # ── 3. 全期总得分趋势（折线图） ──
                total_score_trend = []
                if uid:
                    cur.execute(
                        "SELECT scored_at, score, score_type "
                        "FROM score_items "
                        "WHERE course_id = %s AND student_user_id = %s "
                        "ORDER BY scored_at ASC",
                        (course_id, uid)
                    )
                    rows = cur.fetchall()
                    cumulative = 0.0
                    for row in rows:
                        r = dict(row)
                        cumulative += float(r.get("score", 0) or 0)
                        total_score_trend.append({
                            "date": self._fmt_dt(r.get("scored_at"), date_only=True),
                            "score": round(cumulative, 1),
                            "score_type": r.get("score_type", ""),
                        })
                self.total_score_trend = total_score_trend

                # ── 4. 任务完成率 ──
                completed_count = 0
                total_tasks = 0
                if uid:
                    cur.execute(
                        "SELECT COUNT(*) AS cnt FROM assignments "
                        "WHERE course_id = %s",
                        (course_id,)
                    )
                    total_tasks = cur.fetchone()["cnt"]

                    cur.execute(
                        "SELECT COUNT(DISTINCT a.id) AS cnt "
                        "FROM assignments a "
                        "JOIN submissions s ON s.assignment_id = a.id "
                        "WHERE a.course_id = %s AND s.student_user_id = %s",
                        (course_id, uid)
                    )
                    completed_count = cur.fetchone()["cnt"]

                self.total_tasks = total_tasks
                self.completed_count = completed_count
                self.completion_rate = (
                    round(completed_count / total_tasks * 100, 1)
                    if total_tasks > 0 else 0.0
                )

                # ── 5. 即将到期任务 ──
                upcoming = []
                if uid:
                    now = datetime.now()
                    cur.execute(
                        "SELECT a.id, a.title, a.deadline, "
                        "CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS has_submitted "
                        "FROM assignments a "
                        "LEFT JOIN submissions s ON s.assignment_id = a.id "
                        "AND s.student_user_id = %s "
                        "WHERE a.course_id = %s AND a.deadline > %s "
                        "ORDER BY a.deadline ASC LIMIT 5",
                        (uid, course_id, now)
                    )
                    for row in cur.fetchall():
                        r = dict(row)
                        dl = r.get("deadline")
                        days_left = ""
                        if dl:
                            if isinstance(dl, datetime):
                                delta = dl - now
                                d = delta.days
                                days_left = f"剩余 {d} 天" if d >= 0 else "已截止"
                            else:
                                days_left = str(dl)[:10]
                        upcoming.append({
                            "id": r["id"],
                            "title": r.get("title", ""),
                            "deadline": self._fmt_dt(dl),
                            "days_left": days_left,
                            "has_submitted": bool(r.get("has_submitted")),
                        })
                self.upcoming_deadlines = upcoming

                self.error = ""

        except Exception as e:
            logger.exception("加载得分看板数据失败")
            self.error = f"数据加载失败: {e}"
            self.radar_data = []
            self.exam_history = []
            self.total_score_trend = []
            self.completion_rate = 0.0
            self.completed_count = 0
            self.total_tasks = 0
            self.upcoming_deadlines = []

        self.loading = False

    # ── 静态辅助方法 ────────────────────────────────────────────

    @staticmethod
    def _fmt_dt(val: Any, date_only: bool = False) -> str:
        """安全地将数据库时间对象转为字符串。"""
        if val is None:
            return ""
        if isinstance(val, datetime):
            if date_only:
                return val.strftime("%Y-%m-%d")
            return val.strftime("%Y-%m-%d %H:%M")
        return str(val)[:19] if not date_only else str(val)[:10]
