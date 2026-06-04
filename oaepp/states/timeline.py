"""F-S-041 学习时间线 TimelineState

Reflex State — 按时间序展示任务发布→提交→批改→反馈全流程关键节点。
"""

import os
import sys
from typing import Optional

import reflex as rx

# 确保 backend 包可导入
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from app.database import db


class TimelineState(rx.State):
    """学习时间线状态管理"""

    timeline_events: list = []
    is_loading: bool = False
    current_user_id: str = ""
    error_message: str = ""

    EVENT_TYPES = ("task_publish", "submit", "grade", "feedback")

    async def load_timeline(
        self,
        student_id: str = "",
        course: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """加载学生学习时间线事件"""
        self.is_loading = True
        self.timeline_events = []
        self.error_message = ""

        sid = student_id or self.current_user_id
        if not sid:
            self.error_message = "请先指定学生学号"
            self.is_loading = False
            return

        try:
            with db() as conn:
                student = conn.execute(
                    "SELECT name, student_id, class_name FROM students WHERE student_id = ?",
                    (sid,)
                ).fetchone()
                if not student:
                    self.error_message = f"学号不存在: {sid}"
                    self.is_loading = False
                    return

                sql = "SELECT * FROM timeline_events WHERE student_id = ?"
                params = [sid]

                if course:
                    sql += " AND course = ?"
                    params.append(course)
                if start_date:
                    sql += " AND event_time >= ?"
                    params.append(start_date)
                if end_date:
                    sql += " AND event_time <= ?"
                    params.append(end_date)

                sql += " ORDER BY event_time DESC"

                try:
                    events = [dict(r) for r in conn.execute(sql, params).fetchall()]
                except Exception:
                    events = []

                self.current_user_id = sid
                self.timeline_events = events
        except Exception as e:
            self.error_message = f"加载时间线失败: {e}"
        finally:
            self.is_loading = False

    async def refresh(self):
        """刷新当前用户的时间线"""
        if self.current_user_id:
            await self.load_timeline(student_id=self.current_user_id)
