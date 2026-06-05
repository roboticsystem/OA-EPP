"""提交详情页面

展示特定学生特定任务的提交详情，包含：
- 提交时间
- 版本号
- 提交内容
- 批改状态
- 迟交标记
"""

try:
    import reflex as rx
except Exception:
    rx = None

from ..states.dashboard import DashboardState


def _grading_status_badge(status: str):
    """批改状态标签"""
    styles = {
        "pending": {"bg": "bg-yellow-100", "text": "text-yellow-800", "label": "待批改"},
        "graded": {"bg": "bg-blue-100", "text": "text-blue-800", "label": "已批改"},
        "returned": {"bg": "bg-green-100", "text": "text-green-800", "label": "已发还"}
    }
    style = styles.get(status, {"bg": "bg-gray-100", "text": "text-gray-800", "label": "未知"})
    
    return rx.badge(
        style["label"],
        class_name=f"{style['bg']} {style['text']}",
        variant="outline"
    )


def submission_detail_page():
    """提交详情页面主组件"""
    if rx is None:
        return """<div>Reflex not available</div>"""
    
    # 从 URL 参数获取 student_id 和 assignment_id
    student_id = rx.State.router.page.params.get("student_id", "0")
    assignment_id = rx.State.router.page.params.get("assignment_id", "0")
    
    # 获取提交详情
    detail = DashboardState.get_submission_detail(int(student_id), int(assignment_id))
    
    if not detail:
        return rx.container(
            rx.vstack(
                rx.heading("提交详情", size="xl", margin_bottom="16px"),
                rx.text("未找到相关提交记录", color="red"),
                rx.button("返回看板", on_click=lambda: rx.redirect("/dashboard")),
                spacing="16"
            ),
            padding="16px"
        )
    
    return rx.container(
        rx.vstack(
            # 页面标题
            rx.hstack(
                rx.heading("提交详情", size="xl"),
                rx.spacer(),
                rx.button("返回看板", on_click=lambda: rx.redirect("/dashboard")),
                spacing="16"
            ),
            
            # 提交信息卡片
            rx.box(
                rx.vstack(
                    # 作业标题
                    rx.heading(detail["assignment_title"], size="lg", margin_bottom="16px"),
                    
                    # 基本信息
                    rx.grid(
                        rx.box(
                            rx.text("版本号", font_size="12px", color="#666", margin_bottom="4px"),
                            rx.text(f"v{detail['version_no']}", font_size="16px", font_weight="bold")
                        ),
                        rx.box(
                            rx.text("提交时间", font_size="12px", color="#666", margin_bottom="4px"),
                            rx.text(detail["submitted_at"].strftime("%Y-%m-%d %H:%M:%S"), font_size="16px")
                        ),
                        rx.box(
                            rx.text("截止时间", font_size="12px", color="#666", margin_bottom="4px"),
                            rx.text(detail["deadline"].strftime("%Y-%m-%d %H:%M:%S"), font_size="16px")
                        ),
                        rx.box(
                            rx.text("批改状态", font_size="12px", color="#666", margin_bottom="4px"),
                            _grading_status_badge(detail["grading_status"])
                        ),
                        columns="2",
                        gap="16px",
                        width="100%"
                    ),
                    
                    # 迟交标记
                    rx.box(
                        rx.text("⚠ 迟交", font_size="14px", color="#dc2626", font_weight="bold"),
                        padding="8px 12px",
                        background_color="#fef2f2",
                        border_radius="4px",
                        margin_top="16px",
                        display="block" if detail["is_late"] else "none"
                    ),
                    
                    # 提交内容
                    rx.box(
                        rx.vstack(
                            rx.text("提交内容", font_size="12px", color="#666", margin_bottom="8px"),
                            rx.text_area(
                                value=detail["text_content"] or "",
                                read_only=True,
                                height="200px",
                                width="100%",
                                font_family="monospace",
                                font_size="14px"
                            ),
                            spacing="8"
                        ),
                        margin_top="16px",
                        padding="16px",
                        background_color="#f9fafb",
                        border="1px solid #e5e7eb",
                        border_radius="8px"
                    ),
                    
                    # 文件附件
                    rx.box(
                        rx.vstack(
                            rx.text("附件", font_size="12px", color="#666", margin_bottom="8px"),
                            rx.link(
                                detail["file_url"] or "无附件",
                                href=detail["file_url"],
                                target="_blank",
                                font_size="14px"
                            ),
                            spacing="8"
                        ),
                        margin_top="16px",
                        padding="16px",
                        background_color="#f9fafb",
                        border="1px solid #e5e7eb",
                        border_radius="8px"
                    ),
                    
                    spacing="8",
                    width="100%"
                ),
                padding="24px",
                background_color="white",
                border="1px solid #e5e7eb",
                border_radius="12px",
                box_shadow="0 4px 6px -1px rgba(0,0,0,0.1)"
            ),
            
            spacing="16",
            padding="16px",
            width="100%",
            max_width="800px"
        )
    )
