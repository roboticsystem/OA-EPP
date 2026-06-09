"""F-D-009 Commit 消息格式自动校验 — Reflex 配置页面

提供 commitlint 配置向导界面：
- 规则集选择（Conventional Commits / 自定义）
- Type 枚举列表在线编辑
- Header / Subject 长度配置
- 启用/停用切换
- 配置文件预览与 GitHub 推送
- 状态总览与最近校验失败记录
"""

import reflex as rx
from oaepp.states.commitlint_state import CommitlintState


def _status_grid() -> rx.Component:
    """状态总览 4 格信息网格"""
    return rx.grid(
        rx.box(
            rx.text("启用状态", font_size="0.75rem", color="gray"),
            rx.text(
                rx.cond(
                    CommitlintState.is_enabled,
                    "已启用",
                    "已停用",
                ),
                font_size="1.1rem",
                font_weight="bold",
                color=rx.cond(
                    CommitlintState.is_enabled,
                    "#2e7d32",
                    "#999",
                ),
            ),
            padding="14px",
            border_radius="8px",
            background="#f8f9fa",
        ),
        rx.box(
            rx.text("规则版本", font_size="0.75rem", color="gray"),
            rx.text(
                rx.cond(
                    CommitlintState.config_version,
                    CommitlintState.config_version,
                    "1",
                ),
                font_size="1.1rem",
                font_weight="bold",
            ),
            padding="14px",
            border_radius="8px",
            background="#f8f9fa",
        ),
        rx.box(
            rx.text("规则类型", font_size="0.75rem", color="gray"),
            rx.text(
                rx.cond(
                    CommitlintState.rule_set == "custom",
                    "自定义",
                    "Conventional Commits",
                ),
                font_size="1.1rem",
                font_weight="bold",
            ),
            padding="14px",
            border_radius="8px",
            background="#f8f9fa",
        ),
        rx.box(
            rx.text("Type 数量", font_size="0.75rem", color="gray"),
            rx.text(
                rx.cond(
                    CommitlintState.type_enum.length() > 0,
                    CommitlintState.type_enum.length().to_string() + " 个",
                    "—",
                ),
                font_size="1.1rem",
                font_weight="bold",
            ),
            padding="14px",
            border_radius="8px",
            background="#f8f9fa",
        ),
        columns="4",
        spacing="3",
        width="100%",
    )


def _toggle_section() -> rx.Component:
    """启用/禁用开关 + 分支选择器"""
    return rx.hstack(
        # 启用开关
        rx.hstack(
            rx.switch(
                is_checked=CommitlintState.is_enabled,
                on_change=lambda v: CommitlintState.toggle_enabled(),
                color_scheme="blue",
            ),
            rx.text(
                rx.cond(
                    CommitlintState.is_enabled,
                    "已启用",
                    "已停用",
                ),
                font_size="0.9rem",
                color=rx.cond(
                    CommitlintState.is_enabled,
                    "#2e7d32",
                    "#999",
                ),
            ),
            spacing="2",
        ),
        # 分支选择
        rx.hstack(
            rx.text("目标分支：", font_size="0.82rem", color="gray"),
            rx.select(
                items=CommitlintState.branches.map(lambda b: b["name"]),
                value=CommitlintState.selected_branch,
                on_change=CommitlintState.set_branch,
                placeholder="选择分支",
                width="220px",
            ),
            spacing="1",
        ),
        justify="between",
        width="100%",
        margin_bottom="16px",
    )


