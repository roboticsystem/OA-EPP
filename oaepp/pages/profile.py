"""
Reflex profile page with GitHub binding (F-S-002 + F-S-003).
Provides `profile_page` when Reflex is available.
"""

try:
    import reflex as rx
except Exception:
    rx = None

# ── 双路径导入 GitHubBindState ────────────────────────────────────────
try:
    from oaepp.states.github_bind import GitHubBindState
    HAS_GITHUB_STATE = True
except Exception:
    try:
        from states.github_bind import GitHubBindState  # type: ignore[no-redef]
        HAS_GITHUB_STATE = True
    except Exception:
        HAS_GITHUB_STATE = False
        GitHubBindState = None

profile_page = None
if rx is not None:

    def github_bind_section():
        """GitHub 账号绑定模块（F-S-003）—— 事件驱动，无隐藏按钮"""
        if not HAS_GITHUB_STATE:
            return rx.fragment()

        return rx.box(
            rx.vstack(
                # ── 标题 ──
                rx.heading("GitHub 账号绑定", size="4"),
                rx.text(
                    "绑定您的 GitHub 账号，用于代码提交和 PR 记录追踪",
                    color="gray",
                    size="2",
                ),
                rx.divider(),

                # ── 状态行 + 刷新按钮 ──
                rx.hstack(
                    rx.text("当前状态：", size="2", weight="medium"),
                    rx.match(
                        GitHubBindState.bind_status,
                        ("unbound", rx.badge("未绑定", color_scheme="gray")),
                        ("pending", rx.badge("待审核", color_scheme="orange")),
                        ("approved", rx.badge("已绑定", color_scheme="green")),
                        ("pending_release", rx.badge("待解除", color_scheme="purple")),
                        ("rejected", rx.badge("已拒绝", color_scheme="red")),
                        rx.badge("未知", color_scheme="gray"),
                    ),
                    rx.spacer(),
                    rx.button(
                        "刷新绑定状态",
                        on_click=GitHubBindState.refresh_bind_status,
                        id="refresh-bind-btn",
                        size="1",
                        variant="soft",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),

                # ── 未绑定 / 已拒绝 → 显示输入框 ──
                rx.cond(
                    (GitHubBindState.bind_status == "unbound")
                    | (GitHubBindState.bind_status == "rejected"),
                    rx.vstack(
                        # 输入行
                        rx.hstack(
                            rx.text("GitHub 用户名:", weight="medium", size="2"),
                            rx.input(
                                placeholder="请输入您的 GitHub 用户名",
                                value=GitHubBindState.github_username,
                                on_change=GitHubBindState.set_github_username,
                                size="2",
                                width="300px",
                            ),
                            rx.button(
                                "验证",
                                on_click=GitHubBindState.validate_github_username,
                                loading=GitHubBindState.is_validating,
                                disabled=GitHubBindState.is_validating,
                                size="2",
                                variant="outline",
                            ),
                            spacing="2",
                            align="center",
                        ),

                        # 验证结果
                        rx.cond(
                            GitHubBindState.validation_message != "",
                            rx.text(
                                GitHubBindState.validation_message,
                                size="2",
                                color="blue",
                            ),
                        ),

                        # 提交按钮
                        rx.button(
                            "提交绑定申请",
                            on_click=GitHubBindState.submit_bind_request,
                            loading=GitHubBindState.is_submitting,
                            size="2",
                            variant="solid",
                            color_scheme="blue",
                        ),

                        rx.text(
                            "提交后需教师审核确认，审核通过后生效",
                            size="1",
                            color="gray",
                        ),

                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                ),

                # ── 待审核状态 ──
                rx.cond(
                    GitHubBindState.bind_status == "pending",
                    rx.box(
                        rx.vstack(
                            rx.text("⌛ 绑定申请审核中", weight="medium", size="2"),
                            rx.text(
                                "请耐心等待教师审核，审核通过后会自动生效",
                                size="1",
                                color="gray",
                            ),
                            spacing="2",
                            width="100%",
                            align="stretch",
                        ),
                        padding="12px",
                        border="1px solid #fed7aa",
                        border_radius="8px",
                        background="#fff7ed",
                        width="100%",
                    ),
                ),

                # ── 已绑定状态 ──
                rx.cond(
                    GitHubBindState.bind_status == "approved",
                    rx.box(
                        rx.vstack(
                            rx.text("✅ 已绑定 GitHub 账号", weight="medium", size="2", color="green"),
                            rx.hstack(
                                rx.text("GitHub 用户名:", size="1", color="gray"),
                                rx.text(GitHubBindState.github_username, size="1", color="gray"),
                            ),
                            rx.text(
                                "如需修改绑定账号，请先申请解除当前绑定。",
                                size="1",
                                color="orange",
                                weight="medium",
                            ),
                            rx.button(
                                "申请解除绑定",
                                on_click=GitHubBindState.request_unbind,
                                size="1",
                                variant="outline",
                                color_scheme="red",
                            ),
                            spacing="2",
                            width="100%",
                            align="stretch",
                        ),
                        padding="12px",
                        border="1px solid #86efac",
                        border_radius="8px",
                        background="#f0fdf4",
                        width="100%",
                    ),
                ),

                # ── 待解除绑定状态 ──
                rx.cond(
                    GitHubBindState.bind_status == "pending_release",
                    rx.box(
                        rx.vstack(
                            rx.text("⏳ 解除绑定申请待审核", weight="medium", size="2", color="orange"),
                            rx.hstack(
                                rx.text("GitHub 用户名:", size="1", color="gray"),
                                rx.text(GitHubBindState.github_username, size="1", color="gray"),
                            ),
                            rx.text(
                                "请等待教师审核解除绑定申请，审核通过后可重新绑定新账号。",
                                size="1",
                                color="gray",
                            ),
                            spacing="2",
                            width="100%",
                            align="stretch",
                        ),
                        padding="12px",
                        border="1px solid #fed7aa",
                        border_radius="8px",
                        background="#fff7ed",
                        width="100%",
                    ),
                ),

                spacing="4",
                width="100%",
                align="stretch",
            ),
            width="100%",
        )

    def profile_page():
        """个人资料页（含 GitHub 绑定模块 + 页面加载自动查询状态）"""
        return rx.center(
            rx.box(
                rx.vstack(
                    # ── 用户信息 ──
                    rx.avatar(name="用户", size="9"),
                    rx.heading("个人资料", size="6"),
                    rx.text("这里将展示用户信息", color="gray"),

                    rx.divider(),

                    # ── GitHub 账号绑定模块 ──
                    github_bind_section(),

                    rx.divider(),

                    rx.button("返回首页", on_click=rx.redirect("/")),

                    # ── Toast 提示 ──
                    rx.toast.provider(),

                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                max_width="520px",
                width="100%",
                padding="28px",
                border_radius="12px",
                box_shadow="0 10px 30px rgba(0,0,0,0.08)",
                background="white",
            ),
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
            padding="20px",
            on_mount=GitHubBindState.load_bind_status if HAS_GITHUB_STATE else None,
        )
