"""
F-T-009 学生仓库访问权限配置 — Reflex page
对齐 prototype/admin_settings.html Tab 2
"""
try:
    import reflex as rx
except Exception:
    rx = None

admin_repo_permissions_page = None
if rx is not None:
    try:
        from states.teacher_repo_perm import RepoPermState
    except ImportError:
        from oaepp.states.teacher_repo_perm import RepoPermState

    _BG = "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)"

    def admin_repo_permissions_page():
        return rx.center(
            rx.box(
                rx.vstack(
                    rx.heading("学生仓库访问权限配置", size="6"),
                    rx.text(
                        "通过 GitHub Organization + Team 统一管理班级仓库权限",
                        color="gray",
                        size="1",
                    ),

                    # ── 配置区域：Org + Team ──
                    rx.flex(
                        # Org 信息卡片
                        rx.box(
                            rx.vstack(
                                rx.heading("GitHub Organization", size="3", color="gray"),
                                rx.text("组织名称", size="1", color="gray"),
                                rx.input(
                                    value=RepoPermState.org_name,
                                    on_change=RepoPermState.set_org_name,
                                    placeholder="oa-epp-2025",
                                    width="100%",
                                ),
                                rx.text("课程仓库名", size="1", color="gray"),
                                rx.input(
                                    value=RepoPermState.repo_name,
                                    on_change=RepoPermState.set_repo_name,
                                    placeholder="oa-epp-platform",
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            border="1px solid #e5e7eb",
                            border_radius="8px",
                            padding="14px",
                            flex="1",
                        ),
                        # Team 配置卡片
                        rx.box(
                            rx.vstack(
                                rx.heading("班级 Team", size="3", color="gray"),
                                rx.text("Team 名称", size="1", color="gray"),
                                rx.input(
                                    value=RepoPermState.team_name,
                                    on_change=RepoPermState.set_team_name,
                                    placeholder="class-2025-spring",
                                    width="100%",
                                ),
                                rx.text("仓库权限", size="1", color="gray"),
                                rx.select(
                                    ["write", "read", "triage"],
                                    value=RepoPermState.permission_level,
                                    on_change=RepoPermState.set_permission_level,
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            border="1px solid #e5e7eb",
                            border_radius="8px",
                            padding="14px",
                            flex="1",
                        ),
                        spacing="4",
                        width="100%",
                    ),

                    # ── 邀请状态看板 ──
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("邀请状态", weight="bold", size="3"),
                                rx.hstack(
                                    rx.text(
                                        "已接受: ", RepoPermState.accepted_count,
                                        color="green",
                                        font_size="xs",
                                    ),
                                    rx.text(
                                        "待接受: ", RepoPermState.pending_count,
                                        color="#ca8a04",
                                        font_size="xs",
                                    ),
                                    rx.text(
                                        "无法邀请: ", RepoPermState.left_count,
                                        color="red",
                                        font_size="xs",
                                    ),
                                    spacing="2",
                                ),
                                justify="between",
                                width="100%",
                            ),
                            # 成员表格
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("学号"),
                                        rx.table.column_header_cell("姓名"),
                                        rx.table.column_header_cell("GitHub 账号"),
                                        rx.table.column_header_cell("权限级别"),
                                        rx.table.column_header_cell("邀请状态"),
                                        rx.table.column_header_cell("操作"),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        RepoPermState.members,
                                        lambda m: rx.table.row(
                                            rx.table.cell(m["student_no"], font_family="monospace", font_size="xs"),
                                            rx.table.cell(m["full_name"], font_size="xs"),
                                            rx.cond(
                                                m["github_username"],
                                                rx.table.cell(m["github_username"], font_size="xs", color="#4b5563"),
                                                rx.table.cell("未绑定", font_size="xs", color="#ef4444"),
                                            ),
                                            rx.cond(
                                                m["is_bound"],
                                                rx.table.cell("Write", font_size="xs"),
                                                rx.table.cell("—", font_size="xs", color="gray"),
                                            ),
                                            rx.table.cell(rx.cond(
                                                m["invite_status"] == "accepted",
                                                rx.badge("已接受", color_scheme="green", variant="soft", size="1"),
                                                rx.cond(
                                                    m["invite_status"] == "pending",
                                                    rx.badge("待接受", color_scheme="yellow", variant="soft",
                                                             size="1"),
                                                    rx.badge("无法邀请", color_scheme="red", variant="soft", size="1"),
                                                ),
                                            )),
                                            rx.table.cell(rx.cond(
                                                m["is_bound"],
                                                rx.cond(
                                                    m["invite_status"] == "pending",
                                                    rx.button(
                                                        "重新发送",
                                                        size="1",
                                                        variant="ghost",
                                                        color_scheme="indigo",
                                                        on_click=lambda m=m: RepoPermState.handle_resend(
                                                            m["github_username"]),
                                                    ),
                                                    rx.text("—", color="gray", font_size="xs"),
                                                ),
                                                rx.link(
                                                    "去绑定 →",
                                                    href="/admin_students",
                                                    color_scheme="indigo",
                                                    font_size="xs",
                                                ),
                                            )),
                                            _hover={"bg": "#f9fafb"},
                                        ),
                                    ),
                                ),
                                variant="surface",
                                size="1",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        border="1px solid #e5e7eb",
                        border_radius="8px",
                        padding="14px",
                        width="100%",
                    ),

                    # ── 底部操作按钮 ──
                    rx.hstack(
                        rx.button(
                            "批量邀请全班加入 Org",
                            color_scheme="indigo",
                            on_click=RepoPermState.handle_invite_all,
                        ),
                        rx.button(
                            "学期结束：撤销全班权限",
                            variant="outline",
                            color_scheme="red",
                            on_click=RepoPermState.handle_revoke,
                        ),
                        spacing="3",
                    ),

                    # ── 状态消息 ──
                    rx.cond(
                        RepoPermState.status_message != "",
                        rx.callout(
                            RepoPermState.status_message,
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
            on_mount=RepoPermState.handle_load_members,
        )
