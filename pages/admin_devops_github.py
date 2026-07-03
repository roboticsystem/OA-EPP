"""GitHub 快捷链接 — 高级运营面板（F-D-008 / #41）

7 类标准 GitHub 快捷链接的现代管理看板：
- 仓库主页 / PR 列表 / Issues / Actions / 分支管理 / Secrets / 分支保护规则
- 基于已配置仓库 URL 自动生成，无需手动填写
- 支持自定义标签名称、排序、隐藏
"""

from __future__ import annotations

import reflex as rx
from states.admin_devops_github import GitHubQuickLinksState

# ═══════════════════════════════════════════════════════════════════════════
#  图标定义（Lucide SVG）
# ═══════════════════════════════════════════════════════════════════════════


def icon_github(**kwargs) -> rx.Component:
    return rx.icon("folder-git-2", **kwargs)


def icon_pr(**kwargs) -> rx.Component:
    return rx.icon("git-pull-request", **kwargs)


def icon_issue(**kwargs) -> rx.Component:
    return rx.icon("alert-circle", **kwargs)


def icon_actions(**kwargs) -> rx.Component:
    return rx.icon("play", **kwargs)


def icon_branch(**kwargs) -> rx.Component:
    return rx.icon("git-branch", **kwargs)


def icon_key(**kwargs) -> rx.Component:
    return rx.icon("key", **kwargs)


def icon_shield(**kwargs) -> rx.Component:
    return rx.icon("shield-check", **kwargs)


def icon_eye_off(**kwargs) -> rx.Component:
    return rx.icon("eye-off", **kwargs)


def icon_eye(**kwargs) -> rx.Component:
    return rx.icon("eye", **kwargs)


def icon_edit(**kwargs) -> rx.Component:
    return rx.icon("pencil", **kwargs)


def icon_chevron_up(**kwargs) -> rx.Component:
    return rx.icon("chevron-up", **kwargs)


def icon_chevron_down(**kwargs) -> rx.Component:
    return rx.icon("chevron-down", **kwargs)


def icon_rotate_ccw(**kwargs) -> rx.Component:
    return rx.icon("rotate-ccw", **kwargs)


def icon_external_link(**kwargs) -> rx.Component:
    return rx.icon("external-link", **kwargs)


def icon_copy(**kwargs) -> rx.Component:
    return rx.icon("copy", **kwargs)


def icon_check(**kwargs) -> rx.Component:
    return rx.icon("check", **kwargs)


def icon_x(**kwargs) -> rx.Component:
    return rx.icon("x", **kwargs)


def icon_save(**kwargs) -> rx.Component:
    return rx.icon("save", **kwargs)


def icon_chevron_right(**kwargs) -> rx.Component:
    return rx.icon("chevron-right", **kwargs)


