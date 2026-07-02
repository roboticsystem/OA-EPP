"""页面骨架组件 — 统一布局（响应式）

提供 page_layout() 函数，学生页面统一使用此函数包装内容。
包含：桌面侧边栏 + 顶栏 + 内容区 + 移动端抽屉 + 移动端底部导航栏。

响应式断点：移动端 <768px，桌面端 ≥768px（由 CSS 媒体查询控制）

学生用法：
    from oaepp.components.layout import page_layout

    def my_page():
        return page_layout(
            title="我的页面",
            content=rx.vstack(...),
        )
"""
import reflex as rx

from oaepp.states import ResponsiveState


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

# 移动端底部导航栏核心入口（5项）
_MOBILE_BOTTOM_ITEMS = [
    ("dashboard", "layout_dashboard"),
    ("courses", "book_open"),
    ("assignments", "file_text"),
    ("grades", "bar_chart_3"),
    ("profile", "user"),
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


# ═══════════════════════════════════════════════════════════════════════════
#  桌面端侧边栏（移动端通过 CSS class "oaepp-sidebar" 隐藏）
# ═══════════════════════════════════════════════════════════════════════════

def _sidebar() -> rx.Component:
    """桌面端固定侧边栏导航"""
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
        class_name="oaepp-sidebar",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  移动端组件（桌面端通过 CSS 隐藏）
# ═══════════════════════════════════════════════════════════════════════════

def _hamburger_button() -> rx.Component:
    """移动端汉堡菜单按钮（桌面端 CSS 隐藏）"""
    return rx.icon_button(
        rx.icon(tag="menu", size=24),
        on_click=ResponsiveState.toggle_sidebar,
        variant="ghost",
        color_scheme="gray",
        class_name="oaepp-hamburger-btn",
        aria_label="打开菜单",
    )


def _mobile_drawer() -> rx.Component:
    """移动端侧边导航抽屉（从左侧滑入 + 遮罩层）

    仅在 sidebar_open 时渲染，遮罩层点击关闭。
    """
    return rx.cond(
        ResponsiveState.sidebar_open,
        rx.box(
            # 遮罩层（点击关闭）
            rx.box(
                on_click=ResponsiveState.close_sidebar,
                class_name="oaepp-drawer-backdrop",
            ),
            # 抽屉面板
            rx.box(
                rx.vstack(
                    rx.box(height="16px"),  # 顶部留白
                    rx.heading("OA-EPP", size="5", color_scheme="blue"),
                    rx.text("工程实践管理平台", size="1", color="gray"),
                    rx.divider(),
                    rx.vstack(
                        *[
                            _nav_item(label, route, icon)
                            for label, route, icon in _NAV_ITEMS
                        ],
                        spacing="1",
                        width="100%",
                        padding="8px 0",
                    ),
                    spacing="0",
                    padding="16px",
                    width="100%",
                ),
                class_name="oaepp-drawer-panel",
            ),
            class_name="oaepp-drawer",
        ),
    )


def _mobile_bottom_nav() -> rx.Component:
    """移动端底部固定导航栏（5个核心入口）

    包含：课程主页 / 课程 / 作业 / 成绩 / 资料
    桌面端通过 CSS 隐藏。
    """
    return rx.hstack(
        *[
            rx.link(
                rx.vstack(
                    rx.icon(tag=icon, size=20),
                    rx.text(label, size="1"),
                    spacing="0",
                    align="center",
                ),
                href=f"/{label}" if label != "dashboard" else "/dashboard",
                class_name="oaepp-bottom-nav-item",
            )
            for label, icon in _MOBILE_BOTTOM_ITEMS
        ],
        justify="between",
        align="center",
        padding="8px 12px",
        background_color="white",
        border_top="1px solid var(--gray-5)",
        class_name="oaepp-mobile-bottom-nav",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  顶栏（桌面端 + 移动端通用，桌面端隐藏汉堡按钮）
# ═══════════════════════════════════════════════════════════════════════════

def _topbar(title: str) -> rx.Component:
    """顶栏：页面标题 + 移动端汉堡按钮"""
    return rx.box(
        rx.hstack(
            _hamburger_button(),
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


# ═══════════════════════════════════════════════════════════════════════════
#  统一页面布局
# ═══════════════════════════════════════════════════════════════════════════

def page_layout(title: str, content: rx.Component) -> rx.Component:
    """统一响应式页面布局

    - 桌面端（≥768px）：固定侧边栏 + 顶栏 + 内容区
    - 移动端（<768px）：顶栏（含汉堡按钮）+ 内容区 + 底部导航栏
      + 可展开的侧边抽屉

    Args:
        title: 页面标题（显示在顶栏）
        content: 页面主体内容

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
        # 桌面侧边栏（CSS 在移动端隐藏）
        _sidebar(),
        # 移动端抽屉（仅 sidebar_open 时渲染）
        _mobile_drawer(),
        # 主内容区
        rx.box(
            _topbar(title),
            rx.box(
                content,
                padding="24px",
                width="100%",
                class_name="oaepp-content-area",
            ),
            class_name="oaepp-main-content",
        ),
        # 移动端底部导航栏（CSS 在桌面端隐藏）
        _mobile_bottom_nav(),
        # 网络状态监听脚本
        rx.script("""
            window.addEventListener('online', function() {
                console.log('[OA-EPP] Network restored');
            });
            window.addEventListener('offline', function() {
                console.log('[OA-EPP] Network lost');
            });
        """),
        width="100%",
    )
