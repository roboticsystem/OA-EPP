"""
左侧菜单栏组件
"""
import reflex as rx
from states.auth_state import AuthState


def sidebar_item(icon: str, text: str, href: str, active: bool = False):
    """侧边栏菜单项"""
    return rx.link(
        rx.hstack(
            rx.html(icon),
            rx.text(text, size="2"),
            spacing="3",
            align="center",
        ),
        href=href,
        width="100%",
        padding="10px 12px",
        border_radius="8px",
        color_scheme="blue" if active else "gray",
        background="rgb(239, 246, 255)" if active else "transparent",
        _hover={"background": "rgb(243, 244, 246)" if not active else "rgb(219, 234, 254)"},
        color="rgb(37, 99, 235)" if active else "rgb(75, 85, 99)",
        font_weight="medium" if active else "normal",
        text_decoration="none",
    )


def sidebar() -> rx.Component:
    """侧边栏"""
    return rx.box(
        rx.vstack(
            # Logo区域
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("check-circle", size=20, color="white"),
                        width="32px",
                        height="32px",
                        background="rgb(37, 99, 235)",
                        border_radius="8px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text("OA-EPP", weight="bold", size="2", color="rgb(31, 41, 55)"),
                    spacing="3",
                    align="center",
                ),
                padding="20px",
                border_bottom="1px solid rgb(243, 244, 246)",
            ),
            
            # 导航菜单
            rx.vstack(
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
                    "仪表盘",
                    "/dashboard",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>',
                    "课程列表",
                    "/courses",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
                    "作业提交",
                    "/assignments",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
                    "成绩与反馈",
                    "/grades",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
                    "课堂签到",
                    "/attendance",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>',
                    "在线考试",
                    "/exam",
                    active=False,
                ),
                sidebar_item(
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>',
                    "个人资料",
                    "/profile",
                    active=True,
                ),
                spacing="1",
                padding="16px 12px",
                width="100%",
            ),
            
            # 底部用户信息
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.text(
                                AuthState.full_name.to(str)[0:1],
                                color="rgb(37, 99, 235)",
                                weight="bold",
                                size="2",
                            ),
                            width="32px",
                            height="32px",
                            border_radius="50%",
                            background="rgb(219, 234, 254)",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.vstack(
                            rx.text(AuthState.full_name, size="2", weight="medium", color="rgb(31, 41, 55)"),
                            rx.text(AuthState.student_no, size="1", color="rgb(156, 163, 175)"),
                            spacing="0",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.link(
                        rx.text("退出登录", size="1", color="rgb(156, 163, 175)", _hover={"color": "rgb(239, 68, 68)"}),
                        href="#",
                        on_click=AuthState.do_logout,
                        text_decoration="none",
                        width="100%",
                        text_align="center",
                        margin_top="12px",
                    ),
                    spacing="2",
                ),
                padding="16px",
                border_top="1px solid rgb(243, 244, 246)",
            ),
            spacing="0",
        ),
        width="224px",
        min_height="100vh",
        background="white",
        border_right="1px solid rgb(229, 231, 235)",
        position="fixed",
        left="0",
        top="0",
    )
