import reflex as rx
from oaepp.components.sidebar import sidebar
from oaepp.components.stat_card import stat_card


def header() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.text("仪表盘", font_size="xl", font_weight="bold", color="gray.800"),
                rx.text(
                    "欢迎回来，张三 · 工程实践4 · 2025春",
                    font_size="sm",
                    color="gray.400",
                    margin_top="2px",
                ),
            ),
            rx.box(
                rx.box(
                    rx.icon("bell", size=20, color="gray.500"),
                    width="36px",
                    height="36px",
                    border_radius="lg",
                    border="1px solid",
                    border_color="gray.200",
                    bg="white",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    position="relative",
                    cursor="pointer",
                ),
                rx.box(
                    "2",
                    position="absolute",
                    top="-4px",
                    right="-4px",
                    width="16px",
                    height="16px",
                    bg="red.500",
                    color="white",
                    font_size="xs",
                    border_radius="full",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                position="relative",
            ),
            display="flex",
            align_items="center",
            justify_content="space-between",
        ),
        margin_bottom="32px",
    )


def score_cards() -> rx.Component:
    return rx.grid(
        stat_card("综合总分", "87.5", "满分 100 分", "blue"),
        stat_card("出勤得分", "18", "满分 20 分 · 出勤率 90%", "green"),
        stat_card("考试得分", "24", "满分 30 分", "purple"),
        stat_card("代码 + PR", "45.5", "满分 50 分", "orange"),
        grid_template_columns="repeat(4, 1fr)",
        gap="20px",
        margin_bottom="32px",
    )


def radar_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.text("四维雷达图", font_size="sm", font_weight="semibold", color="gray.700"),
        rx.box(
            rx.html(
                """<svg viewBox="0 0 160 140" width="160" height="140">
                <polygon points="80,10 140,50 120,120 40,120 20,50" fill="none" stroke="#e5e7eb" stroke-width="1.5"/>
                <polygon points="80,30 120,58 108,104 52,104 40,58" fill="none" stroke="#e5e7eb" stroke-width="1"/>
                <polygon points="80,50 100,66 94,90 66,90 60,66" fill="none" stroke="#e5e7eb" stroke-width="1"/>
                <polygon points="80,22 128,56 111,112 49,112 32,54" fill="#3b82f6" fill-opacity="0.25" stroke="#3b82f6" stroke-width="2"/>
                <text x="75" y="8" font-size="9" fill="#6b7280">出勤</text>
                <text x="136" y="54" font-size="9" fill="#6b7280">考试</text>
                <text x="112" y="130" font-size="9" fill="#6b7280">代码</text>
                <text x="28" y="130" font-size="9" fill="#6b7280">PR</text>
                <text x="2" y="54" font-size="9" fill="#6b7280">其他</text>
                </svg>"""
            ),
            display="flex",
            align_items="center",
            justify_content="center",
            height="160px",
            bg="blue.50",
            border_radius="lg",
        ),
        rx.box(
            rx.box(rx.text("出勤 18/20", font_size="xs", color="gray.500"), display="flex", align_items="center", gap="6px"),
            rx.box(rx.text("考试 24/30", font_size="xs", color="gray.500"), display="flex", align_items="center", gap="6px"),
            rx.box(rx.text("代码 32/40", font_size="xs", color="gray.500"), display="flex", align_items="center", gap="6px"),
            rx.box(rx.text("PR 13.5/10", font_size="xs", color="gray.500"), display="flex", align_items="center", gap="6px"),
            display="grid",
            grid_template_columns="repeat(2, 1fr)",
            gap="8px",
            margin_top="12px",
        ),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )


def bar_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.text("历次考试得分", font_size="sm", font_weight="semibold", color="gray.700"),
        rx.box(
            bar_item("22", "73%", "期中1"),
            bar_item("28", "93%", "期中2"),
            bar_item("24", "80%", "期末", is_active=True),
            bar_item("18", "60%", "补考", is_gray=True),
            display="flex",
            align_items="flex-end",
            gap="12px",
            height="160px",
            padding_x="8px",
        ),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )


def bar_item(score: str, height_pct: str, label: str, is_active: bool = False, is_gray: bool = False) -> rx.Component:
    color = "gray.200" if is_gray else ("blue.400" if is_active else "blue.500")
    return rx.box(
        rx.text(score, font_size="xs", color="gray.500"),
        rx.box(
            bg=color,
            border_radius_top="4px",
            width="100%",
            height=height_pct,
        ),
        rx.text(label, font_size="xs", color="gray.400"),
        display="flex",
        flex_direction="column",
        align_items="center",
        gap="4px",
        flex="1",
    )


