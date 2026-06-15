"""F-S-012 公告与通知 — 学生端页面

路由: /notifications（由 app.py 自动发现注册）
页面函数: notifications_page()
状态类: 使用 states.notice.NoticeState

截图匹配要素：
- 标题"📢 公告与通知" + 右上角红色未读数字徽章 + 浅黄色背景
- 分类标签：全部 / 公告 / 截止提醒 / 成绩通知
- 未读项：蓝色竖线左边框 + 粗体标题 + "● 未读"标记
- 已读项：灰色标题
- 底部"全部标记已读"灰色填充按钮
"""

import reflex as rx

from oaepp.components.layout import page_layout
from oaepp.components.common import empty_state, loading_spinner

try:
    from oaepp.states.notice import NoticeState
except ModuleNotFoundError:
    from states.notice import NoticeState


# ── 分类配置 ──
CATEGORY_MAP = {
    "announcement": ("公告", "blue"),
    "deadline": ("截止提醒", "orange"),
    "grade": ("成绩通知", "green"),
}

CATEGORY_TABS = [
    ("all", "全部", "inbox"),
    ("announcement", "公告", "megaphone"),
    ("deadline", "截止提醒", "clock"),
    ("grade", "成绩通知", "graduation-cap"),
]


def category_badge(cat: str) -> rx.Component:
    """分类标签徽章"""
    label, color = CATEGORY_MAP.get(cat, ("通知", "gray"))
    return rx.badge(label, color_scheme=color, size="1", variant="soft")


def notification_card(n: dict) -> rx.Component:
    """通知卡片 — 未读带蓝色左边框，匹配截图布局（无内容摘要）"""
    nid = n.get("id", 0)
    cat = n.get("category", "")
    cat_label, cat_color = CATEGORY_MAP.get(cat, ("通知", "gray"))
    is_read = n.get("is_read", True)

    return rx.hstack(
        # 蓝色竖线（未读时显示）
        rx.box(
            width="4px",
            height="100%",
            bg=rx.cond(is_read, "transparent", "blue.500"),
            border_radius="2px",
            flex_shrink=0,
        ),
        # 左侧：标题
        rx.text(
            n.get("title", ""),
            font_weight=rx.cond(is_read, "normal", "bold"),
            color=rx.cond(is_read, "gray.500", "gray.900"),
            font_size="md",
            flex_grow=1,
        ),
        rx.spacer(),
        # 右侧：分类标签 + 时间 + 未读标记
        rx.hstack(
            rx.badge(cat_label, color_scheme=cat_color, size="1", variant="soft"),
            rx.text(
                n.get("created_at", ""),
                font_size="xs", color="gray.400",
            ),
            rx.cond(
                is_read,
                rx.fragment(),
                rx.hstack(
                    rx.icon("circle", size=8, color="blue.500"),
                    rx.text("未读", font_size="xs", color="blue.500"),
                    spacing="1",
                ),
            ),
            spacing="2", align="center",
        ),
        width="100%",
        padding="12px 16px",
        border_bottom="1px solid var(--gray-100)",
        on_click=NoticeState.mark_as_read(nid),
        cursor="pointer",
        _hover={"bg": "var(--gray-50)"},
        spacing="2", align="center",
    )


def tab_button(tab: str, label: str, icon_name: str) -> rx.Component:
    """分类标签按钮"""
    is_active = NoticeState.current_tab == tab
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14),
            rx.text(label),
            spacing="1",
        ),
        size="2",
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        on_click=NoticeState.switch_tab(tab),
    )


def pagination_controls() -> rx.Component:
    """分页控制"""
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page(NoticeState.current_page - 1),
            is_disabled=~NoticeState.can_go_prev,
        ),
        rx.text(
            NoticeState.current_page,
            " / ",
            NoticeState.total_pages,
            font_size="sm", color="gray.500",
        ),
        rx.button(
            rx.icon("chevron-right", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page(NoticeState.current_page + 1),
            is_disabled=~NoticeState.can_go_next,
        ),
        width="100%", justify="center", spacing="4",
    )


def notifications_page() -> rx.Component:
    """学生端 — 公告与通知页面（由 app.py 自动发现注册为 /notifications）"""
    content = rx.vstack(
        # 标题栏 + 未读徽章（浅黄色背景）
        rx.hstack(
            rx.heading("📢 公告与通知", size="6"),
            rx.spacer(),
            rx.cond(
                NoticeState.has_unread,
                rx.badge(
                    NoticeState.unread_count,
                    color_scheme="red",
                    variant="solid",
                    size="2",
                    border_radius="full",
                ),
                rx.fragment(),
            ),
            width="100%", align="center",
            padding="12px 16px",
            bg="#FFF8E1",
            border_radius="8px",
        ),

        # 分类标签
        rx.hstack(
            *[tab_button(t, l, i) for t, l, i in CATEGORY_TABS],
            width="100%", justify="center", spacing="2",
            wrap="wrap",
        ),

        # 内容区域
        rx.cond(
            NoticeState.loading,
            loading_spinner("加载通知中..."),
            rx.cond(
                NoticeState.error,
                rx.vstack(
                    rx.icon("alert-circle", size=32, color="red.500"),
                    rx.text(NoticeState.error, color="red.500"),
                    rx.button("重试", on_click=NoticeState.refresh),
                    spacing="2", align="center", padding="40px",
                ),
                rx.cond(
                    NoticeState.has_data,
                    rx.vstack(
                        rx.foreach(NoticeState.notices, notification_card),
                        rx.cond(
                            NoticeState.show_pagination,
                            pagination_controls(),
                            rx.fragment(),
                        ),
                        width="100%", spacing="0",
                    ),
                    empty_state("暂无通知", icon="inbox"),
                ),
            ),
        ),

        # 全部标记已读按钮
        rx.cond(
            NoticeState.has_unread,
            rx.button(
                "全部标记已读",
                width="100%",
                variant="soft",
                color_scheme="gray",
                on_click=NoticeState.mark_all_read,
                margin_top="12px",
            ),
            rx.fragment(),
        ),

        # Toast 提示
        rx.toast.provider(),

        width="100%",
        max_width="800px",
        margin="0 auto",
        spacing="4",
        on_mount=NoticeState.load_notices,
    )

    return page_layout(title="公告与通知", content=content)
