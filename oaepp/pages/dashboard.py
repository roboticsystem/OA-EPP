import reflex as rx

from oaepp.components.sidebar import sidebar
from oaepp.components.stat_card import stat_card


def chart_card(title: str, body: rx.Component, footer: str = ""):
    return rx.box(
        rx.text(
            title,
            font_size="0.875rem",
            font_weight="700",
            color="#374151",
            margin_bottom="1rem",
        ),
        body,
        rx.cond(
            footer != "",
            rx.text(
                footer,
                color="#9ca3af",
                font_size="0.75rem",
                text_align="right",
                margin_top="0.5rem",
            ),
        ),
        background="white",
        border="1px solid #f3f4f6",
        border_radius="0.75rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        padding="1.25rem",
        width="100%",
    )


def radar_placeholder():
    return rx.vstack(
        rx.box(
            rx.text("出勤", position="absolute", top="0.4rem", left="50%", transform="translateX(-50%)", color="#6b7280", font_size="0.7rem"),
            rx.text("考试", position="absolute", right="0.5rem", top="4rem", color="#6b7280", font_size="0.7rem"),
            rx.text("代码", position="absolute", right="1.2rem", bottom="0.5rem", color="#6b7280", font_size="0.7rem"),
            rx.text("PR", position="absolute", left="1.2rem", bottom="0.5rem", color="#6b7280", font_size="0.7rem"),
            rx.text("其他", position="absolute", left="0.5rem", top="4rem", color="#6b7280", font_size="0.7rem"),
            rx.box(
                rx.box(
                    "",
                    width="5.5rem",
                    height="5.5rem",
                    background="rgba(59, 130, 246, 0.22)",
                    border="2px solid #3b82f6",
                    transform="rotate(45deg)",
                    border_radius="0.4rem",
                ),
                display="flex",
                align_items="center",
                justify_content="center",
                height="100%",
            ),
            position="relative",
            height="10rem",
            background="#eff6ff",
            border_radius="0.5rem",
            width="100%",
        ),
        rx.box(
            rx.hstack(
                rx.text("● 出勤 18/20", color="#6b7280", font_size="0.75rem"),
                rx.text("● 考试 24/30", color="#6b7280", font_size="0.75rem"),
                spacing="4",
            ),
            rx.hstack(
                rx.text("● 代码 32/40", color="#6b7280", font_size="0.75rem"),
                rx.text("● PR 13.5/10", color="#6b7280", font_size="0.75rem"),
                spacing="4",
            ),
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def bar_item(label: str, value: str, height: str, color: str):
    return rx.vstack(
        rx.text(value, color="#6b7280", font_size="0.75rem"),
        rx.box(
            "",
            width="100%",
            height=height,
            background=color,
            border_radius="0.35rem 0.35rem 0 0",
        ),
        rx.text(label, color="#9ca3af", font_size="0.75rem"),
        spacing="1",
        align_items="center",
        width="100%",
        justify_content="end",
    )


def bar_chart_placeholder():
    return rx.hstack(
        bar_item("期中1", "22", "7.3rem", "#3b82f6"),
        bar_item("期中2", "28", "9.3rem", "#3b82f6"),
        bar_item("期末", "24", "8rem", "#60a5fa"),
        bar_item("补考", "18", "6rem", "#e5e7eb"),
        spacing="3",
        align_items="end",
        height="10rem",
        width="100%",
    )


def line_chart_placeholder():
    return rx.box(
        rx.hstack(
            rx.box("", width="0.55rem", height="0.55rem", border_radius="9999px", background="#93c5fd", margin_top="4.8rem"),
            rx.box("", width="0.55rem", height="0.55rem", border_radius="9999px", background="#60a5fa", margin_top="4.1rem"),
            rx.box("", width="0.55rem", height="0.55rem", border_radius="9999px", background="#3b82f6", margin_top="3.3rem"),
            rx.box("", width="0.55rem", height="0.55rem", border_radius="9999px", background="#2563eb", margin_top="2.4rem"),
            rx.box("", width="0.55rem", height="0.55rem", border_radius="9999px", background="#1d4ed8", margin_top="1.5rem"),
            rx.box("", width="0.7rem", height="0.7rem", border_radius="9999px", background="#1d4ed8", margin_top="0.8rem"),
            spacing="6",
            align_items="start",
        ),
        rx.text(
            "87.5",
            color="#2563eb",
            font_size="0.8rem",
            font_weight="700",
            position="absolute",
            right="1.5rem",
            top="1rem",
        ),
        height="10rem",
        background="#eff6ff",
        border_radius="0.5rem",
        padding="1rem",
        position="relative",
        overflow="hidden",
    )


def task_item(title: str, desc: str, level: str, action: str):
    bg = "#fef2f2" if level == "red" else "#fffbeb" if level == "yellow" else "#f9fafb"
    border = "#fee2e2" if level == "red" else "#fef3c7" if level == "yellow" else "#f3f4f6"
    dot = "#ef4444" if level == "red" else "#f59e0b" if level == "yellow" else "#22c55e"
    desc_color = "#ef4444" if level == "red" else "#ca8a04" if level == "yellow" else "#16a34a"

    return rx.hstack(
        rx.box(
            "",
            width="0.5rem",
            height="0.5rem",
            border_radius="9999px",
            background=dot,
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(title, color="#1f2937", font_size="0.875rem", font_weight="600"),
            rx.text(desc, color=desc_color, font_size="0.75rem"),
            spacing="1",
            align_items="start",
            flex="1",
        ),
        rx.text(action, color="#3b82f6" if action != "✓" else "#22c55e", font_size="0.75rem"),
        background=bg,
        border=f"1px solid {border}",
        border_radius="0.5rem",
        padding="0.75rem",
        width="100%",
        align_items="center",
    )


def notice_item(title: str, desc: str, unread: bool = False):
    return rx.hstack(
        rx.box(
            "",
            width="0.5rem",
            height="0.5rem",
            border_radius="9999px",
            background="#ef4444" if unread else "#d1d5db",
            margin_top="0.35rem",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(title, color="#1f2937" if unread else "#6b7280", font_size="0.875rem"),
            rx.text(desc, color="#9ca3af", font_size="0.75rem"),
            spacing="1",
            align_items="start",
        ),
        spacing="3",
        align_items="start",
        width="100%",
    )


def dashboard():
    return rx.box(
        sidebar(),

        rx.box(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.heading("仪表盘", size="5", color="#1f2937"),
                    rx.text(
                        "欢迎回来，张三 · 工程实践4 · 2025春",
                        color="#9ca3af",
                        font_size="0.875rem",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.text("🔔", font_size="1.1rem"),
                    width="2.25rem",
                    height="2.25rem",
                    border_radius="0.5rem",
                    border="1px solid #e5e7eb",
                    background="white",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    position="relative",
                ),
                spacing="3",
                align_items="center",
                width="100%",
                margin_bottom="2rem",
            ),

            # Score Cards
            rx.box(
                stat_card("综合总分", "87.5", "满分 100 分", "#2563eb"),
                stat_card("出勤得分", "18", "满分 20 分 · 出勤率 90%", "#16a34a"),
                stat_card("考试得分", "24", "满分 30 分", "#9333ea"),
                stat_card("代码 + PR", "45.5", "满分 50 分", "#f97316"),
                display="grid",
                grid_template_columns="repeat(4, minmax(0, 1fr))",
                gap="1.25rem",
                width="100%",
                margin_bottom="2rem",
            ),

            # Charts
            rx.box(
                chart_card("四维雷达图", radar_placeholder()),
                chart_card("历次考试得分", bar_chart_placeholder()),
                chart_card("总分变化曲线", line_chart_placeholder(), "最近更新：2025-05-24"),
                display="grid",
                grid_template_columns="repeat(3, minmax(0, 1fr))",
                gap="1.25rem",
                width="100%",
                margin_bottom="2rem",
            ),

            # Bottom
            rx.box(
                rx.box(
                    rx.hstack(
                        rx.text("即将到期任务", font_size="0.875rem", font_weight="700", color="#374151"),
                        rx.spacer(),
                        rx.text("查看全部", font_size="0.75rem", color="#3b82f6"),
                        width="100%",
                        margin_bottom="1rem",
                    ),
                    rx.vstack(
                        task_item("第7章 软件需求规格说明书", "截止：2025-05-27 23:59 · 剩余 2 天", "red", "提交"),
                        task_item("第8章 系统设计文档", "截止：2025-06-03 23:59 · 剩余 9 天", "yellow", "提交"),
                        task_item("第6章 数据库设计（已提交）", "已提交 · 待批改", "green", "✓"),
                        spacing="3",
                        width="100%",
                    ),
                    background="white",
                    border="1px solid #f3f4f6",
                    border_radius="0.75rem",
                    box_shadow="0 1px 3px rgba(0,0,0,0.05)",
                    padding="1.25rem",
                    width="100%",
                ),

                rx.box(
                    rx.hstack(
                        rx.text("课程公告", font_size="0.875rem", font_weight="700", color="#374151"),
                        rx.spacer(),
                        rx.text(
                            "2 未读",
                            font_size="0.75rem",
                            color="#dc2626",
                            background="#fee2e2",
                            padding="0.15rem 0.5rem",
                            border_radius="9999px",
                        ),
                        width="100%",
                        margin_bottom="1rem",
                    ),
                    rx.vstack(
                        notice_item("第7章截止时间延至5月27日", "2025-05-23 · 教师：李四", True),
                        notice_item("期末汇报安排（6月15日）已发布", "2025-05-21 · 教师：李四", True),
                        notice_item("第6章批改成绩已发布，请查看反馈", "2025-05-18 · 系统通知", False),
                        spacing="3",
                        width="100%",
                    ),
                    background="white",
                    border="1px solid #f3f4f6",
                    border_radius="0.75rem",
                    box_shadow="0 1px 3px rgba(0,0,0,0.05)",
                    padding="1.25rem",
                    width="100%",
                ),

                display="grid",
                grid_template_columns="repeat(2, minmax(0, 1fr))",
                gap="1.25rem",
                width="100%",
            ),

            margin_left="14rem",
            padding="2rem",
            min_height="100vh",
            background="#f9fafb",
        ),

        min_height="100vh",
        background="#f9fafb",
    )
