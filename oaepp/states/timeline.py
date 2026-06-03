"""F-S-041 学习时间线 TimelineState

Reflex State — 按时间序展示任务发布→提交→批改→反馈全流程关键节点。
"""
import reflex as rx


class TimelineState(rx.State):
    """学习时间线状态管理"""

    timeline_events: list = []
    is_loading: bool = False
    current_user_id: str = ""

    EVENT_TYPES = ("task_publish", "submit", "grade", "feedback")

    async def load_timeline(self):
        """加载时间线事件"""
        self.timeline_events = []
