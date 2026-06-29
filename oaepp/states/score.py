"""F-S-030 成绩统计 — ScoreState（Reflex State）

提供成绩看板的状态管理，通过 ORM（rx.session()）查询数据库。
对齐原型 prototype/grades.html：
- 顶部四维度得分卡片
- 详情标签页（代码评阅/考试成绩/出勤记录/时间线）
"""
from typing import Any, List, Optional
import reflex as rx


class ScoreState(rx.State):
    """成绩统计状态管理

    对齐 prototype/grades.html 原型：
    - 顶部四维度得分卡片：出勤/考试/代码/PR
    - 详情标签页：代码评阅/考试成绩/出勤记录/时间线
    """

    # ── 四维度得分 ──
    attendance_score: float = 0.0
    exam_score: float = 0.0
    code_score: float = 0.0
    pr_score: float = 0.0
    total_score: float = 0.0

    # ── 满分基准 ──
    attendance_total: float = 20.0
    exam_total: float = 30.0
    code_total: float = 40.0
    pr_total: float = 10.0

    # ── 当前用户 ──
    current_student_id: str = ""
    current_student_name: str = ""
    current_student_class: str = ""

    # ── 成绩详情 ──
    score_breakdown: List[dict] = []
    exam_records: List[dict] = []

    # ── 加载状态 ──
    is_loading: bool = False

    @rx.var
    def title_text(self) -> str:
        return f"工程实践 4 · 综合总分 {self.total_score:g} / 100"

    def on_load(self):
        """页面加载时自动执行，从 GlobalState 获取当前学号。"""
        # TODO: 集成认证后从 GlobalState.current_user 获取学号
        self.load_scores("2021001001")

    def load_scores(self, student_no: str = ""):
        """加载当前学生各维度成绩。

        使用 ORM 查询 score_items 表按维度汇总，
        从 grading_records 获取评阅详情。
        """
        if student_no:
            self.current_student_id = student_no
        if not self.current_student_id:
            return

        self.is_loading = True

        try:
            with rx.session() as session:
                from sqlmodel import text

                # 1) 查找学生 user_id 和基本信息
                result = session.execute(
                    text(
                        "SELECT u.id, u.full_name, s.class_name "
                        "FROM users u "
                        "LEFT JOIN students s ON s.user_id = u.id "
                        "WHERE u.student_no = :sno AND u.role = 'student'"
                    ),
                    {"sno": self.current_student_id},
                )
                user_row = result.fetchone()
                if not user_row:
                    self.is_loading = False
                    return
                user_id = user_row[0]
                self.current_student_name = user_row[1] or ""
                self.current_student_class = user_row[2] or ""

                # 2) 按维度汇总 score_items
                result = session.execute(
                    text(
                        "SELECT score_type, SUM(score) AS total_score "
                        "FROM score_items "
                        "WHERE student_user_id = :uid "
                        "GROUP BY score_type"
                    ),
                    {"uid": user_id},
                )
                for row in result.fetchall():
                    stype = row[0]
                    val = float(row[1]) if row[1] else 0.0
                    if stype == "attendance":
                        self.attendance_score = min(val, self.attendance_total)
                    elif stype == "exam":
                        self.exam_score = min(val, self.exam_total)
                    elif stype == "code":
                        self.code_score = min(val, self.code_total)
                    elif stype == "pr":
                        self.pr_score = min(val, self.pr_total)

                self.total_score = (
                    self.attendance_score + self.exam_score
                    + self.code_score + self.pr_score
                )

                # 3) 获取评阅详情（grading_records）
                result = session.execute(
                    text(
                        "SELECT "
                        "gr.total_score, gr.graded_at, "
                        "a.title AS assignment_title, "
                        "u2.full_name AS grader_name, "
                        "s.version_no, s.is_late "
                        "FROM grading_records gr "
                        "JOIN submissions s ON s.id = gr.submission_id "
                        "JOIN assignments a ON a.id = s.assignment_id "
                        "JOIN users u2 ON u2.id = gr.graded_by "
                        "WHERE s.student_user_id = :uid "
                        "ORDER BY gr.graded_at DESC"
                    ),
                    {"uid": user_id},
                )
                self.score_breakdown = []
                for row in result.fetchall():
                    sc = float(row[0]) if row[0] else 0.0
                    has_sc = sc > 0
                    self.score_breakdown.append({
                        "assignment_title": row[2] or "",
                        "graded_at": str(row[1]) if row[1] else "",
                        "grader_name": row[3] or "教师",
                        # 预计算展示字段（避免在渲染函数中对 Var 做 Python 运算）
                        "score_text": f"{sc:g}/10" if has_sc else "—",
                        "score_color": "var(--green-9)" if (has_sc and sc >= 7) else
                                       "var(--orange-9)" if (has_sc and sc >= 5) else
                                       "var(--red-9)" if has_sc else "var(--gray-8)",
                        "status_text": "已批改" if has_sc else "待批改",
                        "status_bg": "var(--green-3)" if has_sc else "var(--yellow-3)",
                        "status_fg": "var(--green-9)" if has_sc else "var(--yellow-9)",
                        "has_score": has_sc,
                    })

                # 4) 获取考试成绩
                result = session.execute(
                    text(
                        "SELECT e.title, ea.score, ea.total, ea.submitted_at "
                        "FROM exam_attempts ea "
                        "JOIN exams e ON e.id = ea.exam_id "
                        "WHERE ea.student_user_id = :uid "
                        "ORDER BY ea.submitted_at DESC"
                    ),
                    {"uid": user_id},
                )
                self.exam_records = []
                for row in result.fetchall():
                    self.exam_records.append({
                        "title": row[0] or "",
                        "score": float(row[1]) if row[1] else 0.0,
                        "total": float(row[2]) if row[2] else 0.0,
                        "submitted_at": str(row[3]) if row[3] else "",
                    })

        except Exception as e:
            print(f"[ScoreState] 加载成绩失败: {e}")

        self.is_loading = False
