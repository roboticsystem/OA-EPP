"""F-T-007 Issue-PR 关联规则配置 — Reflex page

教师功能：
- 按课程开启/关闭「Issue 关闭必须关联 PR」规则
- 查看 Issue-PR 关联记录
- 查看 Webhook 警告日志
"""
try:
    import reflex as rx
except Exception:
    rx = None

teacher_issue_pr_page = None
if rx is not None:
    try:
        from states.teacher_issue_pr import IssuePRState
    except ImportError:
        from oaepp.states.teacher_issue_pr import IssuePRState

    _BG = "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)"

    def _rule_config_section():
        return rx.box(
            rx.vstack(
                rx.heading("Issue-PR 关联规则配置", size="5"),
                rx.text(
                    "按课程独立设置「Issue 关闭必须关联 PR 编号」规则",
                    color="gray",
                    size="1",
                ),
                rx.divider(),
                # 课程选择
                rx.vstack(
                    rx.text("选择课程", weight="bold", size="2"),
                    rx.select(
                        IssuePRState.config_course_options,
                        value=str(IssuePRState.selected_course_id) if IssuePRState.selected_course_id else "",
                        on_change=IssuePRState.select_course,
                        placeholder="请选择课程",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # 规则开关
                rx.hstack(
                    rx.text("规则状态", weight="bold", size="2"),
                    rx.switch(
                        is_checked=IssuePRState.rule_enabled,
                        on_change=IssuePRState.toggle_rule,
                    ),
                    rx.badge(
                        "已开启" if IssuePRState.rule_enabled else "已关闭",
                        color_scheme=rx.cond(IssuePRState.rule_enabled, "green", "gray"),
                        variant="soft",
                        size="1",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.text(
                    "开启后，学生在平台内关闭 Issue 时需强制填写已存在的 PR 编号并通过 GitHub API 实时校验",
                    color="gray",
                    size="1",
                ),
                # 保存按钮
                rx.button(
                    "保存配置",
                    color_scheme="indigo",
                    on_click=IssuePRState.save_course_config,
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
        )

    def _issue_pr_mapping_section():
        return rx.box(
            rx.vstack(
                rx.heading("Issue-PR 关联记录", size="4"),
                rx.text("已通过平台关闭的 Issue 及其关联 PR 信息", color="gray", size="1"),
                rx.divider(),
                rx.cond(
                    IssuePRState.issue_pr_map,
                    rx.foreach(
                        IssuePRState.issue_pr_map.items(),
                        lambda item: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(f"Issue #{item[0]}", weight="bold", font_family="monospace"),
                                    rx.badge(
                                        item[1].get("state", ""),
                                        color_scheme=rx.cond(
                                            item[1].get("state") == "merged",
                                            "purple",
                                            rx.cond(
                                                item[1].get("state") == "open",
                                                "green",
                                                "red",
                                            ),
                                        ),
                                        variant="soft",
                                        size="1",
                                    ),
                                    spacing="2",
                                ),
                                rx.text(f"PR #{item[1].get('pr_number', '')}", font_family="monospace", size="1"),
                                rx.cond(
                                    item[1].get("html_url"),
                                    rx.link(
                                        item[1].get("html_url", ""),
                                        href=item[1].get("html_url", ""),
                                        color_scheme="indigo",
                                        font_size="xs",
                                        is_external=True,
                                    ),
                                ),
                                rx.text(
                                    f"关闭时间: {item[1].get('closed_at', '')}",
                                    color="gray",
                                    font_size="xs",
                                ),
                                spacing="1",
                            ),
                            border="1px solid #e5e7eb",
                            border_radius="6px",
                            padding="10px",
                            width="100%",
                            _hover={"bg": "#f9fafb"},
                        ),
                    ),
                    rx.text("暂无关联记录", color="gray", font_size="sm"),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
        )

    def _warning_log_section():
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Webhook 警告日志", size="4"),
                    rx.button(
                        "清空日志",
                        size="1",
                        variant="ghost",
                        color_scheme="red",
                        on_click=IssuePRState.clear_warning_log,
                    ),
                    justify="between",
                    width="100%",
                ),
                rx.text(
                    "记录通过 GitHub 网页直接关闭 Issue 且未关联 PR 的违规事件",
                    color="gray",
                    size="1",
                ),
                rx.divider(),
                rx.cond(
                    IssuePRState.warning_log,
                    rx.foreach(
                        IssuePRState.warning_log,
                        lambda entry: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        f"Issue #{entry.get('issue_id', '?')}",
                                        weight="bold",
                                        font_family="monospace",
                                    ),
                                    rx.badge(
                                        entry.get("source", ""),
                                        color_scheme="red",
                                        variant="soft",
                                        size="1",
                                    ),
                                    spacing="2",
                                ),
                                rx.text(entry.get("reason", ""), size="1"),
                                rx.text(
                                    f"时间: {entry.get('timestamp', '')}",
                                    color="gray",
                                    font_size="xs",
                                ),
                                rx.cond(
                                    entry.get("closed_by"),
                                    rx.text(
                                        f"关闭者: {entry.get('closed_by', '')}",
                                        color="gray",
                                        font_size="xs",
                                    ),
                                ),
                                spacing="1",
                            ),
                            border="1px solid #fecaca",
                            border_radius="6px",
                            padding="10px",
                            bg="#fef2f2",
                            width="100%",
                        ),
                    ),
                    rx.text("暂无警告日志", color="gray", font_size="sm"),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
        )

    def teacher_issue_pr_page():
        return rx.center(
            rx.box(
                rx.vstack(
                    # 页面标题
                    rx.hstack(
                        rx.heading("Issue-PR 关联规则管理", size="6"),
                        rx.badge("F-T-007", color_scheme="indigo", variant="soft", size="1"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "配置 Issue 关闭必须关联 PR 编号的强制规则，支持按课程独立设置",
                        color="gray",
                        size="1",
                    ),
                    # 规则配置卡片
                    _rule_config_section(),
                    # Issue-PR 映射卡片
                    _issue_pr_mapping_section(),
                    # Webhook 警告日志卡片
                    _warning_log_section(),
                    # 状态消息
                    rx.cond(
                        IssuePRState.status_message != "",
                        rx.callout(
                            IssuePRState.status_message,
                            color_scheme="indigo",
                            width="100%",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                max_width="960px",
                width="100%",
                padding="28px",
                border_radius="12px",
                box_shadow="0 10px 30px rgba(0,0,0,0.08)",
                background="white",
            ),
            min_height="100vh",
            width="100%",
            background=_BG,
            padding="20px",
            on_mount=IssuePRState.on_load,
        )
