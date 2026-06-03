import reflex as rx


def sidebar() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.box(
                    rx.icon("shield-check", size=20, color="white"),
                    width="32px",
                    height="32px",
                    bg="blue.600",
                    border_radius="lg",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text("OA-EPP", font_weight="bold", color="gray.800", font_size="sm"),
                display="flex",
                align_items="center",
                gap="2.5",
            ),
            padding_x="20px",
            padding_y="20px",
            border_bottom="1px solid",
            border_color="gray.100",
        ),
        rx.vstack(
            sidebar_item("仪表盘", "layout-dashboard", "/dashboard", is_active=True),
            sidebar_item("课程列表", "book-open", "/courses"),
            sidebar_item("作业提交", "clipboard-list", "/assignments"),
            sidebar_item("成绩与反馈", "bar-chart-3", "/grades"),
            sidebar_item("课堂签到", "clipboard-check", "/attendance"),
            sidebar_item("在线考试", "pen-tool", "/exam"),
            sidebar_item("个人资料", "user", "/profile"),
            spacing="1",
            padding_x="12px",
            padding_y="16px",
            flex="1",
        ),
        rx.box(
            rx.box(
                rx.box(
                    rx.text("张", font_weight="bold", color="blue.700", font_size="sm"),
                    width="32px",
                    height="32px",
                    border_radius="full",
                    bg="blue.100",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.box(
                    rx.text("张三", font_size="sm", font_weight="medium", color="gray.800"),
                    rx.text("2021001001", font_size="xs", color="gray.400"),
                    flex="1",
                    min_width="0",
                ),
                display="flex",
                align_items="center",
                gap="3",
            ),
            rx.link(
                "退出登录",
                href="/login",
                font_size="xs",
                color="gray.400",
                _hover={"color": "red.500"},
                margin_top="12px",
                display="block",
                text_align="center",
            ),
            padding_x="16px",
            padding_y="16px",
            border_top="1px solid",
            border_color="gray.100",
        ),
        width="224px",
        bg="white",
        border_right="1px solid",
        border_color="gray.200",
        display="flex",
        flex_direction="column",
        min_height="100vh",
        position="fixed",
        left="0",
        top="0",
    )


def sidebar_item(
    text: str, icon_name: str, href: str, is_active: bool = False
) -> rx.Component:
    return rx.link(
        rx.box(
            rx.icon(icon_name, size=16),
            rx.text(text, font_size="sm"),
            display="flex",
            align_items="center",
            gap="12px",
            padding_x="12px",
            padding_y="8px",
            border_radius="lg",
            bg="blue.50" if is_active else "transparent",
            color="blue.700" if is_active else "gray.600",
            font_weight="medium" if is_active else "normal",
            _hover={"bg": "gray.50"} if not is_active else {},
            width="100%",
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )