"""常用 UI 组件

学生用法：
    from oaepp.components.common import (
        stat_card, empty_state, loading_spinner,
        connection_banner, network_status_icon,
    )

    def dashboard_page():
        return page_layout(
            title="仪表盘",
            content=rx.vstack(
                connection_banner(),
                rx.grid(
                    stat_card("已选课程", 4, icon="book_open"),
                    stat_card("待提交作业", 2, icon="file_text"),
                    stat_card("平均成绩", "85.5", icon="bar_chart_3"),
                    columns="3",
                    spacing="4",
                ),
            ),
        )
"""
import reflex as rx

from oaepp.states.error import ErrorState


def stat_card(
    label: str,
    value,
    icon: str = "info",
) -> rx.Component:
    """统计卡片 — 用于仪表盘、成绩等页面的数字展示

    Args:
        label: 指标名称（如 "已选课程"、"待提交作业"）
        value: 指标值（数字或字符串）
        icon: 图标标签名（Reflex icon tag，默认 "info"）

    Returns:
        卡片组件
    """
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(tag=icon, size=24, color="blue"),
                padding="12px",
                background_color="var(--blue-3)",
                border_radius="8px",
            ),
            rx.vstack(
                rx.text(label, size="2", color="gray"),
                rx.heading(str(value), size="5"),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        width="100%",
        padding="20px",
    )


def empty_state(message: str, icon: str = "circle_help") -> rx.Component:
    """空数据提示 — 无课程、无作业等场景

    Args:
        message: 提示文字（如 "暂无已选课程"）
        icon: 图标标签名

    Returns:
        空状态组件
    """
    return rx.center(
        rx.vstack(
            rx.icon(tag=icon, size=40, color="gray"),
            rx.text(message, color="gray", size="3"),
            align="center",
            spacing="3",
            padding="48px 24px",
        ),
        width="100%",
    )


def loading_spinner(text: str = "加载中...") -> rx.Component:
    """加载状态指示器

    Args:
        text: 加载提示文字

    Returns:
        加载组件
    """
    return rx.center(
        rx.hstack(
            rx.spinner(color="blue", size="3"),
            rx.text(text, color="gray", size="3"),
            spacing="3",
            align="center",
        ),
        padding="48px 24px",
        width="100%",
    )


def data_table(
    columns: list[str],
    rows: list[list],
    header_color: str = "gray",
) -> rx.Component:
    """通用数据表格

    Args:
        columns: 表头列名列表，如 ["姓名", "学号", "成绩"]
        rows: 数据行，每行为列表，如 [["张三", "2024000001", "85"]]
        header_color: 表头背景色

    Returns:
        表格组件
    """
    return rx.box(
        rx.html(
            "<table style='width:100%;border-collapse:collapse;'>"
            + "<thead><tr>"
            + "".join(
                f"<th style='text-align:left;padding:10px 12px;"
                f"border-bottom:2px solid var(--gray-5);"
                f"font-size:14px;color:var(--gray-11);'>{c}</th>"
                for c in columns
            )
            + "</tr></thead>"
            + "<tbody>"
            + "".join(
                "<tr>"
                + "".join(
                    f"<td style='padding:10px 12px;border-bottom:1px solid var(--gray-4);"
                    f"font-size:14px;'>{cell}</td>"
                    for cell in row
                )
                + "</tr>"
                for row in rows
            )
            + "</tbody></table>"
        ),
        width="100%",
        overflow_x="auto",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  网络状态组件（F-S-050 网络韧性）
# ═══════════════════════════════════════════════════════════════════════════

def connection_banner() -> rx.Component:
    """网络连接状态横幅 — 离线时显示红色提示条

    监听 ErrorState.network_online，离线时自动显示重连提示。

    用法：
        在 page_layout 的 content 顶部放置：
        rx.vstack(
            connection_banner(),
            ... 其他内容 ...
        )
    """
    return rx.cond(
        ErrorState.network_online == False,  # noqa: E712
        rx.box(
            rx.hstack(
                rx.icon(tag="wifi_off", size=16, color="white"),
                rx.text("网络已断开，正在尝试重连...", color="white", size="2"),
                rx.spinner(color="white", size="1"),
                spacing="2",
                align="center",
                justify="center",
            ),
            padding="8px 16px",
            background_color="var(--red-9)",
            width="100%",
            class_name="oaepp-connection-banner",
        ),
    )


def network_status_icon() -> rx.Component:
    """网络状态指示器小图标 — 可放入顶栏或页脚

    在线时显示绿色 WiFi 图标，离线时显示红色断开图标。

    用法：
        rx.hstack(
            rx.heading("仪表盘"),
            rx.spacer(),
            network_status_icon(),
        )
    """
    return rx.cond(
        ErrorState.network_online,
        rx.icon(tag="wifi", size=16, color="var(--green-9)"),
        rx.icon(tag="wifi_off", size=16, color="var(--red-9)"),
    )
