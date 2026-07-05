"""
F-D-007 开发运维 — AI 代码审查提示词配置（pr-agent）
"""
try:
    import reflex as rx
except Exception:
    rx = None

devops_page = None

if rx is not None:
    try:
        from oaepp.states.devops_review import PRReviewState
    except ImportError:
        from states.devops_review import PRReviewState

    _PLACEHOLDERS = ("{diff}", "{pr_title}", "{pr_description}", "{author}")

    def _template_chip(label: str, template_id: str):
        return rx.button(
            label,
            size="2",
            variant=rx.cond(
                PRReviewState.active_template == template_id,
                "solid",
                "soft",
            ),
            color_scheme=rx.cond(
                PRReviewState.active_template == template_id,
                "indigo",
                "gray",
            ),
            on_click=PRReviewState.select_template(template_id),
        )

    def devops_page():
        return rx.box(
            rx.vstack(
                rx.heading("开发运维 · AI 代码审查", size="6"),
                rx.text(
                    "F-D-007：pr-agent 提示词模板、Dry-Run 验证与 GitHub Actions 联动",
                    color="gray",
                    font_size="sm",
                ),
                rx.divider(),
                rx.hstack(
                    rx.heading("步骤 ⑤ · AI 代码审查提示词", size="4"),
                    rx.spacer(),
                    rx.button(
                        "验证配置",
                        size="2",
                        variant="outline",
                        loading=PRReviewState.is_validating,
                        on_click=PRReviewState.dry_run_review,
                    ),
                    rx.button(
                        "保存并应用",
                        size="2",
                        color_scheme="indigo",
                        on_click=PRReviewState.save_template,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.text("选择提示词模板", font_size="xs", color="gray"),
                rx.hstack(
                    _template_chip("通用代码审查", "general-review"),
                    _template_chip("工程实践规范检查", "engineering-practices"),
                    _template_chip("安全全面审查", "security-audit"),
                    flex_wrap="wrap",
                    gap="2",
                ),
                rx.hstack(
                    rx.text("可用变量：", font_size="xs", color="gray"),
                    *[
                        rx.code(p, font_size="xs")
                        for p in _PLACEHOLDERS
                    ],
                    flex_wrap="wrap",
                    gap="1",
                ),
                rx.text_area(
                    value=PRReviewState.editor_content,
                    on_change=PRReviewState.set_editor_content,
                    height="220px",
                    font_family="monospace",
                    font_size="xs",
                    width="100%",
                ),
                rx.hstack(
                    rx.text(
                        "保存至 ",
                        rx.code(PRReviewState.prompt_save_path, font_size="xs"),
                        "（纳入 Git）",
                        font_size="xs",
                        color="gray",
                    ),
                    rx.spacer(),
                    rx.button(
                        "清除验证痕迹",
                        size="2",
                        variant="outline",
                        color_scheme="red",
                        on_click=PRReviewState.clear_dry_run_traces,
                    ),
                    width="100%",
                ),
                rx.box(
                    rx.hstack(
                        rx.text("验证结果预览（Dry-Run）", font_weight="medium", font_size="sm"),
                        rx.spacer(),
                        rx.badge(PRReviewState.dry_run_status_label, color_scheme="blue"),
                        width="100%",
                    ),
                    rx.cond(
                        PRReviewState.dry_run_preview != "",
                        rx.box(
                            rx.text(
                                "提示词版本：",
                                PRReviewState.dry_run_result["prompt_version"],
                                font_size="xs",
                                color="gray",
                                margin_bottom="2",
                            ),
                            rx.code_block(
                                PRReviewState.dry_run_preview,
                                language="markdown",
                                width="100%",
                            ),
                        ),
                        rx.center(
                            rx.text(
                                "点击「验证配置」后在此显示 AI 审查输出（不提交 GitHub）",
                                color="gray",
                                font_size="xs",
                            ),
                            min_height="80px",
                        ),
                    ),
                    padding="4",
                    border="1px solid",
                    border_color="gray.200",
                    border_radius="md",
                    background="gray.50",
                    width="100%",
                ),
                rx.divider(),
                rx.heading("自定义模板", size="3"),
                rx.hstack(
                    rx.input(
                        placeholder="新模板名称（复制当前模板）",
                        value=PRReviewState.new_template_name,
                        on_change=PRReviewState.set_new_template_name,
                        flex="1",
                    ),
                    rx.button("复制模板", on_click=lambda: PRReviewState.copy_template()),
                    rx.button(
                        "设为默认",
                        variant="soft",
                        on_click=lambda: PRReviewState.set_default_template(),
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="重命名（仅自定义模板）",
                        value=PRReviewState.rename_target_name,
                        on_change=PRReviewState.set_rename_target_name,
                        flex="1",
                    ),
                    rx.button("重命名", on_click=lambda: PRReviewState.rename_template()),
                    rx.button(
                        "删除当前",
                        color_scheme="red",
                        variant="outline",
                        on_click=lambda: PRReviewState.delete_template(),
                    ),
                    width="100%",
                ),
                rx.callout(
                    PRReviewState.status_message,
                    icon="info",
                    size="1",
                ),
                rx.link("← 返回首页", href="/"),
                spacing="4",
                width="100%",
                max_width="900px",
                padding="6",
            ),
            on_mount=PRReviewState.on_load,
            min_height="100vh",
            width="100%",
            background="gray.50",
        )
