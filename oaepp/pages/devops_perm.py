"""
F-D-005 仓库协作者权限管理 — devops_perm_page

通过 GitHub Team 统一管理课程组成员权限，禁止个人直接授权，确保权限管理规范化。

验收标准：
- 通过 GitHub Team 而非个人直接授权管理权限
- 角色分配符合 Admin/Write/Triage/Read 规范
- 权限变更有操作记录
"""

try:
    import reflex as rx
except Exception:
    rx = None

devops_perm_page = None

if rx is not None:
    try:
        from states.devops_perm import CollabPermState
    except ImportError:
        from oaepp.states.devops_perm import CollabPermState

    def _role_badge(role):
        return rx.cond(
            role == "admin",
            rx.badge("管理员", color_scheme="red", variant="soft", size="1"),
            rx.cond(
                role == "write",
                rx.badge("写入权限", color_scheme="green", variant="soft", size="1"),
                rx.cond(
                    role == "triage",
                    rx.badge("审核权限", color_scheme="yellow", variant="soft", size="1"),
                    rx.cond(
                        role == "read",
                        rx.badge("只读权限", color_scheme="blue", variant="soft", size="1"),
                        rx.badge("未知", color_scheme="gray", variant="soft", size="1"),
                    ),
                ),
            ),
        )

    def _status_badge(member):
        return rx.cond(
            member["in_team"],
            rx.cond(
                member["current_team"],
                rx.badge(f"已加入: {member['current_team']}", color_scheme="green", variant="soft", size="1"),
                rx.badge("已加入 Team", color_scheme="green", variant="soft", size="1"),
            ),
            rx.badge("未加入 Team", color_scheme="red", variant="soft", size="1"),
        )

    def _member_row(member):
        return rx.table.row(
            rx.table.cell(member["student_no"], font_family="monospace", font_size="xs"),
            rx.table.cell(member["full_name"], font_size="xs"),
            rx.table.cell(
                rx.cond(
                    member["github_username"],
                    rx.text(member["github_username"], font_size="xs", color="#4b5563"),
                    rx.text("未绑定", font_size="xs", color="#ef4444"),
                )
            ),
            rx.table.cell(_role_badge(member["role"])),
            rx.table.cell(_status_badge(member)),
            rx.table.cell(
                rx.vstack(
                    rx.select(
                        CollabPermState.ROLE_CHOICES,
                        value=member["role"],
                        on_change=lambda val, uid=member["user_id"]: CollabPermState.handle_assign_role(uid, val),
                        size="1",
                        width="100%",
                    ),
                    rx.cond(
                        ~member["in_team"],
                        rx.button(
                            "加入 Team",
                            size="1",
                            variant="outline",
                            color_scheme="green",
                            disabled=~member["github_username"],
                            on_click=lambda e, uid=member["user_id"]: CollabPermState.handle_add_to_team(uid),
                            width="100%",
                        ),
                        rx.button(
                            "移除",
                            size="1",
                            variant="outline",
                            color_scheme="red",
                            on_click=lambda e, uid=member["user_id"]: CollabPermState.handle_remove_member(uid),
                            width="100%",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                )
            ),
            _hover={"bg": "#f9fafb"},
        )

    def _stat_card(label, count, color):
        return rx.card(
            rx.vstack(
                rx.text(label, size="1", color="#6b7280"),
                rx.heading(rx.cond(count > 0, count.to_string(), "0"), size="4", color=color),
                spacing="0",
                align="center",
            ),
            padding="16px",
            width="100%",
        )

    def devops_perm_page():
        return rx.box(
            rx.center(
                rx.vstack(
                    rx.vstack(
                        rx.heading("仓库协作者权限管理", size="7"),
                        rx.text(
                            "通过 GitHub Team 统一管理成员权限，禁止个人直接授权",
                            size="2",
                            color="#6b7280",
                        ),
                        spacing="0",
                        width="100%",
                        align="center",
                    ),

                rx.card(
                    rx.vstack(
                        rx.text("配置区域", size="3", weight="bold"),
                        rx.flex(
                            rx.box(
                                rx.vstack(
                                    rx.text("GitHub Organization", size="1", color="#6b7280"),
                                    rx.input(
                                        value=CollabPermState.org_name,
                                        on_change=CollabPermState.set_org_name,
                                        placeholder="oa-epp-2025",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),
                                border="1px solid #e2e8f0",
                                border_radius="8px",
                                padding="14px",
                                flex="1",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("课程仓库名", size="1", color="#6b7280"),
                                    rx.input(
                                        value=CollabPermState.repo_name,
                                        on_change=CollabPermState.set_repo_name,
                                        placeholder="oa-epp-platform",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),
                                border="1px solid #e2e8f0",
                                border_radius="8px",
                                padding="14px",
                                flex="1",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "创建标准 Team（Admin/Write/Triage/Read）",
                                color_scheme="indigo",
                                on_click=CollabPermState.handle_create_teams,
                                loading=CollabPermState.is_loading,
                            ),
                            rx.button(
                                "配置仓库权限",
                                variant="outline",
                                color_scheme="indigo",
                                on_click=CollabPermState.handle_configure_repo_permissions,
                                loading=CollabPermState.is_loading,
                            ),
                            rx.button(
                                "刷新成员状态",
                                variant="outline",
                                color_scheme="gray",
                                on_click=CollabPermState.handle_refresh_status,
                            ),
                            spacing="3",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.text("权限统计", size="3", weight="bold"),
                            rx.spacer(),
                            rx.text(f"总计: {CollabPermState.total_members}", size="1", color="#6b7280"),
                            width="100%",
                        ),
                        rx.grid(
                            _stat_card("管理员", CollabPermState.admin_count, "#ef4444"),
                            _stat_card("写入权限", CollabPermState.write_count, "#22c55e"),
                            _stat_card("审核权限", CollabPermState.triage_count, "#eab308"),
                            _stat_card("只读权限", CollabPermState.read_count, "#4f46e5"),
                            columns="4",
                            spacing="4",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.text("协作者列表", size="3", weight="bold"),
                            rx.spacer(),
                            rx.select(
                                ["all", "admin", "write", "triage", "read"],
                                value=CollabPermState.filter_role,
                                on_change=CollabPermState.set_filter_role,
                                size="1",
                            ),
                            width="100%",
                        ),
                        rx.cond(
                            CollabPermState.is_loading,
                            rx.center(
                                rx.spinner(size="3", color="#4f46e5"),
                                padding="48px",
                            ),
                            rx.cond(
                                CollabPermState.filtered_members.length() == 0,
                                rx.center(
                                    rx.vstack(
                                        rx.icon("users", size=40, color="#6b7280"),
                                        rx.text("暂无协作者数据", color="#6b7280", size="3"),
                                        spacing="3",
                                        padding="48px",
                                    ),
                                ),
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("学号"),
                                            rx.table.column_header_cell("姓名"),
                                            rx.table.column_header_cell("GitHub 账号"),
                                            rx.table.column_header_cell("权限角色"),
                                            rx.table.column_header_cell("Team 状态"),
                                            rx.table.column_header_cell("操作"),
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            CollabPermState.filtered_members,
                                            _member_row,
                                        ),
                                    ),
                                    variant="surface",
                                    size="1",
                                    width="100%",
                                ),
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.text("操作记录", size="3", weight="bold"),
                            rx.spacer(),
                            rx.button(
                                "刷新记录",
                                size="1",
                                variant="outline",
                                on_click=CollabPermState.load_audit_logs,
                            ),
                            width="100%",
                        ),
                        rx.cond(
                            CollabPermState.audit_logs.length() == 0,
                            rx.center(
                                rx.text("暂无操作记录", color="#6b7280", size="2"),
                                padding="24px",
                            ),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("操作"),
                                        rx.table.column_header_cell("详情"),
                                        rx.table.column_header_cell("时间"),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(
                                    CollabPermState.audit_logs,
                                    lambda log: rx.table.row(
                                        rx.table.cell(log["action"], font_size="xs"),
                                        rx.table.cell(
                                            rx.text(
                                                log["message"],
                                                font_size="xs",
                                                color="#6b7280",
                                            ),
                                        ),
                                        rx.table.cell(log["action_at"], font_size="xs"),
                                    ),
                                ),
                                ),
                                variant="surface",
                                size="1",
                                width="100%",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.cond(
                    CollabPermState.status_message != "",
                    rx.callout(
                        CollabPermState.status_message,
                        color_scheme="indigo",
                        width="100%",
                    ),
                ),

                    spacing="6",
                    width="100%",
                    max_width="1100px",
                    padding="32px",
                ),
                min_height="100vh",
                width="100%",
            ),
            background="#f8fafc",
            width="100%",
            on_mount=CollabPermState.handle_load_members,
        )