def icon_link_2(**kwargs) -> rx.Component:
    return rx.icon("link-2", **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
#  图标 → Lucide 名称 映射
# ═══════════════════════════════════════════════════════════════════════════

_LINK_ICONS: dict[str, str] = {
    "repo":               "folder-git-2",
    "pulls":              "git-pull-request",
    "issues":             "alert-circle",
    "actions":            "play",
    "branches":           "git-branch",
    "secrets":            "key",
    "branch_protection":  "shield-check",
}

_LINK_GRADIENTS: dict[str, str] = {
    "repo":               "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "pulls":              "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "issues":             "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "actions":            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    "branches":           "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    "secrets":            "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
    "branch_protection":  "linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)",
}

_LINK_BADGE_COLORS: dict[str, str] = {
    "repo":               "#764ba2",
    "pulls":              "#f5576c",
    "issues":             "#00f2fe",
    "actions":            "#38f9d7",
    "branches":           "#fee140",
    "secrets":            "#fbc2eb",
    "branch_protection":  "#d57eeb",
}

_FEATURE_BADGES = [
    "🔗 URL 自动生成",
    "🏷️ 自定义标签",
    "↕️ 拖拽排序",
    "👁️ 显示/隐藏",
]


# ═══════════════════════════════════════════════════════════════════════════
#  子组件
# ═══════════════════════════════════════════════════════════════════════════


def _repo_header() -> rx.Component:
    """仓库信息头部 — 面包屑 + URL 复制。"""
    return rx.hstack(
        # 左侧图标
        rx.center(
            rx.icon("folder-git-2", size=28, color="white"),
            width="52px",
            height="52px",
            border_radius="14px",
            background="linear-gradient(135deg, #1e293b 0%, #334155 100%)",
            box_shadow="0 4px 14px rgba(30,41,59,0.25)",
            flex_shrink="0",
        ),
        # 仓库路径
        rx.vstack(
            rx.text(
                "GitHub 快捷链接",
                font_size="15px",
                font_weight="700",
                color=rx.color("slate", 12),
                letter_spacing="-0.01em",
            ),
            rx.hstack(
                rx.text(
                    GitHubQuickLinksState.repo_url,
                    font_size="12px",
                    color=rx.color("slate", 10),
                    font_family="monospace",
                    max_width="220px",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.tooltip(
                    rx.button(
                        icon_copy(size=13, color=rx.color("slate", 9)),
                        on_click=rx.set_clipboard(GitHubQuickLinksState.repo_url),
                        variant="ghost",
                        size="1",
                        cursor="pointer",
                    ),
                    content="复制仓库地址",
                ),
                spacing="1",
                align="center",
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        # 功能徽章
        rx.flex(
            rx.foreach(
                _FEATURE_BADGES,
                lambda b: rx.badge(
                    b,
                    variant="soft",
                    color_scheme="indigo",
                    size="1",
                    radius="full",
                ),
            ),
            spacing="1",
            wrap="wrap",
            justify="end",
            max_width="220px",
        ),
        align="center",
        spacing="3",
        width="100%",
    )


def _stats_bar() -> rx.Component:
    """统计条：总链接数 / 可见 / 隐藏。"""
    return rx.hstack(
        rx.hstack(
            rx.text("总链接", font_size="11px", color=rx.color("slate", 9)),
            rx.badge(
                GitHubQuickLinksState.links.length(),
                variant="solid",
                color_scheme="gray",
                size="1",
                radius="full",
            ),
            spacing="1",
        ),
        rx.separator(orientation="vertical", size="1", color_scheme="gray"),
        rx.hstack(
            rx.text("可见", font_size="11px", color=rx.color("slate", 9)),
            rx.badge(
                GitHubQuickLinksState.visible_links.length(),
                variant="solid",
                color_scheme="green",
                size="1",
                radius="full",
            ),
            spacing="1",
        ),
        rx.separator(orientation="vertical", size="1", color_scheme="gray"),
        rx.cond(
            GitHubQuickLinksState.hidden_count > 0,
            rx.hstack(
                rx.text("隐藏", font_size="11px", color=rx.color("slate", 9)),
                rx.badge(
                    GitHubQuickLinksState.hidden_count,
                    variant="soft",
                    color_scheme="orange",
                    size="1",
                    radius="full",
                ),
                spacing="1",
            ),
            rx.hstack(
                icon_eye(size=13, color=rx.color("slate", 9)),
                rx.text("全部可见", font_size="11px", color=rx.color("slate", 9)),
                spacing="1",
            ),
        ),
        rx.spacer(),
        rx.tooltip(
            rx.button(
                icon_rotate_ccw(size=14),
                rx.text("重置", font_size="11px"),
                on_click=GitHubQuickLinksState.reset_to_defaults,
                variant="ghost",
                size="1",
                color_scheme="gray",
                cursor="pointer",
                spacing="1",
            ),
            content="恢复全部默认设置",
        ),
        align="center",
        spacing="2",
        width="100%",
        padding="8px 12px",
        border_radius="10px",
        background=rx.color("slate", 2),
        border=f"1px solid {rx.color('slate', 4)}",
    )


def _link_card(link: dict, index: int, total: int) -> rx.Component:
    """单个快捷链接卡片。"""
    link_id: str = link["id"]
    icon_name: str = _LINK_ICONS.get(link_id, "link-2")
    gradient: str = _LINK_GRADIENTS.get(link_id, _LINK_GRADIENTS["repo"])
    badge_color: str = _LINK_BADGE_COLORS.get(link_id, "#764ba2")

    return rx.cond(
        GitHubQuickLinksState.edit_mode
        & (GitHubQuickLinksState.editing_link_id == link_id),

        # ──── 编辑模式 ───────────────────────────────────────────
        rx.box(
            rx.hstack(
                rx.input(
                    value=GitHubQuickLinksState.editing_label,
                    on_change=GitHubQuickLinksState.set_editing_label,
                    placeholder="自定义标签名称…",
                    width="100%",
                    variant="soft",
                    color_scheme="indigo",
                    size="1",
                ),
                rx.button(
                    icon_save(size=14),
                    on_click=GitHubQuickLinksState.save_label,
                    color_scheme="indigo",
                    variant="solid",
                    size="1",
                    cursor="pointer",
                ),
                rx.button(
                    icon_x(size=14),
                    on_click=GitHubQuickLinksState.cancel_edit,
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                    cursor="pointer",
                ),
                spacing="2",
            ),
            padding="10px 14px",
            border_radius="10px",
            background=rx.color("indigo", 1),
            border=f"2px solid {rx.color('indigo', 6)}",
            width="100%",
        ),

        # ──── 正常模式 ───────────────────────────────────────────
        rx.box(
            rx.hstack(
                # 左侧渐变图标
                rx.center(
                    rx.icon(icon_name, size=16, color="white"),
                    width="36px",
                    height="36px",
                    border_radius="10px",
                    background=gradient,
                    box_shadow="0 2px 8px rgba(0,0,0,0.12)",
                    flex_shrink="0",
                ),
                # 标签名
                rx.text(
                    link["label"],
                    font_size="13px",
                    font_weight="600",
                    color=rx.color("slate", 12),
                    flex="1",
                ),
                # 排序按钮
                rx.vstack(
                    rx.button(
                        icon_chevron_up(size=13),
                        on_click=lambda _e=None, lid=link_id: GitHubQuickLinksState.move_up(lid),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        cursor="pointer",
                        disabled=index == 0,
                    ),
                    rx.button(
                        icon_chevron_down(size=13),
                        on_click=lambda _e=None, lid=link_id: GitHubQuickLinksState.move_down(lid),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        cursor="pointer",
                        disabled=index == total - 1,
                    ),
                    spacing="0",
                ),
                # 编辑
                rx.tooltip(
                    rx.button(
                        icon_edit(size=13),
                        on_click=lambda _e=None, lid=link_id: GitHubQuickLinksState.start_edit_label(lid),
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                        cursor="pointer",
                    ),
                    content="自定义标签",
                ),
                # 隐藏
                rx.tooltip(
                    rx.button(
                        icon_eye_off(size=13),
                        on_click=lambda _e=None, lid=link_id: GitHubQuickLinksState.toggle_visibility(lid),
                        variant="ghost",
                        size="1",
                        color_scheme="orange",
                        cursor="pointer",
                    ),
                    content="隐藏此链接",
                ),
                # 跳转
                rx.tooltip(
                    rx.link(
                        rx.button(
                            icon_external_link(size=13),
                            variant="ghost",
                            size="1",
                            color_scheme="indigo",
                            cursor="pointer",
                        ),
                        href=link["url"],
                        is_external=True,
                    ),
                    content=f"打开 {link['url']}",
                ),
                align="center",
                spacing="2",
            ),
            # URL 底部文字
            rx.text(
                link["url"],
                font_size="10px",
                font_family="monospace",
                color=rx.color("slate", 8),
                padding_left="44px",
                margin_top="1px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            padding="10px 14px",
            border_radius="10px",
            background=rx.color("slate", 1),
            border=f"1px solid {rx.color('slate', 4)}",
            width="100%",
            _hover={
                "border_color": rx.color("indigo", 5),
                "background": rx.color("indigo", 1),
                "box_shadow": "0 2px 12px rgba(99,102,241,0.08)",
            },
            transition="all 0.15s ease",
            cursor="pointer",
        ),
    )


def _hidden_link_row(link: dict) -> rx.Component:
    """已隐藏链接 — 恢复行。"""
    link_id: str = link["id"]
    icon_name: str = _LINK_ICONS.get(link_id, "link-2")
    return rx.hstack(
        rx.icon(icon_name, size=13, color=rx.color("slate", 8)),
        rx.text(
            link["label"],
            font_size="12px",
            color=rx.color("slate", 9),
            text_decoration="line-through",
            flex="1",
        ),
        rx.text(
            link["url"],
            font_size="10px",
            font_family="monospace",
            color=rx.color("slate", 7),
            max_width="160px",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
            flex="1",
        ),
        rx.tooltip(
            rx.button(
                icon_eye(size=13),
                rx.text("恢复", font_size="11px"),
                on_click=lambda _e=None, lid=link_id: GitHubQuickLinksState.toggle_visibility(lid),
                variant="ghost",
                size="1",
                color_scheme="green",
                cursor="pointer",
                spacing="1",
            ),
            content="恢复显示",
        ),
        padding="6px 10px",
        border_radius="8px",
        width="100%",
        align="center",
        spacing="2",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  主面板
# ═══════════════════════════════════════════════════════════════════════════


def github_quick_links_card() -> rx.Component:
    """GitHub 快捷链接 — 高级运营看板。"""
    return rx.vstack(
        # ── 仓库头部 ─────────────────────────────────────────────
        _repo_header(),
        rx.separator(size="1", color_scheme="gray"),
        # ── 统计条 ───────────────────────────────────────────────
        _stats_bar(),
        # ── 可见链接列表 ─────────────────────────────────────────
        rx.vstack(
            rx.foreach(
                GitHubQuickLinksState.visible_links,
                lambda lnk, idx: _link_card(
                    lnk, idx,
                    GitHubQuickLinksState.visible_links.length(),
                ),
            ),
            spacing="2",
            width="100%",
        ),
        # ── 隐藏链接折叠区 ───────────────────────────────────────
        rx.cond(
            GitHubQuickLinksState.hidden_count > 0,
            rx.vstack(
                rx.separator(size="1", color_scheme="gray"),
                rx.hstack(
                    icon_eye_off(size=13, color=rx.color("orange", 9)),
                    rx.text(
                        f"已隐藏 · {GitHubQuickLinksState.hidden_count} 项",
                        font_size="11px",
                        color=rx.color("orange", 9),
                        font_weight="500",
                    ),
                    spacing="1",
                ),
                rx.vstack(
                    rx.foreach(
                        GitHubQuickLinksState.hidden_links,
                        lambda lnk: _hidden_link_row(lnk),
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
        ),
        # ── 底部提示 ─────────────────────────────────────────────
        rx.hstack(
            icon_link_2(size=12, color=rx.color("slate", 9)),
            rx.text(
                "基于已配置仓库 URL 自动生成 · 支持自定义标签与排序",
                font_size="10px",
                color=rx.color("slate", 9),
            ),
            justify="center",
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
        padding="22px",
        border_radius="16px",
        background=rx.color("slate", 1),
        border=f"1px solid {rx.color('slate', 4)}",
        box_shadow="0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03)",
        max_width="400px",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  全页布局（含页面标题、公告栏、步骤预览）
# ═══════════════════════════════════════════════════════════════════════════


def github_quicklinks_page() -> rx.Component:
    """完整页面：左侧内容区 + 右侧常驻快捷链接面板。"""

    return rx.fragment(
        # 加载数据
        rx.box(on_mount=GitHubQuickLinksState.load_links),
        # 全页容器
        rx.container(
            # ── 页面标题 ──────────────────────────────────────
            rx.vstack(
                rx.hstack(
                    rx.badge("F-D-008", variant="solid", color_scheme="indigo", radius="full", size="1"),
                    rx.badge("#41", variant="soft", color_scheme="indigo", radius="full", size="1"),
                    rx.text("开发运维 · GitHub 集成", font_size="12px", color=rx.color("slate", 10)),
                    spacing="2",
                ),
                rx.heading("GitHub 快捷链接", size="7", color=rx.color("slate", 12)),
                rx.text(
                    "基于已配置仓库 URL 自动生成的 7 类标准快捷链接，支持自定义标签、排序与显示控制",
                    font_size="14px",
                    color=rx.color("slate", 10),
                    max_width="520px",
                ),
                spacing="2",
            ),

            # ── 主内容区（左右布局） ──────────────────────────
            rx.grid(
                # 左栏：快速引导卡
                rx.vstack(
                    # 链接特征说明
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("info", size=16, color=rx.color("indigo", 9)),
                                rx.text("快速上手", font_size="14px", font_weight="600", color=rx.color("slate", 12)),
                                spacing="2",
                            ),
                            rx.text(
                                "以下 7 类链接基于仓库 URL 自动拼接生成，无需手动填写任何地址。"
                                "可以通过编辑按钮自定义标签名称，使用上下箭头调整顺序，"
                                "或隐藏暂时不需要的入口。",
                                font_size="13px",
                                color=rx.color("slate", 10),
                                line_height="1.7",
                            ),
                            spacing="3",
                        ),
                        padding="20px",
                    ),
                    # 功能速查
                    rx.card(
                        rx.vstack(
                            rx.text("链接清单", font_size="14px", font_weight="600", color=rx.color("slate", 12)),
                            rx.grid(
                                _feature_item("1", "仓库主页", "GitHub 仓库首页，包含 README 与文件树"),
                                _feature_item("2", "Pull Requests", "正在进行的代码审查与合并请求"),
                                _feature_item("3", "Issues", "Bug 报告、功能请求与任务跟踪"),
                                _feature_item("4", "Actions / CI", "GitHub Actions 持续集成/部署工作流"),
                                _feature_item("5", "分支管理", "查看、切换、删除与管理仓库分支"),
                                _feature_item("6", "Settings · Secrets", "CI/CD 环境变量与敏感信息管理"),
                                _feature_item("7", "Settings · 分支保护", "main 分支保护规则与合并策略"),
                                columns="1",
                                spacing="3",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        padding="20px",
                    ),
                    spacing="4",
                ),
                # 右栏：快捷链接面板
                github_quick_links_card(),
                columns="2",
                spacing="4",
                align_items="start",
                width="100%",
                margin_top="24px",
            ),

            spacing="4",
            padding="40px 32px",
            max_width="1100px",
            margin="0 auto",
        ),
    )


def _feature_item(num: str, title: str, desc: str) -> rx.Component:
    """功能速查列表项。"""
    return rx.hstack(
        rx.center(
            rx.text(num, font_size="11px", font_weight="700", color=rx.color("indigo", 11)),
            width="22px",
            height="22px",
            border_radius="6px",
            background=rx.color("indigo", 3),
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(title, font_size="12px", font_weight="600", color=rx.color("slate", 12)),
            rx.text(desc, font_size="11px", color=rx.color("slate", 10)),
            spacing="0",
        ),
        align="start",
        spacing="2",
    )
