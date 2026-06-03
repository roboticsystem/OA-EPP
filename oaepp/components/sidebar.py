import reflex as rx


def nav_item(label: str, icon: str, href: str = "#", active: bool = False):
    return rx.link(
        rx.box(
            rx.hstack(
                rx.box(
                    icon,
                    width="1.5rem",
                    text_align="center",
                    font_size="0.95rem",
                ),
                rx.text(label),
                spacing="3",
                align_items="center",
            ),
            padding="0.65rem 0.75rem",
            border_radius="0.5rem",
            background="#eff6ff" if active else "transparent",
            color="#1d4ed8" if active else "#4b5563",
            font_weight="600" if active else "400",
            font_size="0.875rem",
            _hover={
                "background": "#f9fafb",
                "color": "#2563eb",
            },
        ),
        href=href,
        text_decoration="none",
        width="100%",
    )


def sidebar():
    return rx.box(
        rx.vstack(
            # Brand
            rx.box(
                rx.hstack(
                    rx.box(
                        "✓",
                        width="2rem",
                        height="2rem",
                        border_radius="0.5rem",
                        background="#2563eb",
                        color="white",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        font_weight="700",
                    ),
                    rx.text(
                        "OA-EPP",
                        font_weight="700",
                        color="#1f2937",
                        font_size="0.9rem",
                    ),
                    spacing="3",
                    align_items="center",
                ),
                padding="1.25rem",
                border_bottom="1px solid #f3f4f6",
                width="100%",
            ),

            # Nav
            rx.vstack(
                nav_item("仪表盘", "⌂", "/dashboard", active=True),
                nav_item("课程列表", "📘"),
                nav_item("作业提交", "📝"),
                nav_item("成绩与反馈", "📊"),
                nav_item("课堂签到", "✅"),
                nav_item("在线考试", "✍"),
                nav_item("个人资料", "👤"),
                spacing="1",
                padding="1rem 0.75rem",
                width="100%",
                align_items="stretch",
            ),

            rx.spacer(),

            # User info
            rx.box(
                rx.hstack(
                    rx.box(
                        "张",
                        width="2rem",
                        height="2rem",
                        border_radius="9999px",
                        background="#dbeafe",
                        color="#1d4ed8",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        font_weight="700",
                        font_size="0.875rem",
                    ),
                    rx.vstack(
                        rx.text(
                            "张三",
                            font_size="0.875rem",
                            font_weight="600",
                            color="#1f2937",
                        ),
                        rx.text(
                            "2021001001",
                            font_size="0.75rem",
                            color="#9ca3af",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    spacing="3",
                    align_items="center",
                ),
                rx.link(
                    "退出登录",
                    href="/",
                    display="block",
                    text_align="center",
                    color="#9ca3af",
                    font_size="0.75rem",
                    margin_top="0.75rem",
                    text_decoration="none",
                    _hover={"color": "#ef4444"},
                ),
                padding="1rem",
                border_top="1px solid #f3f4f6",
                width="100%",
            ),

            height="100%",
            width="100%",
            spacing="0",
            align_items="stretch",
        ),
        width="14rem",
        height="100vh",
        background="white",
        border_right="1px solid #e5e7eb",
        position="fixed",
        left="0",
        top="0",
        z_index="10",
    )
