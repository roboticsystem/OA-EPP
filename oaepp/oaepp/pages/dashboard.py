import reflex as rx
from oaepp.components.sidebar import sidebar
from oaepp.components.stat_card import stat_card
from oaepp.theme import c, FONT

CARD_STYLE = {
    "background": "white",
    "border_radius": "12px",
    "border": f"1px solid {c('gray.100')}",
    "box_shadow": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "padding": "20px",
}


def header() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.el.h1(
                    "仪表盘",
                    style={
                        "font_size": "20px",
                        "font_weight": "700",
                        "color": c("gray.800"),
                        "margin": "0",
                        "font_family": FONT,
                    },
                ),
                rx.el.p(
                    "欢迎回来，张三 · 工程实践4 · 2025春",
                    style={
                        "font_size": "14px",
                        "color": c("gray.400"),
                        "margin": "2px 0 0 0",
                        "font_family": FONT,
                    },
                ),
            ),
            rx.box(
                rx.box(
                    rx.icon("bell", size=20, color=c("gray.500")),
                    style={
                        "width": "36px",
                        "height": "36px",
                        "border_radius": "8px",
                        "border": f"1px solid {c('gray.200')}",
                        "background": "white",
                        "display": "flex",
                        "align_items": "center",
                        "justify_content": "center",
                        "position": "relative",
                        "cursor": "pointer",
                        "color": c("gray.500"),
                        "transition": "color 0.15s",
                    },
                ),
                rx.el.span(
                    "2",
                    style={
                        "position": "absolute",
                        "top": "-4px",
                        "right": "-4px",
                        "width": "16px",
                        "height": "16px",
                        "background": c("red.500"),
                        "color": "white",
                        "font_size": "12px",
                        "border_radius": "9999px",
                        "display": "flex",
                        "align_items": "center",
                        "justify_content": "center",
                        "font_family": FONT,
                    },
                ),
                style={"position": "relative"},
            ),
            style={
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
            },
        ),
        style={"margin_bottom": "32px"},
    )


def score_cards() -> rx.Component:
    return rx.box(
        stat_card("综合总分", "87.5", "满分 100 分", "blue"),
        stat_card("出勤得分", "18", "满分 20 分 · 出勤率 90%", "green"),
        stat_card("考试得分", "24", "满分 30 分", "purple"),
        stat_card("代码 + PR", "45.5", "满分 50 分", "orange"),
        style={
            "display": "grid",
            "grid_template_columns": "repeat(4, 1fr)",
            "gap": "20px",
            "margin_bottom": "32px",
        },
    )


def legend_item(dot_color: str, text: str) -> rx.Component:
    return rx.box(
        rx.el.span(
            "",
            style={
                "width": "10px",
                "height": "10px",
                "border_radius": "9999px",
                "background": dot_color,
                "display": "inline-block",
                "flex_shrink": "0",
            },
        ),
        rx.el.span(
            text,
            style={
                "font_size": "12px",
                "color": c("gray.500"),
                "font_family": FONT,
            },
        ),
        style={
            "display": "flex",
            "align_items": "center",
            "gap": "6px",
        },
    )


def radar_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.el.h3(
            "四维雷达图",
            style={
                "font_size": "14px",
                "font_weight": "600",
                "color": c("gray.700"),
                "margin": "0 0 16px 0",
                "font_family": FONT,
            },
        ),
        rx.box(
            rx.html(
                '<svg viewBox="0 0 160 140" width="160" height="140">'
                '<polygon points="80,10 140,50 120,120 40,120 20,50" fill="none" stroke="#e5e7eb" stroke-width="1.5"/>'
                '<polygon points="80,30 120,58 108,104 52,104 40,58" fill="none" stroke="#e5e7eb" stroke-width="1"/>'
                '<polygon points="80,50 100,66 94,90 66,90 60,66" fill="none" stroke="#e5e7eb" stroke-width="1"/>'
                '<polygon points="80,22 128,56 111,112 49,112 32,54" fill="#3b82f6" fill-opacity="0.25" stroke="#3b82f6" stroke-width="2"/>'
                '<text x="75" y="8" font-size="9" fill="#6b7280">出勤</text>'
                '<text x="136" y="54" font-size="9" fill="#6b7280">考试</text>'
                '<text x="112" y="130" font-size="9" fill="#6b7280">代码</text>'
                '<text x="28" y="130" font-size="9" fill="#6b7280">PR</text>'
                '<text x="2" y="54" font-size="9" fill="#6b7280">其他</text>'
                "</svg>"
            ),
            style={
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "height": "160px",
                "background": c("blue.50"),
                "border_radius": "8px",
            },
        ),
        rx.box(
            legend_item(c("green.400"), "出勤 18/20"),
            legend_item(c("purple.400"), "考试 24/30"),
            legend_item(c("orange.400"), "代码 32/40"),
            legend_item(c("blue.400"), "PR 13.5/10"),
            style={
                "display": "grid",
                "grid_template_columns": "repeat(2, 1fr)",
                "gap": "8px",
                "margin_top": "12px",
            },
        ),
        style=CARD_STYLE,
    )


