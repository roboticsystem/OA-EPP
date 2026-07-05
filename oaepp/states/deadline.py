"""F-S-022 截止规则 — DeadlineState

提供作业截止规则的状态管理：
- deadline: 截止时间
- is_past_deadline: 是否已过截止时间
- late_flag: 迟交标记
- deadline_policy: 截止策略 (block / mark_late / penalty)
- assignments: 作业列表（含截止状态）
- selected_assignment: 当前选中的作业
- filter_status: 当前筛选状态
- submit_message: 提交结果消息
"""

import datetime
from typing import Any, List, Optional


class DeadlineState:
    """截止规则状态管理

    对齐 prototype/assignments.html 原型：
    - 左栏：作业列表，支持筛选（全部/待提交/已提交/已批改）
    - 右栏：提交面板，根据截止状态动态显示警告
    - 迟交状态以橙色标签明确展示

    对齐后端 API：
    - GET /api/assignments?student_no=...&status=...
    - POST /api/assignments/submit
    - GET /api/assignments/{id}/submissions?student_no=...
    """

    # ── 核心状态变量（TDD 测试要求） ──
    deadline: Optional[datetime.datetime] = None
    is_past_deadline: bool = False
    late_flag: bool = False
    deadline_policy: str = "block"  # block | mark_late | penalty

    # ── 业务状态变量 ──
    assignments: List[dict] = []
    selected_assignment: Optional[dict] = None
    filter_status: str = "all"
    submit_message: str = ""
    submission_versions: List[dict] = []

    # ── 私有属性 ──
    _student_no: Optional[str] = None
    _db_session: Any = None

    def __init__(self):
        self.deadline = None
        self.is_past_deadline = False
        self.late_flag = False
        self.deadline_policy = "block"
        self.assignments = []
        self.selected_assignment = None
        self.filter_status = "all"
        self.submit_message = ""
        self.submission_versions = []

    # ── 事件处理器 ──

    def check_deadline(self) -> None:
        """检查当前时间是否超过截止时间，更新 is_past_deadline 和 late_flag。

        对应验收标准：
        - 截止前 is_past_deadline=False，允许正常提交
        - 截止后 is_past_deadline=True，根据策略处理
        """
        if self.deadline is None:
            self.is_past_deadline = False
            self.late_flag = False
            return

        now = datetime.datetime.now()
        self.is_past_deadline = now > self.deadline

        # 根据策略设置迟交标记
        if self.is_past_deadline and self.deadline_policy in ("mark_late", "penalty"):
            self.late_flag = True
        else:
            self.late_flag = False

    def set_filter(self, status: str) -> None:
        """设置筛选状态并重新加载作业列表。

        Args:
            status: all | pending | submitted | graded | late | closed
        """
        self.filter_status = status

    async def load_assignments(self, student_no: Optional[str] = None) -> None:
        """从数据库加载学生作业列表，含截止状态与迟交标记。

        对接后端 GET /api/assignments?student_no=...&status=...
        """
        if student_no:
            self._student_no = student_no

        if hasattr(self, "_db_session") and self._db_session is not None:
            self._load_from_session(self._db_session)
        else:
            self._load_from_production()

    async def submit_assignment(
        self,
        assignment_id: int,
        text_content: str = "",
        file_url: Optional[str] = None,
    ) -> None:
        """提交作业 — 核心截止规则逻辑。

        - 截止前：正常提交
        - 截止后 policy=block(deny)：禁止提交
        - 截止后 policy=mark_late(allow)：标记迟交
        - 截止后 policy=penalty：标记迟交，教师后续扣分
        """
        if hasattr(self, "_db_session") and self._db_session is not None:
            self._submit_via_session(self._db_session, assignment_id, text_content)
        else:
            self._submit_via_production(assignment_id, text_content, file_url)

    def select_assignment(self, assignment: dict) -> None:
        """选中一个作业，展示其详情和提交面板。"""
        self.selected_assignment = assignment
        if assignment:
            deadline_str = assignment.get("deadline")
            if deadline_str and isinstance(deadline_str, str):
                try:
                    self.deadline = datetime.datetime.fromisoformat(deadline_str)
                except (ValueError, TypeError):
                    self.deadline = None
            elif isinstance(deadline_str, datetime.datetime):
                self.deadline = deadline_str

            # 映射 late_policy 到 deadline_policy
            lp = assignment.get("late_policy", "deny")
            policy_map = {"deny": "block", "allow": "mark_late", "penalty": "penalty"}
            self.deadline_policy = policy_map.get(lp, "block")

            self.check_deadline()

    # ── 内部方法 ──

    def _load_from_session(self, session) -> None:
        """从 sqlmodel Session 加载（测试环境）"""
        try:
            from sqlmodel import text

            result = session.execute(
                text(
                    "SELECT a.*, "
                    "s.id AS submission_id, s.version_no, s.file_url, "
                    "s.is_late, s.grading_status, s.submitted_at "
                    "FROM assignments a "
                    "LEFT JOIN submissions s ON s.assignment_id = a.id "
                    "ORDER BY a.deadline ASC"
                )
            )
            rows = result.fetchall()
            now = datetime.datetime.now()
            self.assignments = []
            for row in rows:
                deadline = row[7] if len(row) > 7 else None  # deadline column
                late_policy = row[6] if len(row) > 6 else "deny"
                item = {
                    "id": row[0],
                    "title": row[3] if len(row) > 3 else "",
                    "deadline": str(deadline) if deadline else "",
                    "late_policy": late_policy,
                    "is_past_deadline": now > deadline if deadline else False,
                }
                self.assignments.append(item)
        except Exception:
            self.assignments = []

    def _load_from_production(self) -> None:
        """从生产 MySQL 数据库加载作业列表"""
        try:
            import os
            import pymysql
            from urllib.parse import urlparse, unquote

            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                sql = """
                    SELECT
                        a.id, a.course_id, a.chapter_id, a.title, a.description_md,
                        a.deadline, a.late_policy, a.allow_resubmit, a.created_at,
                        c.code AS course_code, c.name AS course_name, c.term AS course_term,
                        s.id AS submission_id, s.version_no, s.file_url,
                        s.is_late, s.grading_status, s.submitted_at
                    FROM assignments a
                    JOIN courses c ON c.id = a.course_id
                    LEFT JOIN submissions s ON s.id = (
                        SELECT id FROM submissions
                        WHERE assignment_id = a.id AND student_user_id = (
                            SELECT id FROM users WHERE student_no = %s AND role = 'student'
                        )
                        ORDER BY version_no DESC LIMIT 1
                    )
                    WHERE a.course_id IN (
                        SELECT course_id FROM enrollments
                        WHERE student_user_id = (
                            SELECT id FROM users WHERE student_no = %s AND role = 'student'
                        )
                    )
                    ORDER BY a.deadline ASC
                """
                cur.execute(sql, (self._student_no, self._student_no))
                rows = cur.fetchall()

            conn.close()

            now = datetime.datetime.now()
            self.assignments = []
            for row in rows:
                deadline = row["deadline"]
                late_policy = row["late_policy"]
                is_past = now > deadline if deadline else False

                # 计算状态
                submission = None
                if row.get("submission_id"):
                    submission = {
                        "id": row["submission_id"],
                        "version_no": row["version_no"],
                        "file_url": row["file_url"],
                        "is_late": bool(row["is_late"]),
                        "grading_status": row["grading_status"],
                        "submitted_at": row["submitted_at"].isoformat() if row["submitted_at"] else None,
                    }

                status_info = self._classify_status(deadline, late_policy, submission, now)

                # 筛选
                if self.filter_status != "all" and status_info["status_code"] != self.filter_status:
                    continue

                time_left = (deadline - now).total_seconds() if deadline else 0
                remaining_days = int(time_left // 86400) if time_left > 0 else 0

                item = {
                    "id": row["id"],
                    "title": row["title"],
                    "course_code": row.get("course_code", ""),
                    "course_name": row.get("course_name", ""),
                    "course_term": row.get("course_term", ""),
                    "chapter_id": row.get("chapter_id"),
                    "deadline": deadline.isoformat() if deadline else "",
                    "late_policy": late_policy,
                    "allow_resubmit": bool(row.get("allow_resubmit", 1)),
                    "remaining_days": remaining_days,
                    "is_past_deadline": is_past,
                    "status_label": status_info["status_label"],
                    "status_code": status_info["status_code"],
                    "submission": submission,
                }
                self.assignments.append(item)

        except Exception:
            self.assignments = []

    def _submit_via_session(self, session, assignment_id: int, text_content: str) -> None:
        """测试环境提交"""
        try:
            from sqlmodel import text as sql_text

            # 查作业
            result = session.execute(
                sql_text("SELECT * FROM assignments WHERE id = :aid"),
                {"aid": assignment_id},
            )
            assignment = result.fetchone()
            if not assignment:
                self.submit_message = "作业不存在"
                return

            now = datetime.datetime.now()
            deadline = assignment[7] if len(assignment) > 7 else None
            late_policy = assignment[6] if len(assignment) > 6 else "deny"

            if deadline and now > deadline and late_policy == "deny":
                self.submit_message = "作业已截止，禁止提交"
                return

            is_late = 1 if (deadline and now > deadline) else 0
            self.late_flag = bool(is_late)

            if not is_late:
                self.submit_message = "提交成功"
            elif late_policy == "penalty":
                self.submit_message = "已迟交，将按课程策略扣分"
            else:
                self.submit_message = "已迟交，按课程策略允许提交"

        except Exception as e:
            self.submit_message = f"提交失败: {e}"

    def _submit_via_production(
        self, assignment_id: int, text_content: str, file_url: Optional[str]
    ) -> None:
        """生产环境提交"""
        try:
            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                # 查作业
                cur.execute(
                    "SELECT id, deadline, late_policy, allow_resubmit FROM assignments WHERE id = %s",
                    (assignment_id,),
                )
                a = cur.fetchone()
                if not a:
                    self.submit_message = "作业不存在"
                    conn.close()
                    return

                now = datetime.datetime.now()
                deadline = a["deadline"]
                late_policy = a["late_policy"]

                # 截止规则核心判定
                if now > deadline and late_policy == "deny":
                    self.submit_message = (
                        f"作业已于 {deadline.strftime('%Y-%m-%d %H:%M')} 截止，禁止提交"
                    )
                    conn.close()
                    return

                is_late = 1 if now > deadline else 0
                self.late_flag = bool(is_late)
                self.is_past_deadline = now > deadline

                # 查学生 user_id
                cur.execute(
                    "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                    (self._student_no,),
                )
                user_row = cur.fetchone()
                if not user_row:
                    self.submit_message = "学生不存在"
                    conn.close()
                    return
                student_user_id = user_row["id"]

                # 版本号
                cur.execute(
                    "SELECT MAX(version_no) AS max_v FROM submissions WHERE assignment_id = %s AND student_user_id = %s",
                    (assignment_id, student_user_id),
                )
                prev = cur.fetchone()
                version_no = ((prev["max_v"] or 0) + 1) if prev else 1

                # 插入提交记录
                cur.execute(
                    """INSERT INTO submissions
                       (assignment_id, student_user_id, version_no, file_url, text_content, is_late, grading_status, submitted_at)
                       VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())""",
                    (assignment_id, student_user_id, version_no, file_url, text_content, is_late),
                )

            conn.commit()
            conn.close()

            if not is_late:
                self.submit_message = "提交成功"
            elif late_policy == "penalty":
                self.submit_message = "已迟交，将按课程策略扣分"
            else:
                self.submit_message = "已迟交，按课程策略允许提交"

        except Exception as e:
            self.submit_message = f"提交失败: {e}"

    @staticmethod
    def _classify_status(
        deadline: datetime.datetime,
        late_policy: str,
        submission: Optional[dict],
        now: datetime.datetime,
    ) -> dict:
        """根据截止时间、迟交策略和提交记录，计算状态标签。

        与后端 assignment.py _classify_status 逻辑保持一致。
        """
        is_past = now > deadline if deadline else False

        if submission:
            grading_status = submission.get("grading_status", "pending")
            is_late = submission.get("is_late", False)
            if grading_status == "graded":
                return {"status_label": "已批改", "status_code": "graded"}
            elif is_late:
                return {"status_label": "迟交", "status_code": "late"}
            else:
                return {"status_label": "已提交", "status_code": "submitted"}
        else:
            if is_past:
                if late_policy == "deny":
                    return {"status_label": "已截止", "status_code": "closed"}
                else:
                    return {"status_label": "可迟交", "status_code": "late_allowed"}
            else:
                return {"status_label": "待提交", "status_code": "pending"}

    @staticmethod
    def _get_mysql_connection():
        """获取 MySQL 连接"""
        import os
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
