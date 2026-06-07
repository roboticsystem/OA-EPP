"""F-S-031 评语反馈 — FeedbackState

提供教师评语和反馈的状态管理：
- feedbacks: 评语列表（含 comment / deduction_items / suggestions）
- current_feedback: 当前选中的评语详情
- allow_resubmit: 是否允许二次提交

验收标准：
- 每次评阅结果展示教师评语和扣分项
- 改进建议以条目形式展示
- 允许二次提交的任务展示重新提交入口

数据源：
- grading_records 表：comment_md（教师评语）、allow_resubmit
- feedbacks 表：content（附加反馈）
- 扣分项与改进建议从 comment_md 中结构化解析
"""

import os
import re
from typing import Any, List, Optional


class FeedbackState:
    """评语反馈状态管理

    对齐验收标准：
    - 每次评阅结果展示教师评语和扣分项
    - 改进建议以条目形式展示
    - 允许二次提交的任务展示重新提交入口

    对齐原型 prototype/grades.html：
    - 评语卡片展示教师评语、扣分项标签、改进建议条目
    - 允许二次提交时显示"前往重新提交"入口
    """

    # ── 核心状态变量（TDD 测试要求） ──
    feedbacks: List[dict] = []
    current_feedback: Optional[dict] = None
    allow_resubmit: bool = False

    # ── 业务状态变量 ──
    assignment_id: Optional[int] = None
    submission_id: Optional[int] = None
    is_loading: bool = False

    # ── 私有属性 ──
    _student_no: Optional[str] = None
    _current_user_id: Optional[int] = None

    def __init__(self):
        self.feedbacks = []
        self.current_feedback = None
        self.allow_resubmit = False
        self.assignment_id = None
        self.submission_id = None
        self.is_loading = False
        self._student_no = None
        self._current_user_id = None

    # ── 事件处理器 ──

    async def load_feedback(self, assignment_id: Optional[int] = None) -> None:
        """加载指定作业的评语反馈。

        从 grading_records 和 feedbacks 表获取教师评语，
        解析 comment_md 提取扣分项和改进建议。

        Args:
            assignment_id: 作业 ID
        """
        if assignment_id is not None:
            self.assignment_id = assignment_id

        self.is_loading = True

        if hasattr(self, "_db_session") and self._db_session is not None:
            self._load_from_session(self._db_session)
        else:
            self._load_from_production()

        self.is_loading = False

    def select_feedback(self, feedback: dict) -> None:
        """选中一条评语，展示详情。

        Args:
            feedback: 评语字典，包含 comment / deduction_items / suggestions 等
        """
        self.current_feedback = feedback
        if feedback:
            self.allow_resubmit = feedback.get("allow_resubmit", False)

    # ── 内部方法 ──

    @staticmethod
    def _parse_comment_md(comment_md: str) -> dict:
        """解析教师评语文本，提取扣分项和改进建议。

        comment_md 格式约定：
        - 扣分项行格式: "扣分：-N · 理由" 或 "-N: 理由"
        - 建议行格式: "建议：xxx" 或 "改进建议：xxx"
        - 其余为教师评语正文

        Returns:
            {
                "comment": str,           # 教师评语正文
                "deduction_items": list,  # 扣分项 [{points: float, reason: str}]
                "suggestions": list,       # 改进建议 [str]
            }
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

            # 匹配扣分项: "扣分：-N · 理由" 或 "-N · 理由" 或 "-N: 理由"
            deduction_match = re.match(
                r"(?:扣分[：:]\s*)?-(\d+(?:\.\d+)?)\s*[·:：]\s*(.+)", line
            )
            if deduction_match:
                deduction_items.append({
                    "points": float(deduction_match.group(1)),
                    "reason": deduction_match.group(2).strip(),
                })
                continue

            # 匹配改进建议: "建议：xxx" 或 "改进建议：xxx" 或 "💡 xxx"
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

    def _load_from_session(self, session) -> None:
        """从 sqlmodel Session 加载（测试环境）"""
        try:
            from sqlmodel import text

            result = session.execute(
                text(
                    "SELECT gr.id, gr.comment_md, gr.allow_resubmit, gr.graded_at, "
                    "gr.total_score, a.title, a.allow_resubmit AS assignment_allow_resubmit, "
                    "u.full_name AS grader_name "
                    "FROM grading_records gr "
                    "JOIN submissions s ON s.id = gr.submission_id "
                    "JOIN assignments a ON a.id = s.assignment_id "
                    "JOIN users u ON u.id = gr.graded_by "
                    "WHERE s.student_user_id = :uid "
                    "ORDER BY gr.graded_at DESC"
                ),
                {"uid": self._current_user_id or 0},
            )
            rows = result.fetchall()
            self.feedbacks = []
            for row in rows:
                comment_md = row[1] if len(row) > 1 else ""
                parsed = self._parse_comment_md(str(comment_md) if comment_md else "")
                allow_resub = bool(row[2]) if len(row) > 2 else False
                assignment_allow = bool(row[6]) if len(row) > 6 else False

                self.feedbacks.append({
                    "id": row[0],
                    "comment": parsed["comment"],
                    "deduction_items": parsed["deduction_items"],
                    "suggestions": parsed["suggestions"],
                    "allow_resubmit": allow_resub or assignment_allow,
                    "graded_at": str(row[3]) if len(row) > 3 else "",
                    "total_score": float(row[4]) if (len(row) > 4 and row[4]) else 0.0,
                    "assignment_title": row[5] if len(row) > 5 else "",
                    "grader_name": row[7] if len(row) > 7 else "教师",
                })
        except Exception:
            self.feedbacks = []

    def _load_from_production(self) -> None:
        """从生产 MySQL 数据库加载评语反馈"""
        try:
            import pymysql

            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                # 查找学生 user_id
                user_id = self._current_user_id
                if not user_id and self._student_no:
                    cur.execute(
                        "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                        (self._student_no,),
                    )
                    user_row = cur.fetchone()
                    if user_row:
                        user_id = user_row["id"]
                        self._current_user_id = user_id

                if not user_id:
                    conn.close()
                    return

                # 查 grading_records 获取教师评语
                sql = """
                    SELECT
                        gr.id, gr.comment_md, gr.allow_resubmit, gr.graded_at,
                        gr.total_score, a.title, a.allow_resubmit AS assignment_allow_resubmit,
                        u.full_name AS grader_name,
                        s.id AS submission_id, s.version_no, s.is_late,
                        gr.attendance_score, gr.exam_score, gr.code_score, gr.pr_score
                    FROM grading_records gr
                    JOIN submissions s ON s.id = gr.submission_id
                    JOIN assignments a ON a.id = s.assignment_id
                    JOIN users u ON u.id = gr.graded_by
                    WHERE s.student_user_id = %s
                """
                params = [user_id]

                # 如果指定了 assignment_id，则筛选
                if self.assignment_id:
                    sql += " AND s.assignment_id = %s"
                    params.append(self.assignment_id)

                sql += " ORDER BY gr.graded_at DESC"

                cur.execute(sql, params)
                rows = cur.fetchall()

                self.feedbacks = []
                for row in rows:
                    comment_md = row["comment_md"] or ""
                    parsed = self._parse_comment_md(comment_md)
                    allow_resub = bool(row.get("allow_resubmit", 0)) or bool(
                        row.get("assignment_allow_resubmit", 0)
                    )

                    self.feedbacks.append({
                        "id": row["id"],
                        "comment": parsed["comment"],
                        "deduction_items": parsed["deduction_items"],
                        "suggestions": parsed["suggestions"],
                        "allow_resubmit": allow_resub,
                        "graded_at": row["graded_at"].strftime("%Y-%m-%d %H:%M") if row["graded_at"] else "",
                        "total_score": float(row["total_score"]) if row["total_score"] else 0.0,
                        "assignment_title": row["title"],
                        "grader_name": row["grader_name"],
                        "submission_id": row["submission_id"],
                        "version_no": row["version_no"],
                        "is_late": bool(row["is_late"]),
                        "attendance_score": float(row["attendance_score"]) if row["attendance_score"] else None,
                        "exam_score": float(row["exam_score"]) if row["exam_score"] else None,
                        "code_score": float(row["code_score"]) if row["code_score"] else None,
                        "pr_score": float(row["pr_score"]) if row["pr_score"] else None,
                    })

                # 同时查 feedbacks 表获取附加反馈
                sql2 = """
                    SELECT f.id, f.source_type, f.source_id, f.content, f.created_at,
                           u.full_name AS teacher_name
                    FROM feedbacks f
                    JOIN users u ON u.id = f.teacher_user_id
                    WHERE f.student_user_id = %s
                """
                params2 = [user_id]
                if self.assignment_id:
                    sql2 += " AND f.source_type = 'assignment' AND f.source_id = %s"
                    params2.append(self.assignment_id)
                sql2 += " ORDER BY f.created_at DESC"

                cur.execute(sql2, params2)
                fb_rows = cur.fetchall()
                for row in fb_rows:
                    content = row["content"] or ""
                    parsed = self._parse_comment_md(content)
                    self.feedbacks.append({
                        "id": row["id"],
                        "comment": parsed["comment"],
                        "deduction_items": parsed["deduction_items"],
                        "suggestions": parsed["suggestions"],
                        "allow_resubmit": False,
                        "graded_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if row["created_at"] else "",
                        "total_score": 0.0,
                        "assignment_title": f"附加反馈 ({row['source_type']})",
                        "grader_name": row["teacher_name"],
                    })

            conn.close()

        except Exception:
            self.feedbacks = []

    @staticmethod
    def _get_mysql_connection():
        """获取 MySQL 连接"""
        import pymysql
        from urllib.parse import urlparse, unquote

        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            parsed = urlparse(db_url)
            return pymysql.connect(
                host=parsed.hostname or "127.0.0.1",
                port=parsed.port or 3306,
                user=parsed.username or "root",
                password=unquote(parsed.password) if parsed.password else "",
                database=parsed.path.lstrip("/") or "oaepp_dev",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        else:
            return pymysql.connect(
                host=os.environ.get("DB_HOST", "156.239.252.40"),
                port=int(os.environ.get("DB_PORT", "13306")),
                user=os.environ.get("DB_USER", "student_dev"),
                password=os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
                database=os.environ.get("DB_NAME", "oaepp_dev"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
