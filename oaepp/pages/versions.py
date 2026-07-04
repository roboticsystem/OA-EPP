"""F-S-021 提交版本历史页面

路由：/versions?assignment_id=X
功能：
- 展示指定作业的提交版本历史（最新在前）
- 最新版本标注为「评阅版本」
- 支持查看和下载历史版本文件
- 允许重新提交（若作业开放 resubmit）

使用全局组件：
- oaepp.components.layout.page_layout — 统一页面布局（侧边栏+顶栏）
- oaepp.components.common.empty_state — 空数据提示
- oaepp.components.common.loading_spinner — 加载状态指示器
"""

try:
    import reflex as rx
except Exception:
    rx = None

versions_page = None

if rx is not None:
    from oaepp.states.submission import SubmissionState
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state, loading_spinner

    # ═════════════════════════════════════════════════════════════════════
    #  子组件
    # ═════════════════════════════════════════════════════════════════════

    def _version_status_badge(version: dict):
        """版本状态标签：评阅版本 / 待批改 / 已批改 / 已发回 / 迟交"""
        return rx.cond(
            version.get("is_latest", False),
            # 最新版本 → 绿色"评阅版本"标签
            rx.hstack(
                rx.badge("评阅版本", color_scheme="green", variant="solid"),
                rx.cond(
                    version.get("is_late", False),
                    rx.badge("迟交", color_scheme="orange", variant="soft", margin_left="2"),
                ),
                spacing="2",
            ),
            # 历史版本 → 根据 grading_status 显示对应标签
            rx.hstack(
                rx.cond(
                    version.get("grading_status", "pending") == "pending",
                    rx.badge("待批改", color_scheme="gray", variant="soft"),
                    rx.cond(
                        version.get("grading_status", "") == "graded",
                        rx.badge("已批改", color_scheme="blue", variant="soft"),
                        rx.badge("已发回", color_scheme="purple", variant="soft"),
                    ),
                ),
                rx.cond(
                    version.get("is_late", False),
                    rx.badge("迟交", color_scheme="orange", variant="soft", margin_left="2"),
                ),
                spacing="2",
            ),
        )

    def _version_row(version: dict):
        """单条版本记录行。"""
        return rx.hstack(
            rx.text(f"v{version.get('version_no', '-')}", weight="bold", width="60px"),
            rx.text(version.get("submitted_at_display", "—"), width="160px", size="2"),
            _version_status_badge(version),
            rx.hstack(
                rx.cond(
                    version.get("file_url", "") != "",
                    rx.link(
                        rx.button("下载", size="1", color_scheme="blue"),
                        href=version.get("file_url", ""),
                        is_external=True,
                    ),
                    rx.text("—", color="gray"),
                ),
                rx.cond(
                    version.get("text_preview", "") != "",
                    rx.text(
                        version.get("text_preview", ""),
                        color="gray",
                        size="1",
                        max_width="200px",
                        overflow="hidden",
                    ),
                ),
                spacing="2",
                align="center",
            ),
            spacing="4",
            align="center",
            padding="8px 0",
            border_bottom="1px solid #e5e7eb",
            width="100%",
        )

    def _resubmit_form():
        """重新提交表单。"""
        return rx.box(
            rx.vstack(
                rx.divider(),
                rx.heading("提交新版本", size="4"),
                rx.text(
                    "文本内容（可选）",
                    size="2",
                    color="gray",
                ),
                rx.text_area(
                    placeholder="请输入提交说明或文本内容…",
                    value=SubmissionState.form_text_content,
                    on_change=SubmissionState.set_form_text_content,
                    width="100%",
                    min_height="100px",
                ),
                rx.text(
                    "文件链接（可选，支持 PDF / DOCX / ZIP / 代码文件）",
                    size="2",
                    color="gray",
                ),
                rx.input(
                    placeholder="https://example.com/file.pdf",
                    value=SubmissionState.form_file_url,
                    on_change=SubmissionState.set_form_file_url,
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "提交新版本",
                        color_scheme="green",
                        on_click=SubmissionState.handle_submit,
                    ),
                    rx.cond(
                        SubmissionState.submit_message != "",
                        rx.box(
                            rx.text(
                                SubmissionState.submit_message,
                                size="2",
                                weight="medium",
                            ),
                            padding="6px 12px",
                            background="#f0fdf4",
                            border_radius="6px",
                        ),
                    ),
                    spacing="4",
                    align="center",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="16px",
            background="#fafafa",
            border_radius="8px",
            border="1px solid #e5e7eb",
            margin_top="16px",
        )

    # ═════════════════════════════════════════════════════════════════════
    #  主页面内容
    # ═════════════════════════════════════════════════════════════════════

    def _versions_content():
        """页面主体内容（供 page_layout 包装）。"""
        return rx.vstack(
            # 作业信息
            rx.box(
                rx.hstack(
                    rx.text("作业:", color="gray", weight="medium"),
                    rx.text(
                        rx.cond(
                            SubmissionState.current_assignment_title != "",
                            SubmissionState.current_assignment_title,
                            "请从作业列表进入此页面",
                        ),
                        weight="bold",
                    ),
                    rx.cond(
                        SubmissionState.allow_resubmit,
                        rx.badge("允许重交", color_scheme="green", variant="soft"),
                        rx.badge("禁止重交", color_scheme="red", variant="soft"),
                    ),
                    spacing="3",
                    align="center",
                ),
                padding="12px 16px",
                background="#f8fafc",
                border_radius="8px",
                border="1px solid #e2e8f0",
            ),

            # 加载中提示 — 使用全局 loading_spinner 组件
            rx.cond(
                SubmissionState.is_loading,
                loading_spinner("正在加载版本历史…"),
            ),

            # 版本历史表格 / 空数据
            rx.cond(
                SubmissionState.versions.length() > 0,
                rx.box(
                    # 版本数量 — 使用 State 计算属性，避免 f-string 提前求值
                    rx.text(
                        SubmissionState.version_count_text,
                        size="2",
                        color="gray",
                        weight="medium",
                    ),
                    rx.hstack(
                        rx.text("版本", weight="bold", size="2", color="gray", width="60px"),
                        rx.text("提交时间", weight="bold", size="2", color="gray", width="160px"),
                        rx.text("状态", weight="bold", size="2", color="gray", width="120px"),
                        rx.text("内容 / 操作", weight="bold", size="2", color="gray"),
                        spacing="4",
                        padding="8px 0",
                        border_bottom="2px solid #d1d5db",
                        width="100%",
                    ),
                    rx.foreach(SubmissionState.versions, _version_row),
                    width="100%",
                ),
                rx.cond(
                    SubmissionState.is_loading,
                    rx.center(),  # 加载中，已在上面显示
                    empty_state("暂无提交记录"),
                ),
            ),

            # 重新提交表单（仅在允许重交时显示）
            rx.cond(
                SubmissionState.allow_resubmit,
                _resubmit_form(),
            ),

            spacing="4",
            width="100%",
            align="stretch",
        )

    # ═════════════════════════════════════════════════════════════════════
    #  主页面入口
    # ═════════════════════════════════════════════════════════════════════

    def versions_page():
        """提交版本历史页面。

        路由：/versions?assignment_id=X

        功能：
        - 版本历史列表（最新版本标注「评阅版本」）
        - 历史版本文件下载
        - 重新提交表单（需作业允许 resubmit）
        """
        return page_layout(
            title="提交版本历史",
            content=rx.box(
                _versions_content(),
                on_mount=SubmissionState.load_from_route,
            ),
        )


# ═════════════════════════════════════════════════════════════════════
#  辅助函数
# ═════════════════════════════════════════════════════════════════════

def _format_time(ts: str) -> str:
    """格式化时间戳为可读格式。"""
    if not ts:
        return "—"
    try:
        # 尝试解析 ISO 格式
        if "T" in ts:
            dt_part = ts.split("T")[0]
            time_part = ts.split("T")[1].split(".")[0][:5] if "." in ts.split("T")[1] else ts.split("T")[1][:5]
            return f"{dt_part} {time_part}"
        if " " in ts:
            parts = ts.split(" ")
            return f"{parts[0]} {parts[1][:5]}" if len(parts) > 1 else ts[:16]
        return ts[:16]
    except Exception:
        return ts[:16]


def _truncate(text: str, max_len: int = 60) -> str:
    """截断文本，超出部分用省略号表示。"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"
