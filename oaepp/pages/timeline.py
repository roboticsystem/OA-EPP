"""F-S-041 学习时间线页面

按时间序展示任务发布→提交→批改→反馈全流程关键节点。
"""
import reflex as rx
from oaepp.states.timeline import TimelineState


def timeline_page() -> rx.Component:
    """学习时间线页面"""
    return rx.container(
        rx.heading("学习时间线", size="lg"),
        rx.text("追踪学习任务发布 → 提交 → 批改 → 反馈全流程"),
        rx.divider(),
        # Event type summary
        rx.grid(
            rx.card(
                rx.text("任务发布", weight="bold"),
                rx.text("0", id="publish-count"),
            ),
            rx.card(
                rx.text("已提交", weight="bold"),
                rx.text("0", id="submit-count"),
            ),
            rx.card(
                rx.text("已批改", weight="bold"),
                rx.text("0", id="grade-count"),
            ),
            rx.card(
                rx.text("反馈", weight="bold"),
                rx.text("0", id="feedback-count"),
            ),
            columns="4",
            spacing="4",
        ),
        # Timeline list
        rx.vstack(
            rx.foreach(
                TimelineState.timeline_events,
                lambda event: rx.card(
                    rx.hstack(
                        rx.badge(
                            rx.cond(
                                event.event_type == "task_publish",
                                "📋",
                                rx.cond(
                                    event.event_type == "submit",
                                    "📤",
                                    rx.cond(
                                        event.event_type == "grade",
                                        "📝",
                                        "💬",
                                    ),
                                ),
                            ),
                        ),
                        rx.vstack(
                            rx.text(event.title, weight="bold"),
                            rx.text(event.description, size="sm"),
                            rx.text(event.event_time, size="xs"),
                        ),
                    ),
                ),
            ),
            spacing="4",
        ),
        padding="2em",
    )