def _config_form() -> rx.Component:
    """规则配置编辑表单"""
    return rx.box(
        rx.heading("规则配置", size="4", margin_bottom="12px"),
        rx.vstack(
            # 规则集
            rx.hstack(
                rx.text("规则集：", width="120px", font_weight="medium"),
                rx.select(
                    ["conventional", "custom"],
                    value=CommitlintState.rule_set,
                    on_change=CommitlintState.set_rule_set,
                    width="100%",
                ),
                width="100%",
            ),
            # 版本
            rx.hstack(
                rx.text("版本：", width="120px", font_weight="medium"),
                rx.text(
                    CommitlintState.config_version,
                    font_size="0.9rem",
                    color="gray",
                ),
                width="100%",
            ),
            # Type 枚举输入（简化版，实际用 tag 列表）
            rx.hstack(
                rx.text("Type 枚举：", width="120px", font_weight="medium"),
                rx.input(
                    placeholder="输入 type 后按 Enter",
                    on_key_down=CommitlintState.add_type,
                    width="100%",
                ),
                rx.button("+ 添加", size="sm"),
                width="100%",
            ),
            # Header 最大长度
            rx.hstack(
                rx.text("Header 最大长度：", width="120px", font_weight="medium"),
                rx.number_input(
                    value=CommitlintState.header_max_length,
                    on_change=CommitlintState.set_header_max_length,
                    min=1,
                    max=200,
                    width="100%",
                ),
                width="100%",
            ),
            # Subject 最小长度
            rx.hstack(
                rx.text("Subject 最小长度：", width="120px", font_weight="medium"),
                rx.number_input(
                    value=CommitlintState.subject_min_length,
                    on_change=CommitlintState.set_subject_min_length,
                    min=1,
                    max=50,
                    width="100%",
                ),
                width="100%",
            ),
            # 操作按钮
            rx.hstack(
                rx.button(
                    "💾 保存配置",
                    on_click=CommitlintState.save_config_to_db,
                    color_scheme="blue",
                ),
                rx.button(
                    "📤 保存并提交到仓库",
                    on_click=CommitlintState.save_and_push,
                    color_scheme="green",
                ),
                rx.button(
                    "⚡ 预览配置文件",
                    on_click=CommitlintState.generate_config_preview,
                    variant="outline",
                ),
                rx.button(
                    "⬆ 提交到仓库",
                    on_click=CommitlintState.push_config,
                    variant="outline",
                ),
                spacing="3",
                flex_wrap="wrap",
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
        padding="16px",
        border="1px solid #e0e0e0",
        border_radius="8px",
        margin_bottom="16px",
    )


def _preview_section() -> rx.Component:
    """配置文件预览区"""
    return rx.cond(
        CommitlintState.preview_workflow != "",
        rx.box(
            rx.heading("配置文件预览", size="4", margin_bottom="12px"),
            rx.grid(
                rx.box(
                    rx.text("📄 .github/workflows/commitlint.yml", font_size="0.8rem", color="gray"),
                    rx.code_block(
                        CommitlintState.preview_workflow,
                        language="yaml",
                        font_size="0.82rem",
                        border_radius="6px",
                        min_height="200px",
                    ),
                ),
                rx.box(
                    rx.text("📄 .commitlintrc.json", font_size="0.8rem", color="gray"),
                    rx.code_block(
                        CommitlintState.preview_commitlintrc,
                        language="json",
                        font_size="0.82rem",
                        border_radius="6px",
                        min_height="200px",
                    ),
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            padding="16px",
            border="1px solid #e0e0e0",
            border_radius="8px",
            margin_bottom="16px",
        ),
    )


def _repo_status_section() -> rx.Component:
    """仓库同步状态"""
    return rx.box(
        rx.hstack(
            rx.heading("📡 仓库同步状态", size="4"),
            rx.button(
                "🔄 刷新",
                on_click=CommitlintState.check_repo_status,
                size="sm",
                variant="outline",
            ),
            justify="between",
            width="100%",
        ),
        rx.cond(
            CommitlintState.repo_status,
            rx.vstack(
                rx.text(
                    f"仓库：{CommitlintState.repo_status.get('full_name', '—')}",
                    font_size="0.85rem",
                ),
                rx.hstack(
                    rx.text("commitlint.yml：", font_size="0.85rem"),
                    rx.text(
                        rx.cond(
                            CommitlintState.repo_status.get("workflow_in_repo"),
                            "✅ 已存在",
                            "⚠ 未提交",
                        ),
                        color=rx.cond(
                            CommitlintState.repo_status.get("workflow_in_repo"),
                            "#2e7d32",
                            "#e65100",
                        ),
                    ),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text(".commitlintrc.json：", font_size="0.85rem"),
                    rx.text(
                        rx.cond(
                            CommitlintState.repo_status.get("commitlintrc_in_repo"),
                            "✅ 已存在",
                            "⚠ 未提交",
                        ),
                        color=rx.cond(
                            CommitlintState.repo_status.get("commitlintrc_in_repo"),
                            "#2e7d32",
                            "#e65100",
                        ),
                    ),
                    spacing="2",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.text("点击「刷新」检查同步状态", font_size="0.85rem", color="gray"),
        ),
        padding="16px",
        border="1px solid #e0e0e0",
        border_radius="8px",
        margin_bottom="16px",
    )


def _failures_section() -> rx.Component:
    """最近校验失败记录"""
    return rx.box(
        rx.heading("最近校验失败记录", size="4", margin_bottom="12px"),
        rx.cond(
            CommitlintState.recent_failures.length() > 0,
            rx.foreach(
                CommitlintState.recent_failures,
                lambda f: rx.box(
                    rx.text(
                        f"{f.get('commit_msg', '')}",
                        font_weight="bold",
                        font_size="0.88rem",
                    ),
                    rx.text(
                        f"{f.get('commit_sha', '')[:7]} · {f.get('failed_at', '')}",
                        font_size="0.78rem",
                        color="gray",
                    ),
                    rx.text(
                        f.get("error_msg", ""),
                        font_size="0.8rem",
                        color="#c62828",
                    ),
                    padding="12px",
                    border_left="3px solid #c62828",
                    background="#fff5f5",
                    border_radius="4px",
                    margin_bottom="8px",
                ),
            ),
            rx.text("暂无校验失败记录", font_size="0.85rem", color="gray"),
        ),
        padding="16px",
        border="1px solid #e0e0e0",
        border_radius="8px",
    )


def commitlint_page() -> rx.Component:
    """Commitlint 配置主页"""
    return rx.center(
        rx.box(
            # 标题
            rx.hstack(
                rx.heading("✅ Commit 消息格式自动校验（F-D-009）", size="5"),
                rx.badge(
                    rx.cond(
                        CommitlintState.is_enabled,
                        "已启用",
                        "已停用",
                    ),
                    color_scheme=rx.cond(
                        CommitlintState.is_enabled,
                        "green",
                        "gray",
                    ),
                ),
                justify="between",
                width="100%",
                margin_bottom="16px",
            ),
            # Toast 提示
            rx.cond(
                CommitlintState.toast_message != "",
                rx.callout(
                    CommitlintState.toast_message,
                    icon=rx.cond(
                        CommitlintState.toast_type == "error",
                        "triangle_alert",
                        "info",
                    ),
                    color_scheme=rx.cond(
                        CommitlintState.toast_type == "error",
                        "red",
                        rx.cond(
                            CommitlintState.toast_type == "success",
                            "green",
                            "blue",
                        ),
                    ),
                    margin_bottom="12px",
                ),
            ),
            # 状态总览
            _status_grid(),
            rx.divider(margin="16px 0"),
            # 开关 + 分支
            _toggle_section(),
            # 配置表单
            _config_form(),
            # 预览区
            _preview_section(),
            # 仓库状态
            _repo_status_section(),
            # 失败记录
            _failures_section(),
            # 说明
            rx.callout(
                "启用时不合规 commit 将导致 CI 失败并阻止 PR 合并；停用时规则级别为 0（仅记录不阻断）。",
                icon="info",
                margin_top="16px",
            ),
            max_width="900px",
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
        on_mount=rx.sequence(
            CommitlintState.load_config,
            CommitlintState.load_branches,
            CommitlintState.check_repo_status,
        ),
    )
