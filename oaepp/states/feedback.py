"""F-S-031 评语反馈 — FeedbackState（Reflex State）

提供教师评语和反馈的状态管理，通过 ORM（rx.session()）查询数据库。

验收标准：
- 每次评阅结果展示教师评语和扣分项
- 改进建议以条目形式展示
- 允许二次提交的任务展示重新提交入口
"""
import re
from typing import Any, List, Optional
import reflex as rx


class FeedbackState(rx.State):
    """评语反馈状态管理

    对齐验收标准：
    - 展示教师评语和扣分项
    - 改进建议以条目形式展示
    - 允许二次提交时显示"前往重新提交"入口
    """

    # ── 核心状态 ──
    feedbacks: List[dict] = []
    current_feedback: Optional[dict] = None
    allow_resubmit: bool = False

    # ── 学生信息 ──
    current_student_id: str = ""

    # ── 加载状态 ──
    is_loading: bool = False

    @staticmethod
    def _parse_comment_md(comment_md: str) -> dict:
        """解析教师评语文本，提取扣分项和改进建议。

        comment_md 格式约定：
        - 扣分项: "扣分：-N · 理由" 或 "-N · 理由" 或 "-N: 理由"
        - 建议: "建议：xxx" 或 "改进建议：xxx"
        - 其余为教师评语正文
        """
        comment_lines = []
        deduction_items = []
        suggestions = []

        if not comment_md:
            return {"comment": "", "deduction_items": [], "suggestions": []}

        for line in comment_md.split("\n"):
            line = line.strip()
            if not line:
                continue

            deduction_match = re.match(
                r"(?:扣分[：:]\s*)?-(\d+(?:\.\d+)?)\s*[·:：]\s*(.+)", line
            )
            if deduction_match:
                deduction_items.append({
                    "points": float(deduction_match.group(1)),
                    "reason": deduction_match.group(2).strip(),
                })
                continue

            suggestion_match = re.match(
                r"(?:改进?建议[：:]\s*|💡\s*)(.+)", line
            )
            if suggestion_match:
                suggestions.append(suggestion_match.group(1).strip())
                continue

            comment_lines.append(line)

        return {
            "comment": "\n".join(comment_lines).strip(),
            "deduction_items": deduction_items,
            "suggestions": suggestions,
        }

    def on_load(self):
        """页面加载时自动执行，从 GlobalState 获取当前学号。"""
        # TODO: 集成认证后从 GlobalState.current_user 获取学号
        self.load_feedback("2021001001")

    def load_feedback(self, student_no: str = "", assignment_id: Optional[int] = None):
        """加载指定学生/作业的评语反馈。

        从 grading_records 和 feedbacks 表获取教师评语，
        解析 comment_md 提取扣分项和改进建议。
        """
        if student_no:
            self.current_student_id = student_no
        if not self.current_student_id:
            return

        self.is_loading = True

        try:
            with rx.session() as session:
                from sqlmodel import text

                # 查找学生 user_id
                result = session.execute(
                    text(
                        "SELECT id FROM users "
                        "WHERE student_no = :sno AND role = 'student'"
                    ),
                    {"sno": self.current_student_id},
                )
                user_row = result.fetchone()
                if not user_row:
                    self.is_loading = False
                    return
                user_id = user_row[0]

                # 查 grading_records 获取教师评语
                sql = (
                    "SELECT "
                    "gr.id, gr.comment_md, gr.allow_resubmit, gr.graded_at, "
                    "gr.total_score, a.title AS assignment_title, "
                    "a.allow_resubmit AS assignment_allow_resubmit, "
                    "u.full_name AS grader_name, "
                    "s.id AS submission_id, s.version_no, s.is_late "
                    "FROM grading_records gr "
                    "JOIN submissions s ON s.id = gr.submission_id "
                    "JOIN assignments a ON a.id = s.assignment_id "
                    "JOIN users u ON u.id = gr.graded_by "
                    "WHERE s.student_user_id = :uid"
                )
                params = {"uid": user_id}
                if assignment_id:
                    sql += " AND s.assignment_id = :aid"
                    params["aid"] = assignment_id
                sql += " ORDER BY gr.graded_at DESC"

                result = session.execute(text(sql), params)

                self.feedbacks = []
                for row in result.fetchall():
                    comment_md = row[1] or ""
                    parsed = self._parse_comment_md(comment_md)
                    allow_resub = bool(row[2]) or bool(row[6])

                    self.feedbacks.append({
                        "id": row[0],
                        "comment": parsed["comment"],
                        "deduction_items": parsed["deduction_items"],
                        "suggestions": parsed["suggestions"],
                        "allow_resubmit": allow_resub,
                        "graded_at": str(row[3]) if row[3] else "",
                        "total_score": float(row[4]) if row[4] else 0.0,
                        "assignment_title": row[5] or "",
                        "grader_name": row[7] or "教师",
                        "submission_id": row[8],
                        "version_no": row[9],
                        "is_late": bool(row[10]),
                    })

                # 同时查 feedbacks 表获取附加反馈
                sql2 = (
                    "SELECT f.id, f.source_type, f.source_id, f.content, f.created_at, "
                    "u.full_name AS teacher_name "
                    "FROM feedbacks f "
                    "JOIN users u ON u.id = f.teacher_user_id "
                    "WHERE f.student_user_id = :uid"
                )
                params2 = {"uid": user_id}
                if assignment_id:
                    sql2 += " AND f.source_type = 'assignment' AND f.source_id = :aid"
                    params2["aid"] = assignment_id
                sql2 += " ORDER BY f.created_at DESC"

                result2 = session.execute(text(sql2), params2)
                for row in result2.fetchall():
                    content = row[3] or ""
                    parsed = self._parse_comment_md(content)
                    self.feedbacks.append({
                        "id": row[0],
                        "comment": parsed["comment"],
                        "deduction_items": parsed["deduction_items"],
                        "suggestions": parsed["suggestions"],
                        "allow_resubmit": False,
                        "graded_at": str(row[4]) if row[4] else "",
                        "total_score": 0.0,
                        "assignment_title": f"附加反馈 ({row[1]})",
                        "grader_name": row[5] or "教师",
                    })

        except Exception as e:
            print(f"[FeedbackState] 加载评语失败: {e}")

        self.is_loading = False

    def select_feedback(self, feedback: dict):
        """选中一条评语，展示详情。"""
        self.current_feedback = feedback
        if feedback:
            self.allow_resubmit = feedback.get("allow_resubmit", False)
