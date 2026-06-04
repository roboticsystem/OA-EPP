"""OA-EPP Reflex 共享布局组件

顶部导航栏 + 左侧边栏 + 主内容区的三段式布局。
遵循 生成面向 Reflex 的静态快速原型提示词.md 的视觉与布局规范。
"""

import reflex as rx

# ── 导航菜单项 ──
NAV_ITEMS = [
    ("总览仪表盘", "/dashboard", "M3 12l2-2m0 0l7-7 7 7M5 15v7h14v-7"),
    ("课程学习", "/courses", "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"),
    ("作业提交", "/assignments", "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"),
    ("成绩查看", "/grades", "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"),
    ("课堂签到", "/attendance", "M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"),
    ("在线考试", "/exam", "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"),
    ("个人资料", "/profile", "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"),
]

SIDEBAR_WIDTH = "14rem"


def _icon(svg_path: str) -> rx.Component:
    return rx.html(
        f'<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{svg_path}"/></svg>'
    )


def navbar() -> rx.Component:
    """顶部导航栏"""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.html(
                    '<svg class="w-6 h-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>'
                ),
                rx.text("OA-EPP 工程实践平台", class_name="text-white font-bold text-sm"),
                spacing="3",
                align="center",
            ),
            rx.hstack(
                rx.text("同学你好", class_name="text-white text-sm"),
                rx.box(
                    rx.text("张", class_name="text-blue-700 font-bold text-xs"),
                    class_name="w-8 h-8 bg-white rounded-full flex items-center justify-center",
                ),
                spacing="3",
                align="center",
            ),
            justify="between",
            align="center",
            padding_x="6",
            height="100%",
        ),
        class_name="bg-blue-700 h-12",
        width="100%",
    )


def sidebar(current_page: str = "/courses") -> rx.Component:
    """左侧边栏"""
    items = []
    for label, href, svg_path in NAV_ITEMS:
        is_active = href == current_page
        items.append(
            rx.link(
                rx.hstack(
                    _icon(svg_path),
                    rx.text(label, class_name="text-sm font-medium"),
                    spacing="3",
                    align="center",
                    class_name=(
                        "w-full px-4 py-2.5 rounded-lg transition-colors "
                        + ("bg-blue-50 text-blue-700" if is_active else "text-gray-600 hover:bg-gray-50")
                    ),
                ),
                href=href,
                width="100%",
                text_decoration="none",
                _hover={"text_decoration": "none"},
            )
        )

    return rx.box(
        rx.vstack(items, spacing="1", padding="4", width="100%"),
        class_name="bg-white border-r border-gray-200",
        width=SIDEBAR_WIDTH,
        min_height="calc(100vh - 3rem)",
    )


def page_wrapper(content: rx.Component, current_page: str = "/courses") -> rx.Component:
    """三段式布局包装器：将页面内容放入主内容区"""
    return rx.box(
        navbar(),
        rx.hstack(
            sidebar(current_page),
            rx.box(
                rx.container(
                    content,
                    max_width="1200px",
                    width="100%",
                    padding="0",
                ),
                class_name="bg-gray-50 flex-1 p-6",
                min_height="calc(100vh - 3rem)",
                width="100%",
            ),
            align="start",
            spacing="0",
            width="100%",
        ),
        width="100%",
        min_height="100vh",
        class_name="bg-gray-50",
    )
