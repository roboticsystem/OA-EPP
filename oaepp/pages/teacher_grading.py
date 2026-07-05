"""F-T-014 在线批改页面

对应 State : oaepp.states.teacher_grading.GradingState
路由       : /teacher_grading （由 app.py 自动发现机制注册）

功能：
- 左侧：批改队列（支持课程/班级筛选，以截止时间升序排列，二次提交任务高亮）
- 右侧：逐份批改面板（维度打分、Markdown评语、复制上一份评语、允许二次提交、导航）
- 底部：审计日志面板
"""
try:
    import reflex as rx
except Exception:
    rx = None

teacher_grading_page = None
if rx is not None:
    try:
        from oaepp.states.teacher_grading import GradingState
    except ImportError:
        try:
            from states.teacher_grading import GradingState
        except ImportError:
            GradingState = None

    # ── 样式常量 ──────────────────────────────────────────────────────────

    _CARD_STYLE = {
        "padding": "16px",
        "border_radius": "8px",
        "border": "1px solid var(--gray-5)",
        "background": "white",
    }

    _DIMENSION_LABELS = {
        "attendance": ("出勤", "var(--green-9)"),
        "exam": ("考试", "var(--blue-9)"),
        "code": ("代码", "var(--violet-9)"),
        "pr": ("PR贡献", "var(--orange-9)"),
    }

    # ── 筛选栏 ────────────────────────────────────────────────────────────

    def _filter_bar() -> rx.Component:
        """课程/班级筛选栏"""
        return rx.hstack(
            rx.select(
                [rx.option(c["title"], value=str(c["id"])) for c in GradingState.filter_options.get("courses", [])],
                placeholder="全部课程",
                value=GradingState.course_filter,
                on_change=GradingState.set_course,
                width="200px",
            ),
            rx.select(
                [rx.option(c, value=c) for c in GradingState.filter_options.get("classes", [])],
                placeholder="全部班级",
                value=GradingState.class_filter,
                on_change=GradingState.set_class,
                width="200px",
            ),
            rx.spacer(),
            rx.text(
                f"共 {GradingState.queue_pending_count}/{GradingState.queue_total} 待批改",
                color="gray",
                size="2",
            ),
            padding="8px 0",
        )

    # ── 队列列表项 ────────────────────────────────────────────────────────

    def _queue_item(idx: int, item: dict) -> rx.Component:
        """单个队列项，支持 allow_resubmit 高亮、当前选中状态"""
        sid = item.get("submission_id", 0)
        is_current = GradingState.current_index == idx
        is_resubmit = item.get("allow_resubmit", False)
        is_graded = item.get("grading_status") == "graded"

        bg = "var(--gray-2)" if is_current else "white"
        if is_current:
            bg = "var(--blue-2)"
        elif is_resubmit and not is_graded:
            bg = "var(--orange-2)"

        border_left = "4px solid var(--blue-9)" if is_current else (
            "4px solid var(--orange-9)" if (is_resubmit and not is_graded) else "4px solid transparent"
        )

        return rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text(item.get("assignment_title", "未命名"), font_weight="bold", size="2", truncate=True),
                    rx.text(
                        f"{item.get('full_name', '')} · {item.get('student_no', '')}",
                        size="1", color="gray",
                    ),
                    rx.text(
                        f"班级: {item.get('class_name', '')} | 提交: {str(item.get('submitted_at', ''))[:16]}",
                        size="1", color="gray",
                    ),
                    align="start",
                    spacing="2px",
                ),
                rx.spacer(),
                rx.cond(
                    is_graded,
                    rx.badge("已批改", color_scheme="green", size="1"),
                    rx.cond(
                        is_resubmit,
                        rx.badge("可重提", color_scheme="orange", size="1"),
                        rx.badge("待批改", color_scheme="blue", size="1"),
                    ),
                ),
                width="100%",
                align="center",
            ),
            on_click=GradingState.goto_submission(idx),
            padding="10px 12px",
            border_radius="6px",
            background=bg,
            border_left=border_left,
            cursor="pointer",
            _hover={"background": "var(--blue-3)"},
            margin_bottom="4px",
        )

    # ── 队列面板（左侧） ──────────────────────────────────────────────────

    def _queue_panel() -> rx.Component:
        """左侧批改队列面板"""
        return rx.box(
            rx.vstack(
                rx.heading("批改队列", size="4"),
                rx.button(
                    rx.hstack(rx.icon(tag="refresh_cw", size=14), rx.text("刷新"), spacing="2"),
                    on_click=GradingState.load_queue,
                    size="1",
                    variant="outline",
                    color_scheme="blue",
                ),
                _filter_bar(),
                rx.divider(),
                rx.cond(
                    GradingState.is_loading,
                    rx.center(rx.spinner(), padding="20px"),
                    rx.cond(
                        GradingState.grading_queue.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon(tag="check_circle", size=32, color="var(--green-9)"),
                                rx.text("暂无待批改提交", color="gray", size="2"),
                            ),
                            padding="40px 0",
                        ),
                    ),
                ),
                rx.cond(
                    GradingState.grading_queue.length() > 0,
                    rx.box(
                        rx.foreach(
                            GradingState.grading_queue,
                            lambda item, idx: _queue_item(idx, item),
                        ),
                        overflow_y="auto",
                        max_height="calc(100vh - 320px)",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            **_CARD_STYLE,
            width="340px",
            min_width="300px",
            max_height="calc(100vh - 120px)",
            overflow_y="auto",
        )

    # ── 提交内容展示 ──────────────────────────────────────────────────────

    def _submission_content() -> rx.Component:
        """学生提交内容展示（文本预览 + 附件下载）"""
        return rx.box(
            rx.vstack(
                rx.heading("提交内容", size="3"),
                rx.divider(),
                rx.cond(
                    GradingState.current_submission.get("text_content") != "",
                    rx.box(
                        rx.markdown(GradingState.submission_preview),
                        padding="12px",
                        border_radius="6px",
                        background="var(--gray-2)",
                        max_height="200px",
                        overflow_y="auto",
                    ),
                    rx.text("（无文本内容）", color="gray", size="2"),
                ),
                rx.cond(
                    GradingState.current_submission.get("file_url") != "",
                    rx.link(
                        rx.hstack(
                            rx.icon(tag="download", size=14),
                            rx.text("下载附件", size="2"),
                            spacing="1",
                        ),
                        href=GradingState.current_submission.get("file_url", "#"),
                        is_external=True,
                        color="var(--blue-9)",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            **_CARD_STYLE,
            width="100%",
        )

    # ── 维度打分卡 ────────────────────────────────────────────────────────

    def _score_card(label: str, color: str, state_attr, setter) -> rx.Component:
        """单个维度打分卡片"""
        return rx.box(
            rx.hstack(
                rx.text(label, font_weight="bold", size="2", color=color),
                rx.spacer(),
                rx.input(
                    value=state_attr,
                    on_change=setter,
                    placeholder="0.0",
                    width="80px",
                    type="number",
                    min_=0,
                    max_=100,
                ),
                rx.text("/100", size="1", color="gray"),
                align="center",
                width="100%",
            ),
            padding="8px 12px",
            border_radius="6px",
            border=f"1px solid {color}",
            width="100%",
        )

    def _score_panel() -> rx.Component:
        """四个维度打分面板"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("维度打分", size="3"),
                    rx.spacer(),
                    rx.text(f"合计: {GradingState.total_score}", font_weight="bold", color="var(--blue-9)"),
                ),
                rx.divider(),
                _score_card("出勤", "var(--green-9)", GradingState.attendance_score, GradingState.set_attendance_score),
                _score_card("考试", "var(--blue-9)", GradingState.exam_score, GradingState.set_exam_score),
                _score_card("代码", "var(--violet-9)", GradingState.code_score, GradingState.set_code_score),
                _score_card("PR贡献", "var(--orange-9)", GradingState.pr_score, GradingState.set_pr_score),
                spacing="2",
                width="100%",
            ),
            **_CARD_STYLE,
            width="100%",
        )

    # ── 评语面板 ──────────────────────────────────────────────────────────

    def _comment_panel() -> rx.Component:
        """评语与改进建议输入面板（Markdown）"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("评语与反馈", size="3"),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(rx.icon(tag="copy", size=14), rx.text("复制上一份评语"), spacing="1"),
                        on_click=GradingState.copy_last_comment,
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                    ),
                ),
                rx.text("总体评语（支持 Markdown）：", size="1", color="gray", font_weight="bold"),
                rx.text_area(
                    value=GradingState.comment_md,
                    on_change=GradingState.set_comment,
                    placeholder="输入总体评语，支持 Markdown 格式...",
                    min_height="100px",
                    width="100%",
                ),
                rx.text("改进建议（支持 Markdown）：", size="1", color="gray", font_weight="bold"),
                rx.text_area(
                    value=GradingState.improvement_md,
                    on_change=GradingState.set_improvement,
                    placeholder="输入分项改进建议，支持 Markdown 格式...",
                    min_height="80px",
                    width="100%",
                ),
                # Markdown 预览
                rx.cond(
                    (GradingState.comment_md != "") | (GradingState.improvement_md != ""),
                    rx.box(
                        rx.text("预览：", size="1", color="gray", font_weight="bold"),
                        rx.markdown(
                            GradingState.comment_md + ("\n\n---\n\n" + GradingState.improvement_md if GradingState.improvement_md else ""),
                        ),
                        padding="12px",
                        border_radius="6px",
                        background="var(--gray-2)",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            **_CARD_STYLE,
            width="100%",
        )

    # ── 操作栏 ────────────────────────────────────────────────────────────

    def _action_bar() -> rx.Component:
        """批改操作栏：二次提交开关 + 提交按钮 + 导航"""
        return rx.box(
            rx.vstack(
                # 二次提交开关
                rx.hstack(
                    rx.switch(
                        checked=GradingState.allow_resubmit,
                        on_change=GradingState.toggle_resubmit,
                    ),
                    rx.text("允许学生二次提交", size="2"),
                    rx.tooltip(
                        rx.icon(tag="help_circle", size=14, color="gray"),
                        content="开启后学生可根据改进建议重新提交，该任务在队列中会以橙色高亮显示",
                    ),
                    spacing="2",
                    align="center",
                ),
                # 提交按钮 + 导航
                rx.hstack(
                    rx.button(
                        rx.icon(tag="chevron_left", size=16),
                        on_click=GradingState.prev_submission,
                        disabled=~GradingState.has_prev,
                        size="2",
                        variant="outline",
                    ),
                    rx.text(
                        f"{GradingState.current_index + 1} / {GradingState.queue_total}",
                        size="2",
                        color="gray",
                        width="60px",
                        text_align="center",
                    ),
                    rx.button(
                        rx.icon(tag="chevron_right", size=16),
                        on_click=GradingState.next_submission,
                        disabled=~GradingState.has_next,
                        size="2",
                        variant="outline",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.cond(
                            GradingState.is_submitting,
                            rx.hstack(rx.spinner(size="1"), rx.text("保存中..."), spacing="2"),
                            rx.hstack(rx.icon(tag="check", size=16), rx.text("保存批改"), spacing="2"),
                        ),
                        on_click=GradingState.submit_grade,
                        disabled=GradingState.is_submitting,
                        color_scheme="blue",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                # 消息反馈
                rx.cond(
                    GradingState.error_message != "",
                    rx.callout(
                        rx.text(GradingState.error_message, size="1"),
                        icon="alert_triangle",
                        color_scheme="red",
                        width="100%",
                    ),
                ),
                rx.cond(
                    GradingState.success_message != "",
                    rx.callout(
                        rx.text(GradingState.success_message, size="1"),
                        icon="check_circle",
                        color_scheme="green",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            **_CARD_STYLE,
            width="100%",
        )

    # ── 学生信息头 ────────────────────────────────────────────────────────

    def _student_header() -> rx.Component:
        """当前批改学生的信息头"""
        return rx.cond(
            (GradingState.current_submission.get("student_no") != "") | (GradingState.current_submission.get("full_name") != ""),
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            f"{GradingState.current_submission.get('full_name', '')}",
                            size="4",
                        ),
                        rx.hstack(
                            rx.badge(
                                GradingState.current_submission.get("student_no", ""),
                                color_scheme="blue",
                                size="1",
                            ),
                            rx.badge(
                                GradingState.current_submission.get("class_name", ""),
                                color_scheme="gray",
                                size="1",
                            ),
                            rx.cond(
                                GradingState.current_submission.get("is_late", False),
                                rx.badge("迟交", color_scheme="red", size="1"),
                            ),
                            spacing="1",
                        ),
                        rx.text(
                            f"作业: {GradingState.current_submission.get('assignment_title', '')} "
                            f"| 版本: v{GradingState.current_submission.get('version_no', 1)}",
                            size="1",
                            color="gray",
                        ),
                        spacing="2px",
                    ),
                    rx.spacer(),
                    rx.icon(tag="graduation_cap", size=28, color="var(--blue-9)"),
                    align="center",
                    width="100%",
                ),
                padding="12px 16px",
                border_radius="8px",
                background="var(--blue-1)",
                border="1px solid var(--blue-4)",
                width="100%",
            ),
        )

    # ── 右侧批改面板 ──────────────────────────────────────────────────────

    def _grading_panel() -> rx.Component:
        """右侧逐份批改面板"""
        return rx.cond(
            GradingState.queue_total > 0,
            rx.box(
                rx.vstack(
                    _student_header(),
                    _submission_content(),
                    _score_panel(),
                    _comment_panel(),
                    _action_bar(),
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                flex="1",
                min_width="0",
                overflow_y="auto",
                max_height="calc(100vh - 120px)",
                padding_right="4px",
            ),
            # 队列为空时的提示
            rx.center(
                rx.vstack(
                    rx.icon(tag="clipboard_check", size=48, color="var(--gray-7)"),
                    rx.text("选择左侧队列中的一份提交开始批改", color="gray", size="3"),
                    rx.text("或等待学生提交新作业", color="gray", size="1"),
                ),
                width="100%",
                height="400px",
            ),
        )

    # ── 审计日志面板 ──────────────────────────────────────────────────────

    def _audit_log_panel() -> rx.Component:
        """批改审计日志面板（可折叠）"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="shield", size=16),
                            rx.text("审计日志"),
                            rx.cond(
                                GradingState.show_audit_log,
                                rx.icon(tag="chevron_up", size=14),
                                rx.icon(tag="chevron_down", size=14),
                            ),
                            spacing="1",
                        ),
                        on_click=GradingState.toggle_audit_log,
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    rx.cond(
                        GradingState.show_audit_log,
                        rx.button(
                            rx.text("刷新", size="1"),
                            on_click=GradingState.load_audit_logs,
                            variant="outline",
                            size="1",
                        ),
                    ),
                    width="100%",
                ),
                rx.cond(
                    GradingState.show_audit_log,
                    rx.box(
                        rx.cond(
                            GradingState.audit_log.length() == 0,
                            rx.text("暂无审计记录", size="1", color="gray", padding="8px"),
                            rx.box(
                                rx.foreach(
                                    GradingState.audit_log,
                                    lambda entry: rx.box(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.text(
                                                    f"#{entry.get('submission_id', '?')}",
                                                    font_weight="bold",
                                                    size="1",
                                                ),
                                                rx.text(
                                                    str(entry.get("graded_at", ""))[:19],
                                                    size="1",
                                                    color="gray",
                                                ),
                                                rx.cond(
                                                    entry.get("allow_resubmit", False),
                                                    rx.badge("可重提", color_scheme="orange", size="1"),
                                                ),
                                                spacing="1",
                                            ),
                                            rx.text(
                                                f"出勤:{entry.get('attendance_score', '-')} "
                                                f"考试:{entry.get('exam_score', '-')} "
                                                f"代码:{entry.get('code_score', '-')} "
                                                f"PR:{entry.get('pr_score', '-')} "
                                                f"→ 总分:{entry.get('total_score', '-')}",
                                                size="1",
                                                color="gray",
                                            ),
                                            spacing="1",
                                        ),
                                        padding="6px 0",
                                        border_bottom="1px solid var(--gray-4)",
                                        width="100%",
                                    ),
                                ),
                                max_height="200px",
                                overflow_y="auto",
                                width="100%",
                            ),
                        ),
                        **_CARD_STYLE,
                        width="100%",
                        margin_top="8px",
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            width="100%",
        )

    # ── 页面入口 ──────────────────────────────────────────────────────────

    def teacher_grading_page() -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.heading("在线批改", size="6"),
                # 主内容区：队列 + 批改面板
                rx.hstack(
                    _queue_panel(),
                    _grading_panel(),
                    spacing="4",
                    width="100%",
                    align="start",
                ),
                # 审计日志（底部）
                _audit_log_panel(),
                spacing="4",
                width="100%",
            ),
            padding="2em",
            width="100%",
        )
