"""oaepp.components.toast_bar — 全局错误提示条。

从页面顶部 fixed 定位，5 色状态变体，支持自动消失和重试按钮。
"""

import reflex as rx

try:
    from oaepp.states.error import ErrorState
except ImportError:
    ErrorState = rx.State


def toast_bar() -> rx.Component:
    """全局 Toast 条。绑定 ErrorState.current_visible。

    - 按 severity 动态选择背景色 / 文字色
    - 有 retry_label 时显示重试按钮
    - 无错误时返回空白（不占位）
    """

    # 按 severity 动态选择背景色
    bg_color = rx.cond(
        ErrorState.current_severity == "error", "#fef2f2",
        rx.cond(
            ErrorState.current_severity == "warning", "#fefce8",
            rx.cond(
                ErrorState.current_severity == "success", "#f0fdf4",
                "#eff6ff",  # info / default
            ),
        ),
    )
    # 按 severity 动态选择文字色
    text_color = rx.cond(
        ErrorState.current_severity == "error", "#b91c1c",
        rx.cond(
            ErrorState.current_severity == "warning", "#a16207",
            rx.cond(
                ErrorState.current_severity == "success", "#15803d",
                "#1d4ed8",
            ),
        ),
    )

    return rx.cond(
        ErrorState.current_visible,
        rx.box(
            rx.hstack(
                # 消息文本
                rx.text(
                    ErrorState.current_message,
                    font_size="14px",
                    flex="1",
                ),
                # 重试按钮（仅当 retry_label 非空时渲染）
                rx.cond(
                    ErrorState.retry_label != "",
                    rx.button(
                        ErrorState.retry_label,
                        on_click=ErrorState.retry,
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                    ),
                ),
                # 关闭按钮
                rx.button(
                    "✕",
                    on_click=ErrorState.dismiss,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                width="100%",
                align="center",
                gap="8px",
            ),
            # 容器样式
            position="fixed",
            top="16px",
            left="50%",
            transform="translateX(-50%)",
            z_index="50",
            max_width="480px",
            width="calc(100% - 32px)",
            padding="12px 16px",
            background=bg_color,
            color=text_color,
            border_radius="8px",
            box_shadow="0 4px 12px rgba(0, 0, 0, 0.1)",
        ),
    )