def bar_item(
    score: str, height_pct: str, label: str, bar_color: str
) -> rx.Component:
    return rx.box(
        rx.el.span(
            score,
            style={
                "font_size": "12px",
                "color": c("gray.500"),
                "font_family": FONT,
            },
        ),
        rx.el.div(
            style={
                "width": "100%",
                "height": height_pct,
                "background": bar_color,
                "border_radius": "4px 4px 0 0",
            },
        ),
        rx.el.span(
            label,
            style={
                "font_size": "12px",
                "color": c("gray.400"),
                "font_family": FONT,
            },
        ),
        style={
            "display": "flex",
            "flex_direction": "column",
            "align_items": "center",
            "gap": "4px",
            "flex": "1",
        },
    )


def bar_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.el.h3(
            "历次考试得分",
            style={
                "font_size": "14px",
                "font_weight": "600",
                "color": c("gray.700"),
                "margin": "0 0 16px 0",
                "font_family": FONT,
            },
        ),
        rx.box(
            bar_item("22", "73%", "期中1", c("blue.500")),
            bar_item("28", "93%", "期中2", c("blue.500")),
            bar_item("24", "80%", "期末", c("blue.400")),
            bar_item("18", "60%", "补考", c("gray.200")),
            style={
                "display": "flex",
                "align_items": "flex_end",
                "gap": "12px",
                "height": "160px",
                "padding": "0 8px",
            },
        ),
        style=CARD_STYLE,
    )


def line_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.el.h3(
            "总分变化曲线",
            style={
                "font_size": "14px",
                "font_weight": "600",
                "color": c("gray.700"),
                "margin": "0 0 16px 0",
                "font_family": FONT,
            },
        ),
        rx.box(
            rx.html(
                '<svg viewBox="0 0 200 120" width="100%" height="100%">'
                '<polyline points="10,100 40,85 70,78 100,65 130,52 160,45 190,38" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
                '<polyline points="10,100 40,85 70,78 100,65 130,52 160,45 190,38" fill="url(#grad)" fill-opacity="0.12"/>'
                '<defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="white"/></linearGradient></defs>'
                '<circle cx="190" cy="38" r="3.5" fill="#3b82f6"/>'
                '<text x="140" y="35" font-size="9" fill="#3b82f6">87.5</text>'
                "</svg>"
            ),
            style={
                "height": "160px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "background": c("blue.50"),
                "border_radius": "8px",
                "position": "relative",
                "overflow": "hidden",
            },
        ),
        rx.el.p(
            "最近更新：2025-05-24",
            style={
                "font_size": "12px",
                "color": c("gray.400"),
                "text_align": "right",
                "margin": "8px 0 0 0",
                "font_family": FONT,
            },
        ),
        style=CARD_STYLE,
    )


def charts_row() -> rx.Component:
    return rx.box(
        radar_chart_placeholder(),
        bar_chart_placeholder(),
        line_chart_placeholder(),
        style={
            "display": "grid",
            "grid_template_columns": "repeat(3, 1fr)",
            "gap": "20px",
            "margin_bottom": "32px",
        },
    )


def task_item(
    title: str,
    deadline: str,
    bg_color: str,
    border_color: str,
    dot_color: str,
    text_color: str,
    action: str,
    is_done: bool = False,
) -> rx.Component:
    return rx.box(
        rx.el.span(
            "",
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": "9999px",
                "background": dot_color,
                "flex_shrink": "0",
            },
        ),
        rx.box(
            rx.el.p(
                title,
                style={
                    "font_size": "14px",
                    "color": c("gray.800"),
                    "font_weight": "500",
                    "margin": "0",
                    "white_space": "nowrap",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "font_family": FONT,
                },
            ),
            rx.el.p(
                deadline,
                style={
                    "font_size": "12px",
                    "color": text_color,
                    "margin": "0",
                    "font_family": FONT,
                },
            ),
            style={"flex": "1", "min_width": "0"},
        ),
        rx.el.a(
            action,
            href="/assignments",
            style={
                "font_size": "12px",
                "color": c("blue.500") if not is_done else c("green.500"),
                "flex_shrink": "0",
                "text_decoration": "none",
                "font_family": FONT,
            },
        ),
        style={
            "display": "flex",
            "align_items": "center",
            "gap": "12px",
            "padding": "12px",
            "background": bg_color,
            "border": f"1px solid {border_color}",
            "border_radius": "8px",
        },
    )


