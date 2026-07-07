"""F-S-020 作业提交页面（学生端）

对应原型：prototype/assignments.html
路由：/assignments （由 app.py 自动发现机制注册）

功能：学生登录后浏览活跃作业、提交文本+文件、
      查看提交历史（含版本号）。
"""
try:
    import reflex as rx
except Exception:
    rx = None

assignments_page = None
if rx is not None:
    try:
        from components.layout import page_layout
    except ImportError:
        from oaepp.components.layout import page_layout

    try:
        from states.assignments import AssignmentsState
    except ImportError:
        from oaepp.states.assignments import AssignmentsState


    # ── 登录提示组件 ──
    def _login_prompt() -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.icon(tag="log_in", size=48, color="var(--gray-8)"),
                rx.heading("请先登录", size="5"),
                rx.text(
                    "请通过首页登录后再访问作业提交",
                    color="gray",
                    size="2",
                ),
                align="center",
                spacing="3",
                padding="40px",
            ),
            width="100%",
            max_width="500px",
            margin="0 auto",
        )


    # ── 作业卡片组件 ──
    def _assignment_card(assignment: dict) -> rx.Component:
        """单个作业卡片"""
        aid = assignment["id"]
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(assignment["title"], size="4"),
                    rx.cond(
                        assignment["is_past_deadline"],
                        rx.badge(
                            "已截止",
                            color_scheme="red",
                            variant="soft",
                        ),
                        rx.cond(
                            assignment["remaining"] != "",
                            rx.badge(
                                assignment["remaining"],
                                color_scheme="green",
                                variant="soft",
                            ),
                            rx.badge(
                                "即将截止",
                                color_scheme="orange",
                                variant="soft",
                            ),
                        ),
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.text(
                    assignment.get("description") or "暂无描述",
                    color="gray",
                    size="2",
                ),
                rx.hstack(
                    rx.text(
                        f"截止：{assignment['deadline']}",
                        size="1",
                        color="gray",
                    ),
                    rx.text(
                        f"格式：{assignment['allowed_formats']}",
                        size="1",
                        color="gray",
                    ),
                    rx.text(
                        f"上限：{assignment['max_file_size'] // (1024*1024)}MB",
                        size="1",
                        color="gray",
                    ),
                    spacing="4",
                ),
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="upload", size=16),
                            rx.text("提交作业"),
                            spacing="2",
                        ),
                        on_click=lambda: AssignmentsState.select_assignment(  # type: ignore
                            aid
                        ),
                        color_scheme="blue",
                        size="2",
                        disabled=assignment["is_past_deadline"],
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="history", size=16),
                            rx.text("查看历史"),
                            spacing="2",
                        ),
                        on_click=[
                            lambda: AssignmentsState.select_assignment(  # type: ignore
                                aid
                            ),
                            AssignmentsState.load_history,  # type: ignore
                        ],
                        variant="outline",
                        size="2",
                    ),
                    spacing="2",
                ),
                spacing="2",
                align="stretch",
                width="100%",
            ),
            padding="16px",
            border_radius="10px",
            background="white",
            border="1px solid var(--gray-4)",
            box_shadow="0 1px 3px rgba(0,0,0,0.04)",
            width="100%",
        )


    # ── 提交面板 ──
    def _submit_panel() -> rx.Component:
        """提交面板 — 文本输入 + 文件上传 + 提交按钮"""
        return rx.cond(
            AssignmentsState.selected_assignment_id != "",  # type: ignore
            rx.box(
                rx.vstack(
                    rx.heading("📤 提交作业", size="5"),
                    rx.text(
                        "当前作业：",
                        size="2",
                        color="gray",
                    ),
                    # 文本输入
                    rx.text_area(
                        placeholder="输入纯文本答案或说明（可选）",
                        value=AssignmentsState.content_text,  # type: ignore
                        on_change=AssignmentsState.set_content_text,  # type: ignore
                        min_height="120px",
                        width="100%",
                    ),
                    # 文件上传
                    rx.text("附件（可选）：", size="2", weight="bold"),
                    rx.upload(
                        rx.vstack(
                            rx.icon(tag="file_up", size=24, color="gray"),
                            rx.text(
                                "点击或拖拽文件到此处上传",
                                size="2",
                                color="gray",
                            ),
                            rx.text(
                                "支持格式见作业卡片说明",
                                size="1",
                                color="gray",
                            ),
                            spacing="1",
                            align="center",
                            padding="20px",
                        ),
                        id="assignment_upload",
                        accept={
                            "application/pdf": ".pdf",
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document": ".docx",
                            "application/zip": ".zip",
                            "text/x-python": ".py",
                            "text/x-c": ".c",
                            "text/x-c++": ".cpp",
                            "text/plain": ".txt",
                        },
                        max_files=1,
                        border="2px dashed var(--gray-6)",
                        border_radius="8px",
                        padding="8px",
                        width="100%",
                    ),
                    rx.cond(
                        AssignmentsState.uploaded_file_name != "",  # type: ignore
                        rx.hstack(
                            rx.icon(tag="file", size=16, color="green"),
                            rx.text(
                                AssignmentsState.uploaded_file_name,  # type: ignore
                                size="2",
                                color="green",
                            ),
                            rx.text(
                                AssignmentsState.uploaded_file_size_display,  # type: ignore
                                size="1",
                                color="gray",
                            ),
                            rx.button(
                                rx.icon(tag="x", size=14),
                                on_click=AssignmentsState.clear_upload,  # type: ignore
                                variant="ghost",
                                size="1",
                                color_scheme="red",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.box(),
                    ),
                    # 提交按钮
                    rx.button(
                        rx.cond(
                            AssignmentsState.is_submitting,  # type: ignore
                            rx.hstack(
                                rx.spinner(size="3"),
                                rx.text("提交中..."),
                                spacing="2",
                            ),
                            rx.hstack(
                                rx.icon(tag="send", size=16),
                                rx.text("提交作业"),
                                spacing="2",
                            ),
                        ),
                        on_click=AssignmentsState.submit_assignment,  # type: ignore
                        color_scheme="blue",
                        size="3",
                        width="100%",
                        disabled=AssignmentsState.is_submitting,  # type: ignore
                    ),
                    # 消息提示
                    rx.cond(
                        AssignmentsState.submit_message != "",  # type: ignore
                        rx.callout(
                            rx.text(AssignmentsState.submit_message),  # type: ignore
                            icon="check_circle",
                            color_scheme="green",
                            width="100%",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        AssignmentsState.submit_error != "",  # type: ignore
                        rx.callout(
                            rx.text(AssignmentsState.submit_error),  # type: ignore
                            icon="alert_triangle",
                            color_scheme="red",
                            width="100%",
                        ),
                        rx.box(),
                    ),
                    spacing="3",
                    align="stretch",
                    width="100%",
                ),
                padding="20px",
                border_radius="10px",
                background="white",
                border="1px solid var(--gray-4)",
                width="100%",
                max_width="720px",
            ),
            rx.box(),  # 未选中作业时显示空
        )


    # ── 历史面板 ──
    def _history_panel() -> rx.Component:
        """提交历史面板 — 表格展示各版本信息"""
        return rx.cond(
            AssignmentsState.show_history,  # type: ignore
            rx.box(
                rx.vstack(
                    rx.heading("📋 提交历史", size="5"),
                    rx.cond(
                        # 有历史记录
                        rx.foreach(
                            AssignmentsState.submission_history,  # type: ignore
                            lambda s: rx.box(
                                rx.hstack(
                                    rx.badge(
                                        f"v{s['version']}",
                                        color_scheme="blue",
                                        variant="solid",
                                    ),
                                    rx.cond(
                                        s["version"]
                                        == AssignmentsState.submission_history[0][  # type: ignore
                                            "version"
                                        ],
                                        rx.badge(
                                            "最新",
                                            color_scheme="green",
                                            variant="soft",
                                        ),
                                        rx.box(),
                                    ),
                                    rx.text(
                                        s["file_name"] or "(纯文本)",
                                        size="2",
                                    ),
                                    rx.text(
                                        s["file_size_display"] or "-",
                                        size="1",
                                        color="gray",
                                    ),
                                    rx.text(
                                        s["submitted_at"],
                                        size="1",
                                        color="gray",
                                    ),
                                    spacing="3",
                                    align="center",
                                    width="100%",
                                ),
                                padding="10px 0",
                                border_bottom="1px solid var(--gray-4)",
                                width="100%",
                            ),
                        ),
                        rx.text(
                            "暂无提交记录",
                            size="2",
                            color="gray",
                        ),
                    ),
                    rx.button(
                        "收起",
                        on_click=AssignmentsState.toggle_history,  # type: ignore
                        variant="ghost",
                        size="1",
                    ),
                    spacing="3",
                    align="stretch",
                    width="100%",
                ),
                padding="20px",
                border_radius="10px",
                background="white",
                border="1px solid var(--gray-4)",
                width="100%",
                max_width="720px",
            ),
            rx.box(),
        )


    # ── 主页面 ──
    def assignments_page():
        """作业提交页面 — F-S-020"""
        # 页面加载时检查登录
        rx.call_effect(AssignmentsState.check_login)  # type: ignore

        return page_layout(
            title="作业提交",
            content=rx.vstack(
                # 未登录提示
                rx.cond(
                    AssignmentsState.current_student_no == "",  # type: ignore
                    _login_prompt(),
                    rx.vstack(
                        # 已登录 — 用户信息
                        rx.hstack(
                            rx.icon(tag="user", size=20, color="var(--blue-9)"),
                            rx.text(
                                f"当前用户：{AssignmentsState.current_student_name} "  # type: ignore
                                f"({AssignmentsState.current_student_no})",  # type: ignore
                                size="3",
                                weight="bold",
                            ),
                            spacing="2",
                            align="center",
                            padding="12px 0",
                        ),
                        # 作业列表
                        rx.heading("📋 可用作业", size="4"),
                        rx.cond(
                            AssignmentsState.assignments.length() > 0,  # type: ignore
                            rx.foreach(
                                AssignmentsState.assignments,  # type: ignore
                                _assignment_card,
                            ),
                            rx.text(
                                "暂无可用作业",
                                color="gray",
                                size="2",
                            ),
                        ),
                        rx.divider(),
                        # 提交面板
                        _submit_panel(),
                        # 历史面板
                        _history_panel(),
                        spacing="4",
                        width="100%",
                        align="start",
                        max_width="760px",
                    ),
                ),
                spacing="4",
                width="100%",
                align="start",
            ),
        )
