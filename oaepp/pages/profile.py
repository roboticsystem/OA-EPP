"""
Reflex profile page with GitHub binding (F-S-002 + F-S-003).
Provides `profile_page` when Reflex is available.
"""
try:
    import reflex as rx
except Exception:
    rx = None

# 尝试导入 GitHubBindState，如果失败则使用简化版
try:
    from states.github_bind import GitHubBindState
    HAS_GITHUB_STATE = True
except Exception:
    HAS_GITHUB_STATE = False
    GitHubBindState = None

profile_page = None
if rx is not None:
    def github_bind_section():
        """GitHub 账号绑定功能模块（F-S-003）"""
        if HAS_GITHUB_STATE:
            return rx.box(
                rx.vstack(
                    rx.heading("GitHub 账号绑定", size="4"),
                    rx.text(
                        "绑定您的 GitHub 账号，用于代码提交和 PR 记录追踪",
                        color="gray",
                        size="2",
                    ),
                    rx.divider(),
                    # 自动刷新触发器（隐藏）
                    rx.button(
                        "自动刷新",
                        on_click=GitHubBindState.show_current_status,
                        style={"display": "none"},
                        id="auto-refresh-trigger"
                    ),
                    rx.script("""
                        setTimeout(() => {
                            const btn = document.getElementById('auto-refresh-trigger');
                            if (btn) btn.click();
                        }, 500);
                    """),

                    # 绑定状态显示
                    rx.cond(
                        GitHubBindState.bind_status == "unbound",
                        rx.badge("未绑定", color_scheme="gray"),
                    ),
                    rx.cond(
                        GitHubBindState.bind_status == "pending",
                        rx.badge("待审核", color_scheme="orange"),
                    ),
                    rx.cond(
                        GitHubBindState.bind_status == "approved",
                        rx.badge("已绑定", color_scheme="green"),
                    ),
                    rx.cond(
                        GitHubBindState.bind_status == "rejected",
                        rx.badge("已拒绝", color_scheme="red"),
                    ),

                    # 未绑定或已拒绝状态：显示输入框
                    rx.cond(
                        (GitHubBindState.bind_status == "unbound") | 
                        (GitHubBindState.bind_status == "rejected"),
                        rx.vstack(
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

                            # 验证结果提示
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

                    # 待审核状态
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

                    # 已绑定状态
                    rx.cond(
                        GitHubBindState.bind_status == "approved",
                        rx.box(
                            rx.vstack(
                                rx.text("✅ 已绑定 GitHub 账号", weight="medium", size="2", color="green"),
                                rx.text(
                                    f"GitHub 用户名: {GitHubBindState.github_username}",
                                    size="1",
                                    color="gray",
                                ),
                                rx.text(
                                    "如需修改绑定账号，请向教师申请解除当前绑定后重新提交。",
                                    size="1",
                                    color="orange",
                                    font_weight="medium",
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

                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                padding="20px",
                border="1px solid #e2e8f0",
                border_radius="12px",
                background="white",
                width="100%",
            )
        else:
            # 简化版：无 State 管理，仅展示 UI
            return rx.box(
                rx.vstack(
                    rx.heading("GitHub 账号绑定", size="4"),
                    rx.text(
                        "绑定您的 GitHub 账号，用于代码提交和 PR 记录追踪",
                        color="gray",
                        size="2",
                    ),
                    rx.divider(),
                    rx.badge("未绑定", color_scheme="gray"),
                    rx.text("输入 GitHub 用户名：", weight="medium", size="2"),
                    rx.input(
                        placeholder="请输入您的 GitHub 用户名",
                        size="2",
                        width="100%",
                    ),
                    rx.button("验证", size="2", variant="outline"),
                    rx.button("提交绑定申请", size="2", variant="solid", color_scheme="blue"),
                    rx.text(
                        "提交后需教师审核确认，审核通过后生效",
                        size="1",
                        color="gray",
                    ),
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
                padding="20px",
                border="1px solid #e2e8f0",
                border_radius="12px",
                background="white",
                width="100%",
            )
    
    def profile_page():
        return rx.center(
            rx.box(
                rx.vstack(
                    # GitHub 账号绑定模块（F-S-003）
                    github_bind_section(),
                    rx.divider(),
                ),
                max_width="600px",
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
        )