def line_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.text("总分变化曲线", font_size="sm", font_weight="semibold", color="gray.700"),
        rx.box(
            rx.html(
                """<svg viewBox="0 0 200 120" width="100%" height="100%">
                <polyline points="10,100 40,85 70,78 100,65 130,52 160,45 190,38" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="10,100 40,85 70,78 100,65 130,52 160,45 190,38" fill="url(#grad)" fill-opacity="0.12"/>
                <defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="white"/></linearGradient></defs>
                <circle cx="190" cy="38" r="3.5" fill="#3b82f6"/>
                <text x="140" y="35" font-size="9" fill="#3b82f6">87.5</text>
                </svg>"""
            ),
            height="160px",
            display="flex",
            align_items="center",
            justify_content="center",
            bg="blue.50",
            border_radius="lg",
            position="relative",
            overflow="hidden",
        ),
        rx.text("最近更新：2025-05-24", font_size="xs", color="gray.400", text_align="right", margin_top="8px"),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )


def charts_row() -> rx.Component:
    return rx.grid(
        radar_chart_placeholder(),
        bar_chart_placeholder(),
        line_chart_placeholder(),
        grid_template_columns="repeat(3, 1fr)",
        gap="20px",
        margin_bottom="32px",
    )


def pending_tasks() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text("即将到期任务", font_size="sm", font_weight="semibold", color="gray.700"),
            rx.link("查看全部", href="/assignments", font_size="xs", color="blue.500", _hover={"text_decoration": "underline"}),
            display="flex",
            align_items="center",
            justify_content="space-between",
            margin_bottom="16px",
        ),
        rx.vstack(
            task_item("第7章 软件需求规格说明书", "截止：2025-05-27 23:59 · 剩余 2 天", "red", "提交"),
            task_item("第8章 系统设计文档", "截止：2025-06-03 23:59 · 剩余 9 天", "yellow", "提交"),
            task_item("第6章 数据库设计（已提交）", "已提交 · 待批改", "green", "✓", is_done=True),
            spacing="3",
        ),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )


def task_item(title: str, deadline: str, color: str, action: str, is_done: bool = False) -> rx.Component:
    bg_map = {"red": "red.50", "yellow": "yellow.50", "green": "gray.50"}
    border_map = {"red": "red.100", "yellow": "yellow.100", "green": "gray.100"}
    dot_map = {"red": "red.500", "yellow": "yellow.500", "green": "green.500"}
    text_color_map = {"red": "red.500", "yellow": "yellow.600", "green": "green.600"}

    return rx.box(
        rx.box(
            width="8px",
            height="8px",
            border_radius="full",
            bg=dot_map.get(color, "gray.300"),
            flex_shrink="0",
        ),
        rx.box(
            rx.text(title, font_size="sm", color="gray.800", font_weight="medium"),
            rx.text(deadline, font_size="xs", color=text_color_map.get(color, "gray.400")),
            flex="1",
            min_width="0",
        ),
        rx.link(
            action,
            href="/assignments",
            font_size="xs",
            color="blue.500" if not is_done else "green.500",
            flex_shrink="0",
        ),
        display="flex",
        align_items="center",
        gap="12px",
        padding="12px",
        bg=bg_map.get(color, "gray.50"),
        border="1px solid",
        border_color=border_map.get(color, "gray.100"),
        border_radius="lg",
    )


def notifications() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text("课程公告", font_size="sm", font_weight="semibold", color="gray.700"),
            rx.box(
                "2 未读",
                font_size="xs",
                bg="red.100",
                color="red.600",
                padding_x="8px",
                padding_y="2px",
                border_radius="full",
            ),
            display="flex",
            align_items="center",
            justify_content="space-between",
            margin_bottom="16px",
        ),
        rx.vstack(
            notification_item("第7章截止时间延至5月27日", "2025-05-23 · 教师：李四", is_unread=True),
            notification_item("期末汇报安排（6月15日）已发布", "2025-05-21 · 教师：李四", is_unread=True),
            notification_item("第6章批改成绩已发布，请查看反馈", "2025-05-18 · 系统通知", is_unread=False),
            spacing="3",
        ),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )


def notification_item(text: str, meta: str, is_unread: bool = False) -> rx.Component:
    return rx.box(
        rx.box(
            width="8px",
            height="8px",
            border_radius="full",
            bg="red.500" if is_unread else "gray.300",
            margin_top="6px",
            flex_shrink="0",
        ),
        rx.box(
            rx.text(text, font_size="sm", color="gray.800"),
            rx.text(meta, font_size="xs", color="gray.400", margin_top="2px"),
        ),
        display="flex",
        gap="12px",
    )


def bottom_row() -> rx.Component:
    return rx.grid(
        pending_tasks(),
        notifications(),
        grid_template_columns="repeat(2, 1fr)",
        gap="20px",
    )


def dashboard_content() -> rx.Component:
    return rx.box(
        header(),
        score_cards(),
        charts_row(),
        bottom_row(),
        margin_left="224px",
        flex="1",
        padding="32px",
        bg="gray.50",
        min_height="100vh",
    )


def dashboard_page() -> rx.Component:
    return rx.box(
        sidebar(),
        dashboard_content(),
        display="flex",
        min_height="100vh",
        bg="gray.50",
    )