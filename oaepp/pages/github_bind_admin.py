"""
F-S-003 教师审核页 — GitHub 账号绑定审核
Route: /github_bind_admin
"""

try:
    import reflex as rx
except Exception:
    rx = None

# ── 双路径导入 ────────────────────────────────────────────────────────
try:
    from oaepp.states.github_bind_admin import GitHubBindAdminState
    HAS_ADMIN_STATE = True
except Exception:
    try:
        from states.github_bind_admin import GitHubBindAdminState  # type: ignore[no-redef]
        HAS_ADMIN_STATE = True
    except Exception:
        HAS_ADMIN_STATE = False
        GitHubBindAdminState = None  # type: ignore

# ── 回退占位（当 State 加载失败时保证页面不会崩溃） ────────────
if rx is not None and GitHubBindAdminState is None:
    GitHubBindAdminState = rx.State


def binding_card(item: dict):
    """单条绑定申请卡片"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text("学号:", weight="bold", size="2"),
                rx.text(item["student_no"], size="2"),
                rx.spacer(),
                # 徽章：is_pending_release → 待解除
                rx.cond(
                    item["is_pending_release"],
                    rx.badge("待解除", color_scheme="purple"),
                    rx.badge(
                        rx.match(
                            item["verify_status"],
                            ("pending", "待审核"),
                            ("approved", "已批准"),
                            ("rejected", "已拒绝"),
                            "未知",
                        ),
                        color_scheme=rx.match(
                            item["verify_status"],
                            ("pending", "orange"),
                            ("approved", "green"),
                            ("rejected", "red"),
                            "gray",
                        ),
                    ),
                ),
                spacing="2",
            ),
            rx.hstack(
                rx.text("姓名:", weight="bold", size="2"),
                rx.text(item["student_name"], size="2"),
                spacing="2",
            ),
            rx.hstack(
                rx.text("GitHub:", weight="bold", size="2"),
                rx.text(item["github_username"], size="2"),
                rx.text("|", size="2", color="gray"),
                rx.text(item["github_name"], size="2", color="gray"),
                spacing="2",
            ),
            rx.cond(
                item["verify_status"] == "pending",
                rx.hstack(
                    rx.button(
                        "✓ 批准",
                        on_click=lambda: GitHubBindAdminState.approve_binding(item["id"]),
                        size="1",
                        color_scheme="green",
                    ),
                    rx.button(
                        "✗ 拒绝",
                        on_click=lambda: GitHubBindAdminState.reject_binding(item["id"]),
                        size="1",
                        color_scheme="red",
                        variant="outline",
                    ),
                    spacing="2",
                ),
            ),
            rx.cond(
                item["is_pending_release"],
                rx.hstack(
                    rx.button(
                        "✓ 同意解除",
                        on_click=lambda: GitHubBindAdminState.approve_unbind(item["id"]),
                        size="1",
                        color_scheme="green",
                    ),
                    rx.button(
                        "✗ 拒绝解除",
                        on_click=lambda: GitHubBindAdminState.reject_unbind(item["id"]),
                        size="1",
                        color_scheme="red",
                        variant="outline",
                    ),
                    spacing="2",
                ),
            ),
            spacing="2",
            align="start",
        ),
        size="2",
        width="100%",
    )


def github_bind_admin_page():
    """GitHub 绑定审核管理页面"""
    return rx.center(
        rx.box(
            rx.vstack(
                rx.heading("GitHub 账号绑定审核", size="5"),
                rx.text("管理学生的 GitHub 账号绑定申请", color="gray", size="2"),

                rx.button(
                    "刷新列表",
                    on_click=GitHubBindAdminState.load_pending_list,
                    size="1",
                    variant="soft",
                ),

                rx.divider(),

                # ── 绑定申请列表 ──
                rx.cond(
                    GitHubBindAdminState.is_loading,
                    rx.center(rx.text("加载中...", size="2", color="gray")),
                    rx.cond(
                        GitHubBindAdminState.pending_list.length() == 0,
                        rx.text("暂无绑定申请记录", size="2", color="gray"),
                        rx.vstack(
                            rx.foreach(
                                GitHubBindAdminState.pending_list,
                                binding_card,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                ),

                width="100%",
                max_width="700px",
                spacing="4",
                padding="4",
            ),
            width="100%",
        ),
        width="100%",
        min_height="80vh",
        padding="4",
        on_mount=GitHubBindAdminState.load_pending_list,
    )

