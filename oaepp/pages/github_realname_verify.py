"""
F-T-003 GitHub账号实名核查（含AI审查）— 教师端页面

对应原型：prototype/admin_students.html（AI实名审查部分）
路由：/github_realname_verify（由 app.py 自动发现机制注册）

功能：
- AI 自动审查GitHub name字段是否为真实中文姓名
- 教师查看审查结果并可逐条人工确认
- 支持批量通过高置信度条目
- 向未填写姓名的学生发送提醒
"""

try:
    import reflex as rx
except Exception:
    rx = None

github_realname_verify_page = None

if rx is not None:
    try:
        from states.github_realname_verify import GitHubRealnameVerifyState
    except ImportError:
        from oaepp.states.github_realname_verify import (
            GitHubRealnameVerifyState,
        )

    # ── 颜色常量 ──────────────────────────────────────────────────────
    _BG = "#f8fafc"
    _CARD = "#ffffff"
    _BORDER = "#e2e8f0"
    _ACCENT = "#4f46e5"          # indigo-600
    _ACCENT_LIGHT = "#eef2ff"    # indigo-50
    _ACCENT_HOVER = "#4338ca"    # indigo-700
    _GREEN = "#16a34a"
    _GREEN_BG = "#f0fdf4"
    _GREEN_BORDER = "#bbf7d0"
    _ORANGE = "#ea580c"
    _ORANGE_BG = "#fff7ed"
    _ORANGE_BORDER = "#fed7aa"
    _RED = "#dc2626"
    _RED_BG = "#fef2f2"
    _RED_BORDER = "#fecaca"
    _YELLOW = "#ca8a04"
    _YELLOW_BG = "#fefce8"
    _GRAY = "#6b7280"
    _GRAY_LIGHT = "#9ca3af"
    _DARK = "#1f2937"
    _WHITE = "#ffffff"

    # ── 侧边栏 ─────────────────────────────────────────────────────────
    def _sidebar() -> rx.Component:
        """教师端侧边栏导航"""
        return rx.box(
            rx.vstack(
                # Logo 区域
                rx.hstack(
                    rx.box(
                        rx.icon("shield-check", size=18, color="white"),
                        width="32px", height="32px",
                        border_radius="8px",
                        background=_ACCENT,
                        display="flex", align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("OA-EPP", weight="bold", color=_DARK, size="2"),
                        rx.text("教师端", size="1", background=_ACCENT_LIGHT,
                                color=_ACCENT, padding_x="6px", padding_y="1px",
                                border_radius="full"),
                        spacing="0",
                    ),
                    spacing="2",
                ),
                padding_x="20px", padding_y="20px",
                border_bottom=f"1px solid {_BORDER}",
                width="100%",
            ),
            # 导航菜单
            rx.vstack(
                _nav_item("学生管理", "users", True, href="/admin_students"),
                _nav_item("开发运维", "terminal", False, href="/admin_devops"),
                _nav_item("成绩管理", "bar-chart-3", False, href="/admin_grades"),
                _nav_item("系统设置", "settings", False, href="/admin_settings"),
                _nav_item(
                    "GitHub实名核查", "fingerprint", True,
                    href="/github_realname_verify", is_active_override=True,
                ),
                spacing="1",
                padding_x="12px", padding_y="16px",
                width="100%",
            ),
            # 底部用户信息
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.text("教", weight="bold", size="2", color=_ACCENT),
                        width="32px", height="32px",
                        border_radius="full",
                        background=_ACCENT_LIGHT,
                        display="flex", align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("教师", weight="medium", size="2", color=_DARK),
                        rx.text("admin", size="1", color=_GRAY_LIGHT),
                        spacing="0",
                    ),
                    spacing="3",
                ),
                rx.link(
                    rx.text("退出登录", size="1", color=_GRAY_LIGHT,
                            _hover={"color": _RED}),
                    href="/",
                ),
                padding_x="20px", padding_y="16px",
                border_top=f"1px solid {_BORDER}",
                width="100%",
                spacing="3",
            ),
            width="224px", min_height="100vh",
            position="fixed", left="0", top="0",
            background=_CARD,
            border_right=f"1px solid {_BORDER}",
            z_index="10",
            justify_content="space-between",
        )

    def _nav_item(
        label: str, icon: str, active: bool = False,
        href: str = "#", is_active_override: bool = False,
    ) -> rx.Component:
        """单个导航项"""
        is_current = is_active_override or active
        return rx.link(
            rx.hstack(
                rx.icon(icon, size=16,
                        color=_ACCENT if is_current else _GRAY),
                rx.text(label, size="2",
                        color=_ACCENT if is_current else _GRAY,
                        weight="medium" if is_current else "regular"),
                spacing="3",
                padding_x="12px", padding_y="10px",
                width="100%",
            ),
            href=href,
            width="100%",
        )

    # ── 统计卡片 ──────────────────────────────────────────────────────
    def _stat_card(
        label: str, value, color: str = _DARK, bg: str = _CARD,
        subtitle: str = "",
    ) -> rx.Component:
        """统计数字卡片"""
        return rx.box(
            rx.vstack(
                rx.text(label, size="1", color=_GRAY),
                rx.heading(value, size="6", color=color),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, size="1", color=_GRAY_LIGHT),
                ),
                spacing="1",
                align="start",
            ),
            padding="16px 20px",
            border_radius="12px",
            background=bg,
            border=f"1px solid {_BORDER}",
            flex="1",
        )

    # ── 徽章组件 ──────────────────────────────────────────────────────
    def _ai_verdict_badge(verdict: str) -> rx.Component:
        """AI判断结论徽章"""
        return rx.match(
            verdict,
            ("suspected_real",
             rx.badge("✅ 疑似真名", color_scheme="green", variant="soft",
                      size="1")),
            ("not_filled",
             rx.badge("❌ 未填写", color_scheme="gray", variant="soft",
                      size="1")),
            ("pending_review",
             rx.badge("⚠️ 待审查", color_scheme="orange", variant="soft",
                      size="1")),
            rx.badge("— 未审查", color_scheme="gray", variant="soft",
                     size="1"),
        )

    def _confidence_badge(confidence: str) -> rx.Component:
        """置信度徽章"""
        return rx.match(
            confidence,
            ("high",
             rx.badge("高", color_scheme="green", variant="soft", size="1")),
            ("medium",
             rx.badge("中", color_scheme="orange", variant="soft", size="1")),
            ("low",
             rx.badge("低", color_scheme="red", variant="soft", size="1")),
            rx.text("—", size="1", color=_GRAY_LIGHT),
        )

    def _human_confirm_badge(status: str) -> rx.Component:
        """人工确认状态徽章"""
        return rx.match(
            status,
            ("passed",
             rx.badge("✅ 已通过", color_scheme="green", variant="soft",
                      size="1")),
            ("abnormal",
             rx.badge("⚠️ 异常", color_scheme="red", variant="soft",
                      size="1")),
            rx.badge("待处理", color_scheme="gray", variant="soft", size="1"),
        )

    # ── 表格行 ────────────────────────────────────────────────────────
    def _verification_row(item: dict) -> rx.Component:
        """单条核查记录行"""
        return rx.table.row(
            rx.table.cell(
                rx.cond(
                    item["verify_status"] != "unbound",
                    rx.checkbox(
                        value=item["id"].to(str),
                        color_scheme="indigo",
                        size="1",
                    ),
                ),
                width="40px",
            ),
            rx.table.cell(
                rx.vstack(
                    rx.text(item["student_name"], weight="medium", size="2",
                            color=_DARK),
                    rx.text(item["student_no"], size="1", color=_GRAY_LIGHT),
                    spacing="0",
                ),
            ),
            rx.table.cell(
                rx.text(item["github_username"], size="2",
                        color=rx.cond(
                            item["verify_status"] != "unbound",
                            _ACCENT,
                            _GRAY_LIGHT,
                        )),
            ),
            rx.table.cell(
                rx.cond(
                    item["is_name_empty"],
                    rx.text("（未设置）", size="2", color=_GRAY_LIGHT,
                            font_style="italic"),
                    rx.text(item["github_name"], size="2",
                            color=rx.cond(
                                item["ai_verdict"] == "pending_review",
                                _ORANGE,
                                _DARK,
                            )),
                ),
            ),
            rx.table.cell(
                _ai_verdict_badge(item.get("ai_verdict", "")),
            ),
            rx.table.cell(
                _confidence_badge(item.get("ai_confidence", "")),
            ),
            rx.table.cell(
                rx.tooltip(
                    rx.text(
                        item.get("ai_reason", "—"),
                        size="1", color=_GRAY,
                    ),
                    content=item.get("ai_reason", "暂无判断理由"),
                ),
                max_width="200px",
            ),
            rx.table.cell(
                _human_confirm_badge(item.get("human_confirm", "pending")),
            ),
            rx.table.cell(
                rx.cond(
                    item["verify_status"] != "unbound",
                    rx.hstack(
                        # 通过按钮
                        rx.cond(
                            item.get("human_confirm") != "passed",
                            rx.button(
                                rx.icon("check", size=14),
                                "通过",
                                size="1",
                                color_scheme="green",
                                variant="soft",
                                on_click=lambda: GitHubRealnameVerifyState.human_pass(
                                    item["id"]
                                ),
                            ),
                        ),
                        # 标记异常按钮
                        rx.cond(
                            item.get("human_confirm") != "abnormal",
                            rx.button(
                                rx.icon("triangle-alert", size=14),
                                "标记异常",
                                size="1",
                                color_scheme="red",
                                variant="soft",
                                on_click=lambda: GitHubRealnameVerifyState.human_mark_abnormal(
                                    item["id"]
                                ),
                            ),
                        ),
                        # 发提醒按钮
                        rx.button(
                            rx.icon("bell", size=14),
                            "发提醒",
                            size="1",
                            color_scheme="gray",
                            variant="soft",
                            on_click=lambda: GitHubRealnameVerifyState.send_reminder(
                                item["id"]
                            ),
                        ),
                        # 重新核查按钮
                        rx.button(
                            rx.icon("refresh-cw", size=14),
                            size="1",
                            color_scheme="blue",
                            variant="ghost",
                            on_click=lambda: GitHubRealnameVerifyState.verify_single(
                                item["id"]
                            ),
                        ),
                        spacing="2",
                        justify="end",
                    ),
                    # 未绑定：显示发提醒按钮
                    rx.button(
                        rx.icon("bell", size=14),
                        "发提醒绑定",
                        size="1",
                        color_scheme="gray",
                        variant="soft",
                    ),
                ),
                min_width="280px",
            ),
            background=rx.cond(
                item.get("ai_verdict") == "pending_review",
                _ORANGE_BG,
                rx.cond(
                    item["verify_status"] == "unbound",
                    _RED_BG,
                    "transparent",
                ),
            ),
            _hover={"background": "#f1f5f9"},
        )

    # ── 头部操作栏 ────────────────────────────────────────────────────
    def _header() -> rx.Component:
        """页面头部：标题 + 操作按钮"""
        return rx.hstack(
            rx.vstack(
                rx.heading("GitHub 账号实名核查", size="6", color=_DARK),
                rx.text(
                    "AI 检测 GitHub profile name 字段是否为真实中文姓名，"
                    "标记疑似异常条目供教师人工确认",
                    size="2", color=_GRAY,
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("brain", size=16),
                    "AI 实名审查",
                    color_scheme="orange",
                    variant="soft",
                    size="2",
                    loading=GitHubRealnameVerifyState.is_verifying,
                    on_click=GitHubRealnameVerifyState.verify_all,
                ),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "一键全班核查",
                    color_scheme="indigo",
                    size="2",
                    loading=GitHubRealnameVerifyState.is_verifying,
                    on_click=GitHubRealnameVerifyState.verify_all,
                ),
                spacing="3",
            ),
            spacing="4",
            justify="between",
            width="100%",
            padding_bottom="24px",
        )

    # ── 统计行 ────────────────────────────────────────────────────────
    def _stats_row() -> rx.Component:
        """五个统计卡片"""
        return rx.hstack(
            _stat_card("全班人数", GitHubRealnameVerifyState.total_students,
                       color=_DARK),
            _stat_card("已绑定", GitHubRealnameVerifyState.bound_count,
                       color=_GREEN),
            _stat_card("待审核", GitHubRealnameVerifyState.pending_bind_count,
                       color=_YELLOW),
            _stat_card("未绑定", GitHubRealnameVerifyState.unbound_count,
                       color=_RED),
            _stat_card(
                "AI 审查待确认",
                GitHubRealnameVerifyState.ai_pending_review_count,
                color=_ORANGE,
                bg="#fff7ed",
                subtitle="待人工复核",
            ),
            spacing="4",
            width="100%",
            padding_bottom="24px",
        )

    # ── AI审查队列面板 ────────────────────────────────────────────────
    def _ai_review_panel() -> rx.Component:
        """AI 实名自动审查队列主面板"""
        return rx.box(
            # 面板头部
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon("brain", size=16, color=_ORANGE),
                        width="32px", height="32px",
                        border_radius="8px",
                        background=_ORANGE_BG,
                        display="flex", align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("AI 实名自动审查队列", weight="bold",
                                size="3", color=_DARK),
                        rx.text(
                            "AI 检测 GitHub name 字段是否为汉语姓名，"
                            "标记疑似异常条目供教师人工确认",
                            size="1", color=_GRAY,
                        ),
                        spacing="0",
                    ),
                    spacing="3",
                ),
                rx.spacer(),
                rx.hstack(
                    # 统计摘要
                    rx.hstack(
                        rx.text("通过 ", size="1", color=_GREEN),
                        rx.text(
                            GitHubRealnameVerifyState.ai_passed_count,
                            size="1", color=_GREEN, weight="bold",
                        ),
                        rx.text(" 人", size="1", color=_GREEN),
                        spacing="0",
                    ),
                    rx.text("·", size="1", color=_GRAY_LIGHT),
                    rx.hstack(
                        rx.text("待审查 ", size="1", color=_ORANGE),
                        rx.text(
                            GitHubRealnameVerifyState.ai_review_count,
                            size="1", color=_ORANGE, weight="bold",
                        ),
                        rx.text(" 人", size="1", color=_ORANGE),
                        spacing="0",
                    ),
                    rx.text("·", size="1", color=_GRAY_LIGHT),
                    rx.hstack(
                        rx.text("未设置 ", size="1", color=_GRAY),
                        rx.text(
                            GitHubRealnameVerifyState.ai_not_filled_count,
                            size="1", color=_GRAY, weight="bold",
                        ),
                        rx.text(" 人", size="1", color=_GRAY),
                        spacing="0",
                    ),
                    rx.button(
                        "批量通过高置信度",
                        size="1",
                        color_scheme="orange",
                        loading=GitHubRealnameVerifyState.is_batch_processing,
                        on_click=GitHubRealnameVerifyState.batch_pass_high_confidence,
                    ),
                    spacing="3",
                ),
                justify="between",
                width="100%",
                padding="16px 20px",
                border_bottom=f"1px solid {_ORANGE_BORDER}",
            ),

            # AI 判断规则说明
            rx.box(
                rx.hstack(
                    rx.icon("info", size=14, color=_ORANGE),
                    rx.text(
                        "AI 判断规则：✅ 疑似真名 = 含 CJK 汉字 + 2–4 字 + 常见姓氏匹配；"
                        "⚠️ 待审查 = 纯英文/拼音/数字/昵称特征、长度异常；"
                        "❌ 未设置 = name 字段为空。AI 结论仅供参考，以教师人工确认为准。",
                        size="1", color=_ORANGE,
                    ),
                    spacing="2",
                    align="start",
                ),
                padding="12px 20px",
                background=_ORANGE_BG,
                border_bottom=f"1px solid {_ORANGE_BORDER}",
            ),

            # 筛选栏
            rx.hstack(
                rx.input(
                    placeholder="搜索学号/姓名/GitHub用户名...",
                    size="2",
                    width="300px",
                    on_change=GitHubRealnameVerifyState.set_search_keyword,
                    on_blur=GitHubRealnameVerifyState.load_verification_list,
                ),
                rx.select(
                    ["全部", "疑似真名", "待人工审查", "未填写"],
                    default_value="全部",
                    size="2",
                    width="150px",
                    on_change=GitHubRealnameVerifyState.set_filter_ai_verdict,
                ),
                rx.button(
                    "筛选",
                    size="2",
                    color_scheme="indigo",
                    variant="outline",
                    on_click=GitHubRealnameVerifyState.load_verification_list,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("bell", size=14),
                    "向未填写姓名学生批量发提醒",
                    size="1",
                    color_scheme="orange",
                    variant="soft",
                    loading=GitHubRealnameVerifyState.is_batch_processing,
                    on_click=GitHubRealnameVerifyState.batch_send_reminder_not_filled,
                ),
                spacing="3",
                padding="12px 20px",
                border_bottom=f"1px solid {_BORDER}",
            ),

            # 数据表格
            rx.box(
                rx.cond(
                    GitHubRealnameVerifyState.is_loading,
                    rx.center(
                        rx.vstack(
                            rx.spinner(color="indigo", size="3"),
                            rx.text("加载中...", size="2", color=_GRAY),
                            spacing="3",
                            padding="48px",
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        GitHubRealnameVerifyState.verification_list.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon("search-x", size=48, color=_GRAY_LIGHT),
                                rx.text("暂无核查数据", size="3", color=_GRAY),
                                rx.text(
                                    "请先导入学生名单并完成 GitHub 账号绑定",
                                    size="2", color=_GRAY_LIGHT,
                                ),
                                spacing="3",
                                padding="48px",
                            ),
                            width="100%",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(
                                        rx.checkbox(size="1", color_scheme="indigo"),
                                        width="40px",
                                    ),
                                    rx.table.column_header_cell(
                                        "学号 / 姓名", width="130px"
                                    ),
                                    rx.table.column_header_cell(
                                        "GitHub 用户名", width="130px"
                                    ),
                                    rx.table.column_header_cell(
                                        "GitHub 实名（name 字段）", width="150px"
                                    ),
                                    rx.table.column_header_cell(
                                        "AI 判断", width="110px"
                                    ),
                                    rx.table.column_header_cell(
                                        "置信度", width="70px"
                                    ),
                                    rx.table.column_header_cell(
                                        "AI 判断理由", width="200px"
                                    ),
                                    rx.table.column_header_cell(
                                        "人工确认", width="100px"
                                    ),
                                    rx.table.column_header_cell(
                                        "操作", width="280px"
                                    ),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    GitHubRealnameVerifyState.verification_list,
                                    _verification_row,
                                ),
                            ),
                            width="100%",
                            size="1",
                            variant="surface",
                        ),
                    ),
                ),
                width="100%",
                overflow_x="auto",
            ),

            # 底部汇总信息
            rx.hstack(
                rx.text(
                    GitHubRealnameVerifyState.summary_text,
                    size="1", color=_GRAY_LIGHT,
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text("共 ", size="1", color=_GRAY_LIGHT),
                    rx.text(
                        GitHubRealnameVerifyState.list_count,
                        size="1", color=_DARK, weight="bold",
                    ),
                    rx.text(" 条记录", size="1", color=_GRAY_LIGHT),
                    spacing="1",
                ),
                padding="12px 20px",
                border_top=f"1px solid {_BORDER}",
            ),

            border_radius="12px",
            border=f"1px solid {_ORANGE_BORDER}",
            background=_CARD,
            width="100%",
        )

    # ── 操作结果提示 ──────────────────────────────────────────────────
    def _action_toast() -> rx.Component:
        """操作结果提示条"""
        return rx.cond(
            GitHubRealnameVerifyState.action_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("info", size=14, color=_ACCENT),
                    rx.text(GitHubRealnameVerifyState.action_message,
                            size="2", color=_DARK),
                    rx.button(
                        rx.icon("x", size=12),
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=GitHubRealnameVerifyState.clear_action_message,
                    ),
                    spacing="3",
                    padding="10px 16px",
                    width="100%",
                ),
                border_radius="8px",
                background=_ACCENT_LIGHT,
                border=f"1px solid {_ACCENT}20",
                width="100%",
                margin_bottom="16px",
            ),
        )

    # ═════════════════════════════════════════════════════════════════════
    #  主页面
    # ═════════════════════════════════════════════════════════════════════

    def github_realname_verify_page() -> rx.Component:
        """GitHub 账号实名核查（含 AI 审查）页面"""
        return rx.box(
            _sidebar(),
            # 主内容区
            rx.box(
                _action_toast(),
                _header(),
                _stats_row(),
                _ai_review_panel(),
                margin_left="224px",
                min_height="100vh",
                background=_BG,
                padding="28px 32px",
            ),
            width="100%",
            on_mount=GitHubRealnameVerifyState.on_mount,
        )
