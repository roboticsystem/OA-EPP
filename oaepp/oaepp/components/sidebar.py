import reflex as rx
from oaepp.theme import c, FONT


def sidebar() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.box(
                    rx.icon("shield-check", size=20, color="white"),
                    style={
                        "width": "32px",
                        "height": "32px",
                        "background": c("blue.600"),
                        "border_radius": "8px",
                        "display": "flex",
                        "align_items": "center",
                        "justify_content": "center",
                    },
                ),
                rx.el.span(
                    "OA-EPP",
                    style={
                        "font_weight": "700",
                        "color": c("gray.800"),
                        "font_size": "14px",
                        "font_family": FONT,
                    },
                ),
                style={
                    "display": "flex",
                    "align_items": "center",
                    "gap": "10px",
                },
            ),
            style={
                "padding": "20px",
                "border_bottom": f"1px solid {c('gray.100')}",
            },
        ),
        rx.box(
            sidebar_item("仪表盘", "layout-dashboard", "/dashboard", is_active=True),
            sidebar_item("课程列表", "book-open", "/courses"),
            sidebar_item("作业提交", "clipboard-list", "/assignments"),
            sidebar_item("成绩与反馈", "bar-chart-3", "/grades"),
            sidebar_item("课堂签到", "clipboard-check", "/attendance"),
            sidebar_item("在线考试", "pen-tool", "/exam"),
            sidebar_item("个人资料", "user", "/profile"),
            style={
                "display": "flex",
                "flex_direction": "column",
                "gap": "4px",
                "padding": "16px 12px",
                "flex": "1",
            },
        ),
        rx.box(
            rx.box(
                rx.box(
                    rx.el.span(
                        "张",
                        style={
                            "font_weight": "700",
                            "color": c("blue.700"),
                            "font_size": "14px",
                            "font_family": FONT,
                        },
                    ),
                    style={
                        "width": "32px",
                        "height": "32px",
                        "border_radius": "9999px",
                        "background": c("blue.100"),
                        "display": "flex",
                        "align_items": "center",
                        "justify_content": "center",
                    },
                ),
                rx.box(
                    rx.el.p(
                        "张三",
                        style={
                            "font_size": "14px",
                            "font_weight": "500",
                            "color": c("gray.800"),
                            "font_family": FONT,
                            "margin": "0",
                            "white_space": "nowrap",
                            "overflow": "hidden",
                            "text_overflow": "ellipsis",
                        },
                    ),
                    rx.el.p(
                        "2021001001",
                        style={
                            "font_size": "12px",
                            "color": c("gray.400"),
                            "font_family": FONT,
                            "margin": "0",
                            "white_space": "nowrap",
                            "overflow": "hidden",
                            "text_overflow": "ellipsis",
                        },
                    ),
                    style={"flex": "1", "min_width": "0"},
                ),
                style={
                    "display": "flex",
                    "align_items": "center",
                    "gap": "12px",
                },
            ),
            rx.el.a(
                "退出登录",
                href="/login",
                style={
                    "display": "block",
                    "margin_top": "12px",
                    "text_align": "center",
                    "font_size": "12px",
                    "color": c("gray.400"),
                    "text_decoration": "none",
                    "font_family": FONT,
                    "transition": "color 0.15s",
                },
            ),
            style={
                "padding": "16px",
                "border_top": f"1px solid {c('gray.100')}",
            },
        ),
        style={
            "width": "224px",
            "background": "white",
            "border_right": f"1px solid {c('gray.200')}",
            "display": "flex",
            "flex_direction": "column",
            "min_height": "100vh",
            "position": "fixed",
            "left": "0",
            "top": "0",
            "font_family": FONT,
        },
    )


def sidebar_item(
    text: str, icon_name: str, href: str, is_active: bool = False
) -> rx.Component:
    return rx.el.a(
        rx.box(
            rx.icon(icon_name, size=16),
            rx.el.span(
                text,
                style={
                    "font_size": "14px",
                    "font_family": FONT,
                },
            ),
            style={
                "display": "flex",
                "align_items": "center",
                "gap": "12px",
                "padding": "8px 12px",
                "border_radius": "8px",
                "background": c("blue.50") if is_active else "transparent",
                "color": c("blue.700") if is_active else c("gray.600"),
                "font_weight": "500" if is_active else "400",
                "font_family": FONT,
                "font_size": "14px",
                "text_decoration": "none",
                "transition": "background 0.15s, color 0.15s",
                "width": "100%",
                "cursor": "pointer",
            },
        ),
        href=href,
        style={"text_decoration": "none", "display": "block", "width": "100%"},
    )
