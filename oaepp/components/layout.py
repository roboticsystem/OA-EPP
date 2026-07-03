"""页面骨架组件 — 统一布局

提供 page_layout() 函数，学生页面统一使用此函数包装内容。
包含：侧边栏导航 + 顶栏 + 内容区。

学生用法：
    from oaepp.components.layout import page_layout

    def my_page():
        return page_layout(
            title="我的页面",
            content=rx.vstack(...),
        )
"""
import reflex as rx


# ── 导航菜单项 ──────────────────────────────────────────────────────────
_NAV_ITEMS = [
    ("课程主页", "/dashboard", "layout_dashboard"),
    ("我的课程", "/courses", "book_open"),
    ("作业提交", "/assignments", "file_text"),
    ("成绩看板", "/grades", "bar_chart_3"),
    ("课堂点名", "/attendance", "user_check"),
    ("在线考试", "/exam", "clipboard_check"),
    ("个人资料", "/profile", "user"),
]


def _nav_item(label: str, route: str, icon_tag: str) -> rx.Component:
    """单个导航项 — 高亮当前路由"""
    return rx.link(
        rx.hstack(
            rx.icon(tag=icon_tag, size=18),
            rx.text(label, size="3"),
            spacing="3",
            align="center",
            width="100%",
            padding="10px 14px",
            border_radius="8px",
            background_color=rx.cond(
                rx.State.router.page.path == route,
                "var(--blue-3)",
                "transparent",
            ),
            color=rx.cond(
                rx.State.router.page.path == route,
                "var(--blue-9)",
                "var(--gray-11)",
            ),
            _hover={
                "background_color": rx.cond(
                    rx.State.router.page.path == route,
                    "var(--blue-3)",
                    "var(--gray-4)",
                ),
            },
        ),
        href=route,
        width="100%",
        text_decoration="none",
    )


def _sidebar() -> rx.Component:
    """侧边栏导航"""
    return rx.box(
        rx.vstack(
            # Logo / 系统名称
            rx.vstack(
                rx.heading("OA-EPP", size="5", color_scheme="blue"),
                rx.text("工程实践管理平台", size="1", color="gray"),
                align="center",
                padding="20px 16px",
                width="100%",
            ),
            rx.divider(),
            # 导航列表
            rx.vstack(
                *[_nav_item(label, route, icon) for label, route, icon in _NAV_ITEMS],
                spacing="1",
                width="100%",
                padding="8px 12px",
            ),
            # 底部占位
            rx.box(flex="1"),
            spacing="0",
            width="100%",
            height="100%",
        ),
        width="240px",
        min_height="100vh",
        background_color="var(--gray-2)",
        border_right="1px solid var(--gray-5)",
        position="fixed",
        left="0",
        top="0",
        overflow_y="auto",
    )


def _topbar(title: str) -> rx.Component:
    """顶栏：页面标题"""
    return rx.box(
        rx.hstack(
            rx.heading(title, size="5"),
            rx.box(flex="1"),
            align="center",
            width="100%",
            padding="16px 24px",
            border_bottom="1px solid var(--gray-5)",
            background_color="white",
        ),
        width="100%",
    )


def page_layout(title: str, content: rx.Component) -> rx.Component:
    """统一页面布局：侧边栏 + 顶栏 + 内容区

    Args:
        title: 页面标题（显示在顶栏）
        content: 页面主体内容（学生传入自己的组件）

    Returns:
        完整的页面布局组件

    用法示例：
        def dashboard_page():
            return page_layout(
                title="仪表盘",
                content=rx.vstack(
                    stat_card("已提交作业", 3),
                    stat_card("待批改", 1),
                ),
            )
    """
    return rx.box(
        _sidebar(),
        # 主内容区（左侧留出侧边栏宽度）
        rx.box(
            _topbar(title),
            rx.box(
                content,
                padding="24px",
                width="100%",
            ),
            margin_left="240px",
            min_height="100vh",
            background_color="var(--gray-1)",
        ),
        width="100%",
    )
