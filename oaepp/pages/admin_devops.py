"""
F-D-006 开发运维 — admin_devops_page

提供：
- 运维步骤进度条（对应仓库初始化/分支保护/Secrets/CI/AI审查）
- 脚本执行控制台（实时输出 + 错误高亮）
- GitHub 快捷链接面板
- 执行状态汇总 + 重试
"""

try:
    import reflex as rx
except Exception:
    rx = None

admin_devops_page = None

if rx is not None:
    try:
        from states.devops_script import ScriptExecuteState, LineType
    except ImportError:
        from oaepp.states.devops_script import ScriptExecuteState, LineType

    try:
        from states.auth import AuthState
    except ImportError:
        from oaepp.states.auth import AuthState

    # ── 颜色常量 ──────────────────────────────────────────────────────
    _COLOR_BG = "#f8fafc"
    _COLOR_CARD = "#ffffff"
    _COLOR_BORDER = "#e2e8f0"
    _COLOR_ACCENT = "#4f46e5"
    _COLOR_ACCENT_LIGHT = "#eef2ff"
    _COLOR_GREEN = "#22c55e"
    _COLOR_GREEN_BG = "#f0fdf4"
    _COLOR_RED = "#ef4444"
    _COLOR_RED_BG = "#fef2f2"
    _COLOR_GRAY = "#6b7280"
    _COLOR_DARK = "#1f2937"
    _COLOR_TERM_BG = "#1e1e2e"
    _COLOR_TERM_TEXT = "#cdd6f4"
    _COLOR_TERM_ERROR = "#f38ba8"
    _COLOR_TERM_SUCCESS = "#a6e3a1"

    # ── 侧边栏 ─────────────────────────────────────────────────────────
    def _sidebar():
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("shield-check", size=18, color="white"),
                        width="32px", height="32px",
                        border_radius="8px",
                        background=_COLOR_ACCENT,
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("OA-EPP", weight="bold", color=_COLOR_DARK, size="2"),
                        rx.text("教师端", size="1", background=_COLOR_ACCENT_LIGHT,
                                color=_COLOR_ACCENT, padding_x="6px", padding_y="1px",
                                border_radius="full"),
                        spacing="0",
                    ),
                    spacing="2",
                ),
                padding_x="20px", padding_y="20px",
                border_bottom=f"1px solid {_COLOR_BORDER}",
                width="100%",
            ),
            rx.vstack(
                _nav_item("学生管理", "users", False, href="/admin_students"),
                _nav_item("开发运维", "terminal", True, href="/admin_devops"),
                _nav_item("成绩管理", "bar-chart", False, href="/admin_grades"),
                _nav_item("系统设置", "settings", False, href="/admin_settings"),
                spacing="1",
                padding_x="12px", padding_y="16px",
                width="100%",
            ),
            width="224px", height="100vh",
            position="fixed", left="0", top="0",
            background=_COLOR_CARD,
            border_right=f"1px solid {_COLOR_BORDER}",
            z_index="10",
        )

    def _nav_item(label: str, icon: str, active: bool = False, href: str = "#"):
        return rx.link(
            rx.hstack(
                rx.icon(icon, size=16, color=_COLOR_ACCENT if active else _COLOR_GRAY),
                rx.text(label, size="2", color=_COLOR_ACCENT if active else _COLOR_GRAY,
                        weight="medium" if active else "regular"),
                spacing="3",
                padding_x="12px", padding_y="10px",
                width="100%",
            ),
            href=href,
            width="100%",
        )

    # ── 脚本选择卡片 ──────────────────────────────────────────────────
    def _script_card(script: dict):
        is_selected = ScriptExecuteState.selected_script == script["id"]
        is_running = ScriptExecuteState.is_running

        return rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text(script["name"], size="2", weight="bold",
                            color=rx.cond(is_selected, _COLOR_ACCENT, _COLOR_DARK)),
                    rx.text(script["description"], size="1", color=_COLOR_GRAY),
                    spacing="0",
                    flex="1",
                ),
                rx.cond(
                    is_selected & is_running,
                    rx.spinner(size="3", color=_COLOR_ACCENT),
                    rx.button(
                        "执行",
                        size="1",
                        on_click=ScriptExecuteState.execute_script,
                        color_scheme="indigo",
                        variant=rx.cond(is_selected, "solid", "outline"),
                        disabled=is_running,
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            padding="14px",
            border_radius="8px",
            background=rx.cond(is_selected, _COLOR_ACCENT_LIGHT, _COLOR_CARD),
            border=rx.cond(is_selected, f"1px solid {_COLOR_ACCENT}", f"1px solid {_COLOR_BORDER}"),
            cursor="pointer",
            on_click=lambda: ScriptExecuteState.select_script(script["id"]),
            width="100%",
        )

    # ── 控制台行渲染 ──────────────────────────────────────────────────
    def _console_line(line_text: str):
        return rx.text(
            line_text,
            size="1",
            font_family="'JetBrains Mono', 'Fira Code', monospace",
            color=rx.cond(
                line_text.contains("❌") | line_text.contains("✗") | line_text.contains("error"),
                _COLOR_TERM_ERROR,
                rx.cond(
                    line_text.contains("✅") | line_text.contains("✓") | line_text.contains("🚀"),
                    _COLOR_TERM_SUCCESS,
                    _COLOR_TERM_TEXT,
                ),
            ),
            white_space="pre-wrap",
            word_break="break-all",
        )

    # ── 脚本控制台 ────────────────────────────────────────────────────
    def _console_output():
        return rx.box(
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        ScriptExecuteState.script_output,
                        _console_line,
                    ),
                    spacing="0",
                    align="start",
                    width="100%",
                ),
                max_height="340px",
                width="100%",
            ),
            # 底部状态栏
            rx.hstack(
                rx.cond(
                    ScriptExecuteState.is_running,
                    rx.hstack(
                        rx.spinner(size="3", color=_COLOR_ACCENT),
                        rx.text("执行中...", size="1", color=_COLOR_ACCENT),
                        spacing="2",
                    ),
                    rx.cond(
                        ScriptExecuteState.is_failed,
                        rx.hstack(
                            rx.icon("circle-x", size=14, color=_COLOR_RED),
                            rx.text(f"退出码: {ScriptExecuteState.exit_code}", size="1",
                                    color=_COLOR_RED),
                            spacing="1",
                        ),
                        rx.cond(
                            ScriptExecuteState.is_success,
                            rx.hstack(
                                rx.icon("circle-check", size=14, color=_COLOR_GREEN),
                                rx.text("执行成功", size="1", color=_COLOR_GREEN),
                                spacing="1",
                            ),
                            rx.text("就绪", size="1", color=_COLOR_GRAY),
                        ),
                    ),
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        "清空",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=ScriptExecuteState.clear_output,
                    ),
                    rx.cond(
                        ScriptExecuteState.is_failed,
                        rx.button(
                            "🔄 重试",
                            size="1",
                            color_scheme="red",
                            variant="solid",
                            on_click=ScriptExecuteState.retry_failed,
                        ),
                    ),
                    spacing="2",
                ),
                padding_x="12px", padding_y="8px",
                width="100%",
                border_top=f"1px solid rgb(49, 50, 68)",
            ),
            background=_COLOR_TERM_BG,
            border_radius="8px",
            overflow="hidden",
            width="100%",
        )

    # ── 进度步骤条 ────────────────────────────────────────────────────
    def _progress_bar():
        return rx.box(
            rx.hstack(
                rx.text("执行进度", size="2", weight="bold", color=_COLOR_DARK),
                rx.spacer(),
                rx.text(
                    rx.text(f"{ScriptExecuteState.current_step}", as_="span", weight="bold"),
                    f" / {ScriptExecuteState.total_steps} 步",
                    size="1",
                    color=_COLOR_GRAY,
                ),
                width="100%",
            ),
            rx.progress(
                value=ScriptExecuteState.progress_percent,
                width="100%",
                size="2",
                color_scheme="indigo",
                border_radius="full",
            ),
            spacing="2",
            width="100%",
        )

    # ── 步骤汇总面板 ──────────────────────────────────────────────────
    def _step_summary():
        return rx.box(
            rx.text("运维步骤总览", size="2", weight="bold", color=_COLOR_DARK),
            rx.vstack(
                *_step_item("① 仓库初始化", True, "F-D-001"),
                *_step_item("② 分支保护 & Secrets", True, "F-D-002/003"),
                *_step_item("③ CI/CD 工作流", True, "F-D-004"),
                *_step_item("④ 协作权限配置", True, "F-D-005"),
                *_step_item("⑤ 脚本Web执行", False, "F-D-006"),
                spacing="2",
                width="100%",
            ),
            spacing="3",
            padding="16px",
            background=_COLOR_CARD,
            border_radius="12px",
            border=f"1px solid {_COLOR_BORDER}",
            width="100%",
        )

    def _step_item(label: str, done: bool, ref: str):
        return [
            rx.hstack(
                rx.icon("circle-check" if done else "circle", size=14,
                        color=_COLOR_GREEN if done else _COLOR_GRAY),
                rx.text(label, size="1", weight="medium",
                        color=_COLOR_GREEN if done else _COLOR_DARK),
                rx.spacer(),
                rx.text(ref, size="1", color=_COLOR_GRAY),
                spacing="2",
                width="100%",
            ),
        ]

    # ── 错误日志复制区 ────────────────────────────────────────────────
    def _error_log_panel():
        return rx.cond(
            ScriptExecuteState.is_failed,
            rx.box(
                rx.hstack(
                    rx.text("错误日志", size="2", weight="bold", color=_COLOR_RED),
                    rx.spacer(),
                    rx.button(
                        "复制日志",
                        size="1",
                        color_scheme="red",
                        variant="outline",
                        on_click=rx.set_clipboard(ScriptExecuteState.get_full_log),
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.text(
                        ScriptExecuteState.get_full_log,
                        size="1",
                        font_family="monospace",
                        color=_COLOR_RED,
                        white_space="pre-wrap",
                        word_break="break-all",
                    ),
                    padding="12px",
                    background=_COLOR_RED_BG,
                    border_radius="8px",
                    border=f"1px solid #fecaca",
                    max_height="200px",
                    overflow_y="auto",
                    width="100%",
                ),
                spacing="3",
                padding="16px",
                background=_COLOR_CARD,
                border_radius="12px",
                border=f"1px solid {_COLOR_BORDER}",
                width="100%",
            ),
        )

    # ── 快捷链接 ──────────────────────────────────────────────────────
    def _quick_links():
        links = [
            ("github", "仓库主页", "https://github.com"),
            ("git-pull-request", "Pull Requests", "https://github.com/pulls"),
            ("circle-dot", "Issues", "https://github.com/issues"),
            ("play", "Actions", "https://github.com/actions"),
            ("git-branch", "分支管理", "https://github.com/branches"),
            ("key", "Secrets", "https://github.com/settings/secrets"),
        ]
        return rx.box(
            rx.text("GitHub 快捷链接", size="2", weight="bold", color=_COLOR_DARK),
            rx.text("开发运维常用入口 (F-D-008)", size="1", color=_COLOR_GRAY),
            rx.vstack(
                *[
                    rx.link(
                        rx.hstack(
                            rx.icon(icon, size=14, color=_COLOR_GRAY),
                            rx.text(label, size="1", color=_COLOR_DARK),
                            spacing="3",
                            padding_x="12px", padding_y="10px",
                            width="100%",
                        ),
                        href=url,
                        is_external=True,
                        _hover={"background": _COLOR_ACCENT_LIGHT},
                        border_radius="8px",
                        width="100%",
                    )
                    for icon, label, url in links
                ],
                spacing="1",
                width="100%",
            ),
            spacing="3",
            padding="16px",
            background=_COLOR_CARD,
            border_radius="12px",
            border=f"1px solid {_COLOR_BORDER}",
            width="100%",
        )

    # ── 主页面 ────────────────────────────────────────────────────────
    def admin_devops_page():
        return rx.box(
            # 侧边栏
            _sidebar(),
            # 主内容区
            rx.box(
                rx.vstack(
                    # 页面标题
                    rx.hstack(
                        rx.vstack(
                            rx.heading("开发运维", size="7", color=_COLOR_DARK),
                            rx.text(
                                "按顺序完成运维步骤，确保项目环境规范就绪",
                                size="2",
                                color=_COLOR_GRAY,
                            ),
                            spacing="0",
                        ),
                        width="100%",
                    ),

                    # 两栏布局
                    rx.box(
                        # 左栏：脚本执行区
                        rx.vstack(
                            rx.text("自动化脚本执行", size="3", weight="bold",
                                    color=_COLOR_DARK),
                            # 脚本选择
                            rx.text("选择脚本", size="2", weight="medium", color=_COLOR_GRAY),
                            rx.vstack(
                                rx.foreach(
                                    ScriptExecuteState.available_scripts,
                                    _script_card,
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            # 进度条
                            rx.cond(
                                ScriptExecuteState.is_running | ScriptExecuteState.is_failed | ScriptExecuteState.is_success,
                                _progress_bar(),
                            ),
                            # 控制台
                            rx.text("执行控制台", size="2", weight="medium", color=_COLOR_GRAY),
                            _console_output(),
                            # 错误日志
                            _error_log_panel(),
                            spacing="4",
                            width="100%",
                        ),
                        # 右栏：汇总和链接
                        rx.vstack(
                            _step_summary(),
                            _quick_links(),
                            spacing="4",
                            width="280px",
                            flex_shrink="0",
                        ),
                        display="flex",
                        gap="24px",
                        width="100%",
                    ),
                    spacing="6",
                    width="100%",
                    max_width="1100px",
                ),
                margin_left="224px",
                padding="32px",
                width="100%",
            ),
            min_height="100vh",
            background=_COLOR_BG,
            width="100%",
        )