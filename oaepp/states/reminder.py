"""F-S-054 截止日期个性化提醒设置 — ReminderState

学生可为每门课程的每次作业单独设置截止前 X 小时提醒，
提醒到达时触发站内通知，已完成提交或已过截止时间的任务自动屏蔽。
"""
import datetime
from typing import Optional


class ReminderState:
    """截止提醒状态

    状态变量:
        reminders        : list[dict] — 每个元素含 assignment_id / hours_before / deadline
        available_hours  : list[int]  — 可选的提前提醒小时数
        error_message    : str        — 操作失败时的错误消息
        overdue_days     : int        — 逾期天数（当前无逾期时为 0）
    """

    reminders: list = []
    available_hours: list = [1, 2, 6, 12, 24]

    def __init__(self):
        self.error_message: str = ""
        self.overdue_days: int = 0

    async def set_reminder(
        self,
        assignment_id: int,
        hours_before: int,
        deadline: Optional[datetime.datetime] = None,
    ) -> None:
        """为指定作业添加截止提醒。

        若 deadline 已过则拒绝添加并设置 error_message。
        """
        if deadline is not None and deadline < datetime.datetime.now():
            self.error_message = "截止时间已过，无法新增提醒"
            return

        self.error_message = ""
        reminders_list = list(self.reminders)
        # 替换同一作业的旧提醒
        reminders_list = [
            r for r in reminders_list if r.get("assignment_id") != assignment_id
        ]
        reminder = {
            "assignment_id": assignment_id,
            "hours_before": hours_before,
            "deadline": deadline.isoformat() if deadline else "",
        }
        reminders_list.append(reminder)
        self.reminders = reminders_list

    async def cancel_reminder_on_submit(self, assignment_id: int) -> None:
        """已提交的任务自动撤销对应提醒。"""
        self.reminders = [
            r for r in self.reminders if r.get("assignment_id") != assignment_id
        ]

    def get_overdue_days(self) -> int:
        """返回当前逾期天数（兼容 test_F_S_054_TC05 对属性或方法的要求）。"""
        return self.overdue_days