def pending_tasks() -> rx.Component:
    return rx.box(
        rx.box(
            rx.el.h3(
                "即将到期任务",
                style={
                    "font_size": "14px",
                    "font_weight": "600",
                    "color": c("gray.700"),
                    "margin": "0",
                    "font_family": FONT,
                },
            ),
            rx.el.a(
                "查看全部",
                href="/assignments",
                style={
                    "font_size": "12px",
                    "color": c("blue.500"),
                    "text_decoration": "none",
                    "font_family": FONT,
                },
            ),
            style={
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "margin_bottom": "16px",
            },
        ),
        rx.box(
            task_item(
                "第7章 软件需求规格说明书",
                "截止：2025-05-27 23:59 · 剩余 2 天",
                c("red.50"),
                c("red.100"),
                c("red.500"),
                c("red.500"),
                "提交",
            ),
            task_item(
                "第8章 系统设计文档",
                "截止：2025-06-03 23:59 · 剩余 9 天",
                c("yellow.50"),
                c("yellow.100"),
                c("yellow.500"),
                c("yellow.600"),
                "提交",
            ),
            task_item(
                "第6章 数据库设计（已提交）",
                "已提交 · 待批改",
                c("gray.50"),
                c("gray.100"),
                c("green.500"),
                c("green.600"),
                "✓",
                is_done=True,
            ),
            style={"display": "flex", "flex_direction": "column", "gap": "12px"},
        ),
        style=CARD_STYLE,
    )


def notification_item(text: str, meta: str, is_unread: bool = False) -> rx.Component:
    return rx.box(
        rx.el.span(
            "",
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": "9999px",
                "background": c("red.500") if is_unread else c("gray.300"),
                "margin_top": "6px",
                "flex_shrink": "0",
            },
        ),
        rx.box(
            rx.el.p(
                text,
                style={
                    "font_size": "14px",
                    "color": c("gray.800") if is_unread else c("gray.500"),
                    "margin": "0",
                    "font_family": FONT,
                },
            ),
            rx.el.p(
                meta,
                style={
                    "font_size": "12px",
                    "color": c("gray.400"),
                    "margin": "2px 0 0 0",
                    "font_family": FONT,
                },
            ),
        ),
        style={"display": "flex", "gap": "12px"},
    )


def notifications() -> rx.Component:
    return rx.box(
        rx.box(
            rx.el.h3(
                "课程公告",
                style={
                    "font_size": "14px",
                    "font_weight": "600",
                    "color": c("gray.700"),
                    "margin": "0",
                    "font_family": FONT,
                },
            ),
            rx.el.span(
                "2 未读",
                style={
                    "font_size": "12px",
                    "background": c("red.100"),
                    "color": c("red.600"),
                    "padding": "2px 8px",
                    "border_radius": "9999px",
                    "font_family": FONT,
                },
            ),
            style={
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "margin_bottom": "16px",
            },
        ),
        rx.box(
            notification_item("第7章截止时间延至5月27日", "2025-05-23 · 教师：李四", True),
            notification_item("期末汇报安排（6月15日）已发布", "2025-05-21 · 教师：李四", True),
            notification_item("第6章批改成绩已发布，请查看反馈", "2025-05-18 · 系统通知", False),
            style={"display": "flex", "flex_direction": "column", "gap": "12px"},
        ),
        style=CARD_STYLE,
    )


def bottom_row() -> rx.Component:
    return rx.box(
        pending_tasks(),
        notifications(),
        style={
            "display": "grid",
            "grid_template_columns": "repeat(2, 1fr)",
            "gap": "20px",
        },
    )


def dashboard_content() -> rx.Component:
    return rx.box(
        header(),
        score_cards(),
        charts_row(),
        bottom_row(),
        style={
            "margin_left": "224px",
            "flex": "1",
            "padding": "32px",
            "background": c("gray.50"),
            "min_height": "100vh",
            "font_family": FONT,
        },
    )


def dashboard_page() -> rx.Component:
    return rx.box(
        sidebar(),
        dashboard_content(),
        style={
            "display": "flex",
            "min_height": "100vh",
            "background": c("gray.50"),
        },
    )
