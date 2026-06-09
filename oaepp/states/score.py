"""F-S-030 成绩统计 — ScoreState

提供成绩看板的状态管理：
- attendance_score: 出勤得分
- exam_score: 考试得分
- code_score: 代码提交得分
- pr_score: PR 贡献得分
- total_score: 综合总分
- score_breakdown: 各维度得分详情列表
- current_user_id: 当前用户 ID（数据隔离）

数据源：
- score_items 表：按 score_type 分类汇总
- grading_records 表：作业评阅总分

对齐原型 prototype/grades.html：
- 顶部四维度得分卡片
- 详情标签页（代码评阅/考试成绩/出勤记录/时间线）
"""

import os
from typing import Any, List, Optional


class ScoreState:
    """成绩统计状态管理

    对齐 prototype/grades.html 原型：
    - 顶部四维度得分卡片：出勤/考试/代码/PR
    - 详情标签页：代码评阅/考试成绩/出勤记录/时间线

    数据隔离：通过 current_user_id 仅加载当前学生自身成绩。
    """

    # ── 四维度得分（TDD 测试要求） ──
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

    # ── 数据隔离 ──
    current_user_id: int = 0

    # ── 业务状态 ──
    course_id: Optional[int] = None
    score_breakdown: List[dict] = []
    exam_records: List[dict] = []
    attendance_records: List[dict] = []
    is_loading: bool = False

    # ── 私有属性 ──
    _student_no: Optional[str] = None

    def __init__(self):
        self.attendance_score = 0.0
        self.exam_score = 0.0
        self.code_score = 0.0
        self.pr_score = 0.0
        self.total_score = 0.0
        self.attendance_total = 20.0
        self.exam_total = 30.0
        self.code_total = 40.0
        self.pr_total = 10.0
        self.current_user_id = 0
        self.course_id = None
        self.score_breakdown = []
        self.exam_records = []
        self.attendance_records = []
        self.is_loading = False
        self._student_no = None

    # ── 事件处理器 ──

    async def load_scores(self, student_no: Optional[str] = None) -> None:
        """加载当前学生各维度成绩。

        从 score_items 表按 score_type 汇总四维度得分，
        从 grading_records 表获取作业评阅详情。

        Args:
            student_no: 学号（可选，优先使用实例属性）
        """
        if student_no:
            self._student_no = student_no

        self.is_loading = True

        if hasattr(self, "_db_session") and self._db_session is not None:
            self._load_from_session(self._db_session)
        else:
            self._load_from_production()

        self._recalculate_total()
        self.is_loading = False

    # ── 内部方法 ──

    def _recalculate_total(self) -> None:
        """根据四维度得分计算综合总分。"""
        self.total_score = (
            self.attendance_score
            + self.exam_score
            + self.code_score
            + self.pr_score
        )

    def _load_from_session(self, session) -> None:
        """从 sqlmodel Session 加载（测试环境）"""
        try:
            from sqlmodel import text

            # 查 score_items
            result = session.execute(
                text(
                    "SELECT score_type, SUM(score) AS total_score "
                    "FROM score_items "
                    "WHERE student_user_id = :uid "
                    "GROUP BY score_type"
                ),
                {"uid": self.current_user_id},
            )
            rows = result.fetchall()
            for row in rows:
                stype = row[0]
                val = float(row[1]) if row[1] else 0.0
                if stype == "attendance":
                    self.attendance_score = val
                elif stype == "exam":
                    self.exam_score = val
                elif stype == "code":
                    self.code_score = val
                elif stype == "pr":
                    self.pr_score = val

            # 查 grading_records 获取评阅详情
            result2 = session.execute(
                text(
                    "SELECT gr.*, a.title AS assignment_title, s.version_no "
                    "FROM grading_records gr "
                    "JOIN submissions s ON s.id = gr.submission_id "
                    "JOIN assignments a ON a.id = s.assignment_id "
                    "WHERE s.student_user_id = :uid "
                    "ORDER BY gr.graded_at DESC"
                ),
                {"uid": self.current_user_id},
            )
            self.score_breakdown = []
            for row in result2.fetchall():
                self.score_breakdown.append({
                    "assignment_title": row[8] if len(row) > 8 else "",
                    "total_score": float(row[7]) if row[7] else 0.0,
                    "comment_md": row[8] if len(row) > 8 else "",
                    "allow_resubmit": bool(row[9]) if len(row) > 9 else False,
                    "graded_at": str(row[10]) if len(row) > 10 else "",
                })
        except Exception:
            pass

    def _load_from_production(self) -> None:
        """从生产 MySQL 数据库加载成绩数据"""
        try:
            import pymysql
            from decimal import Decimal

            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                # 1) 查找学生 user_id
                if self._student_no:
                    cur.execute(
                        "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                        (self._student_no,),
                    )
                    user_row = cur.fetchone()
                    if user_row:
                        self.current_user_id = user_row["id"]

                # 2) 查 score_items 按维度汇总
                cur.execute(
                    "SELECT score_type, SUM(score) AS total_score "
                    "FROM score_items "
                    "WHERE student_user_id = %s "
                    "GROUP BY score_type",
                    (self.current_user_id,),
                )
                rows = cur.fetchall()
                for row in rows:
                    stype = row["score_type"]
                    val = float(row["total_score"]) if row["total_score"] else 0.0
                    if stype == "attendance":
                        self.attendance_score = val
                    elif stype == "exam":
                        self.exam_score = val
                    elif stype == "code":
                        self.code_score = val
                    elif stype == "pr":
                        self.pr_score = val

                # 3) 查 grading_records 获取作业评阅详情
                cur.execute(
                    """
                    SELECT
                        gr.id, gr.submission_id, gr.graded_by, gr.attendance_score,
                        gr.exam_score, gr.code_score, gr.pr_score, gr.total_score,
                        gr.comment_md, gr.allow_resubmit, gr.graded_at,
                        a.title AS assignment_title, a.allow_resubmit AS assignment_allow_resubmit,
                        s.version_no, s.is_late,
                        u.full_name AS grader_name
                    FROM grading_records gr
                    JOIN submissions s ON s.id = gr.submission_id
                    JOIN assignments a ON a.id = s.assignment_id
                    JOIN users u ON u.id = gr.graded_by
                    WHERE s.student_user_id = %s
                    ORDER BY gr.graded_at DESC
                    """,
                    (self.current_user_id,),
                )
                grade_rows = cur.fetchall()
                self.score_breakdown = []
                for row in grade_rows:
                    allow_resub = bool(row.get("allow_resubmit", 0)) or bool(
                        row.get("assignment_allow_resubmit", 0)
                    )
                    self.score_breakdown.append({
                        "id": row["id"],
                        "submission_id": row["submission_id"],
                        "assignment_title": row["assignment_title"],
                        "total_score": float(row["total_score"]) if row["total_score"] else 0.0,
                        "code_score": float(row["code_score"]) if row["code_score"] else None,
                        "comment_md": row["comment_md"] or "",
                        "allow_resubmit": allow_resub,
                        "graded_at": row["graded_at"].strftime("%Y-%m-%d %H:%M") if row["graded_at"] else "",
                        "grader_name": row["grader_name"],
                        "version_no": row["version_no"],
                        "is_late": bool(row["is_late"]),
                    })

                # 4) 查考试成绩（从 exams / exam_attempts）
                cur.execute(
                    """
                    SELECT e.title, ea.score, ea.total, ea.submitted_at
                    FROM exam_attempts ea
                    JOIN exams e ON e.id = ea.exam_id
                    WHERE ea.student_user_id = %s
                    ORDER BY ea.submitted_at DESC
                    """,
                    (self.current_user_id,),
                )
                self.exam_records = []
                for row in cur.fetchall():
                    self.exam_records.append({
                        "title": row["title"],
                        "score": float(row["score"]) if row["score"] else 0.0,
                        "total": float(row["total"]) if row["total"] else 0.0,
                        "submitted_at": row["submitted_at"].strftime("%Y-%m-%d") if row["submitted_at"] else "",
                    })

            conn.close()

        except Exception:
            pass

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
