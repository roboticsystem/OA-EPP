"""F-S-041 学习时间线 — TimelineState

按时间序展示任务发布→提交→批改→反馈全流程关键节点。
对齐 prototype/timeline.html 原型页面。

验收标准：
- 时间线按时间序展示全部关键节点
- 节点类型清晰区分（发布/提交/批改/反馈）
- 支持按课程或时间段筛选
"""
import datetime
from typing import List, Optional


class TimelineState:
    """学习时间线状态管理

    状态变量：
        timeline_events: 时间线事件列表（按时间倒序）
        is_loading: 加载状态
        current_user_id: 当前用户 ID
        filter_course: 课程筛选
        filter_start: 开始日期筛选
        filter_end: 结束日期筛选
    """

    # ── 核心状态变量（TDD 测试要求） ──
    timeline_events: List[dict] = []
    is_loading: bool = False
    current_user_id: str = ""

    # ── 事件类型定义 ──
    EVENT_TYPES = ("task_publish", "submit", "grade", "feedback")
    EVENT_TYPE_LABELS = {
        "task_publish": "发布",
        "submit": "提交",
        "grade": "批改",
        "feedback": "反馈",
    }

    # ── 筛选状态 ──
    filter_course: str = ""
    filter_start: str = ""
    filter_end: str = ""

    # ── 私有属性 ──
    _student_no: Optional[str] = None
    _db_session: Optional[object] = None

    def __init__(self):
        self.timeline_events = []
        self.is_loading = False
        self.current_user_id = ""
        self.filter_course = ""
        self.filter_start = ""
        self.filter_end = ""

    # ── 事件处理器 ──

    async def load_timeline(self, student_no: Optional[str] = None) -> None:
        """加载时间线事件

        对接后端数据库，按事件时间倒序返回时间线事件列表。
        支持按课程和时间段筛选。
        """
        self.is_loading = True
        if student_no:
            self._student_no = student_no

        try:
            if self._db_session is not None:
                self._load_from_session(self._db_session)
            else:
                await self._load_from_production()
        except Exception:
            self.timeline_events = []
        finally:
            self.is_loading = False

    def set_filter(self, course: str = "", start: str = "", end: str = "") -> None:
        """设置筛选条件并重新加载时间线"""
        self.filter_course = course
        self.filter_start = start
        self.filter_end = end

    # ── 内部方法 ──

    def _load_from_session(self, session) -> None:
        """从 sqlmodel Session 加载（测试环境）"""
        import datetime

        try:
            from sqlmodel import text

            conditions = ["1=1"]
            params = {}

            if self._student_no:
                conditions.append("t.student_no = :student_no")
                params["student_no"] = self._student_no
            if self.filter_course:
                conditions.append("t.course = :course")
                params["course"] = self.filter_course
            if self.filter_start:
                conditions.append("t.event_time >= :start")
                params["start"] = self.filter_start
            if self.filter_end:
                conditions.append("t.event_time <= :end")
                params["end"] = self.filter_end

            sql = (
                "SELECT t.* FROM timeline_events t"
                " WHERE " + " AND ".join(conditions) +
                " ORDER BY t.event_time DESC"
            )

            result = session.execute(text(sql), params)
            rows = result.fetchall()

            self.timeline_events = []
            for row in rows:
                event = {}
                for col in row._mapping.keys():
                    val = row._mapping[col]
                    if isinstance(val, (datetime.datetime, datetime.date)):
                        val = val.isoformat()
                    event[col] = val
                self.timeline_events.append(event)

        except Exception:
            self.timeline_events = []

    async def _load_from_production(self) -> None:
        """从生产 MySQL 数据库加载时间线事件"""
        try:
            from oaepp.database import db as db_ctx

            conditions = ["1=1"]
            params = []

            if self._student_no:
                conditions.append("t.student_no = %s")
                params.append(self._student_no)
            if self.filter_course:
                conditions.append("t.course = %s")
                params.append(self.filter_course)
            if self.filter_start:
                conditions.append("t.event_time >= %s")
                params.append(self.filter_start)
            if self.filter_end:
                conditions.append("t.event_time <= %s")
                params.append(self.filter_end)

            sql = (
                "SELECT t.* FROM timeline_events t"
                " WHERE " + " AND ".join(conditions) +
                " ORDER BY t.event_time DESC"
            )

            async with db_ctx() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

            self.timeline_events = []
            for row in rows:
                event = dict(row)
                for k, v in event.items():
                    if isinstance(v, (datetime.datetime, datetime.date)):
                        event[k] = v.isoformat()
                self.timeline_events.append(event)

        except Exception:
            self.timeline_events = []
