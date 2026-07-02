"""F-T-006 需求文档编辑器页面（教师端）

对应原型：教师端需求文档编辑工具
路由：/req-editor（由 app.py 自动发现机制注册）
对应 State：oaepp.states.req_editor.ReqEditorState

功能：
- 左右分栏：Markdown 编辑器 + 实时 HTML 预览
- 工具栏：加载模板 / 导入 .md / 格式校验 / 保存 / 封存
- Copilot 辅助：一键插入验收标准、安全属性等片段
- 审阅评论：学生可添加评论，教师确认后封存
"""

import reflex as rx

try:
    from states.req_editor import ReqEditorState
except ImportError:
    from oaepp.states.req_editor import ReqEditorState

# ── 页面色彩常量 ─────────────────────────────────────────────────────────
_TOOLBAR_BG = "#f8fafc"
_BORDER_COLOR = "var(--gray-5)"
_SEALED_BG = "#fef2f2"
_SEALED_BORDER = "#fecaca"


# ═══════════════════════════════════════════════════════════════════════════
#  工具栏
# ═══════════════════════════════════════════════════════════════════════════

def _toolbar() -> rx.Component:
    """顶部工具栏：模板、导入、校验、保存、封存"""
    return rx.box(
        rx.hstack(
            # 左侧操作按钮
            rx.hstack(
                rx.button(
                    rx.icon("file_text", size=16),
                    "加载模板",
                    on_click=ReqEditorState.load_template,
                    color_scheme="blue",
                    variant="soft",
                    size="2",
                    disabled=ReqEditorState.is_sealed,
                ),
                rx.upload(
                    rx.button(
                        rx.icon("upload", size=16),
                        "导入 .md",
                        color_scheme="indigo",
                        variant="soft",
                        size="2",
                        disabled=ReqEditorState.is_sealed,
                    ),
                    id="md_upload",
                    accept={".md": ".md", ".txt": ".txt"},
                    max_files=1,
                    on_drop=ReqEditorState.handle_upload(
                        rx.upload_files("md_upload")
                    ),
                ),
                rx.button(
                    rx.icon("check_circle", size=16),
                    "校验格式",
                    on_click=ReqEditorState.validate_format,
                    color_scheme="amber",
                    variant="soft",
                    size="2",
                ),
                rx.divider(orientation="vertical", height="24px"),
                rx.button(
                    rx.icon("save", size=16),
                    "保存文档",
                    on_click=ReqEditorState.save_and_commit,
                    color_scheme="green",
                    variant="solid",
                    size="2",
                    disabled=ReqEditorState.is_sealed,
                ),
                rx.button(
                    rx.icon("lock", size=16),
                    rx.cond(ReqEditorState.is_sealed, "已封存", "封存文档"),
                    on_click=ReqEditorState.seal_document,
                    color_scheme="red",
                    variant="solid",
                    size="2",
                    disabled=ReqEditorState.is_sealed,
                ),
                spacing="2",
                align="center",
            ),
            # 右侧 Copilot 切换
            rx.button(
                rx.icon("bot", size=16),
                "Copilot",
                on_click=ReqEditorState.toggle_copilot,
                color_scheme="purple",
                variant="ghost",
                size="2",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        padding="12px 16px",
        background=_TOOLBAR_BG,
        border_bottom=f"1px solid {_BORDER_COLOR}",
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Copilot 建议面板
# ═══════════════════════════════════════════════════════════════════════════

def _copilot_panel() -> rx.Component:
    """Copilot 片段插入面板"""
    return rx.cond(
        ReqEditorState.show_copilot_panel,
        rx.box(
            rx.vstack(
                rx.text("Copilot 辅助 — 插入片段", weight="bold", size="2"),
                rx.text(
                    "点击下方按钮将对应片段插入到文档末尾",
                    color="gray",
                    size="1",
                ),
                rx.divider(),
                rx.grid(
                    rx.button(
                        "验收标准",
                        on_click=lambda: ReqEditorState.insert_snippet("验收标准"),
                        size="1",
                        color_scheme="green",
                        variant="soft",
                        width="100%",
                    ),
                    rx.button(
                        "安全属性",
                        on_click=lambda: ReqEditorState.insert_snippet("安全属性"),
                        size="1",
                        color_scheme="red",
                        variant="soft",
                        width="100%",
                    ),
                    rx.button(
                        "技术约束",
                        on_click=lambda: ReqEditorState.insert_snippet("技术约束"),
                        size="1",
                        color_scheme="blue",
                        variant="soft",
                        width="100%",
                    ),
                    rx.button(
                        "测试要点",
                        on_click=lambda: ReqEditorState.insert_snippet("测试要点"),
                        size="1",
                        color_scheme="amber",
                        variant="soft",
                        width="100%",
                    ),
                    columns="2",
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="14px 16px",
            border=f"1px solid {_BORDER_COLOR}",
            border_radius="8px",
            background="white",
            width="100%",
        ),
        rx.box(),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  文档元信息输入
# ═══════════════════════════════════════════════════════════════════════════

def _meta_inputs() -> rx.Component:
    """文档标题和课程 ID 输入"""
    return rx.hstack(
        rx.input(
            placeholder="文档标题",
            value=ReqEditorState.document_title,
            on_change=ReqEditorState.set_document_title,
            width="260px",
            disabled=ReqEditorState.is_sealed,
        ),
        rx.input(
            placeholder="关联课程 ID（可选）",
            value=ReqEditorState.course_id.to(str),
            on_change=ReqEditorState.set_course_id,
            width="160px",
            disabled=ReqEditorState.is_sealed,
        ),
        rx.text("", color="gray", size="1"),
        spacing="3",
        align="center",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  消息提示条
# ═══════════════════════════════════════════════════════════════════════════

def _message_bar() -> rx.Component:
    """保存/操作反馈消息"""
    return rx.cond(
        ReqEditorState.save_message != "",
        rx.box(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(
                        ReqEditorState.has_validation_errors,
                        "circle_alert",
                        "circle_check",
                    ),
                    size=14,
                ),
                rx.text(ReqEditorState.save_message, size="1"),
                spacing="2",
                align="center",
            ),
            padding="6px 12px",
            background=rx.cond(
                ReqEditorState.has_validation_errors,
                "#fef2f2",
                "#f0fdf4",
            ),
            border_radius="6px",
            width="100%",
        ),
        rx.box(),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  格式校验错误列表
# ═══════════════════════════════════════════════════════════════════════════

def _validation_errors_display() -> rx.Component:
    """格式校验错误展示"""
    return rx.cond(
        ReqEditorState.validation_errors.length() > 0,
        rx.box(
            rx.vstack(
                rx.text("格式校验未通过:", weight="bold", size="2", color="#dc2626"),
                rx.foreach(
                    ReqEditorState.validation_errors,
                    lambda err: rx.hstack(
                        rx.icon("x", size=12, color="#dc2626"),
                        rx.text(err, size="1", color="#dc2626"),
                        spacing="2",
                        align="center",
                    ),
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            padding="10px 14px",
            background="#fef2f2",
            border="1px solid #fecaca",
            border_radius="8px",
            width="100%",
        ),
        rx.box(),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  封存状态横幅
# ═══════════════════════════════════════════════════════════════════════════

def _sealed_banner() -> rx.Component:
    """文档已封存时的提示横幅"""
    return rx.cond(
        ReqEditorState.is_sealed,
        rx.box(
            rx.hstack(
                rx.icon("lock", size=16, color="#b91c1c"),
                rx.text(
                    "此文档已封存，所有编辑操作已锁定。如需修改，请联系教师解锁。",
                    size="2",
                    color="#b91c1c",
                    weight="medium",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            padding="10px 16px",
            background=_SEALED_BG,
            border=f"1px solid {_SEALED_BORDER}",
            border_radius="8px",
            width="100%",
        ),
        rx.box(),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Markdown 编辑器（左侧面板）
# ═══════════════════════════════════════════════════════════════════════════

def _editor_panel() -> rx.Component:
    """左侧：Markdown 编辑区"""
    return rx.box(
        rx.vstack(
            rx.text("Markdown 编辑器", weight="bold", size="2", color="gray"),
            rx.text_area(
                value=ReqEditorState.content,
                on_change=ReqEditorState.update_content,
                placeholder="在此编写功能需求文档，或点击「加载模板」开始...",
                width="100%",
                height="calc(100vh - 340px)",
                min_height="400px",
                background="white",
                font_family="'Cascadia Code', 'Fira Code', 'Consolas', monospace",
                font_size="13px",
                line_height="1.7",
                disabled=ReqEditorState.is_sealed,
            ),
            width="100%",
            spacing="2",
            align="stretch",
        ),
        width="50%",
        padding="16px",
        border_right=f"1px solid {_BORDER_COLOR}",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  实时预览面板（右侧面板）
# ═══════════════════════════════════════════════════════════════════════════

def _preview_panel() -> rx.Component:
    """右侧：实时 HTML 预览"""
    return rx.box(
        rx.vstack(
            rx.text("实时预览", weight="bold", size="2", color="gray"),
            rx.box(
                rx.html(ReqEditorState.preview_html),
                width="100%",
                height="calc(100vh - 340px)",
                min_height="400px",
                overflow="auto",
                padding="16px",
                background="white",
                border=f"1px solid {_BORDER_COLOR}",
                border_radius="6px",
            ),
            width="100%",
            spacing="2",
            align="stretch",
        ),
        width="50%",
        padding="16px",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  审阅评论面板
# ═══════════════════════════════════════════════════════════════════════════

def _comment_item(comment: dict):
    """单条评论"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("message_circle", size=14, color="gray"),
                rx.text(comment["time"], size="1", color="gray"),
                spacing="2",
                align="center",
            ),
            rx.text(comment["content"], size="2"),
            spacing="1",
            align="start",
            width="100%",
        ),
        padding="10px 14px",
        background="white",
        border=f"1px solid {_BORDER_COLOR}",
        border_radius="8px",
        width="100%",
    )


def _comment_section() -> rx.Component:
    """审阅评论区域"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("messages_square", size=16),
                rx.text("审阅评论", weight="bold", size="2"),
                rx.text(f"({ReqEditorState.comment_count} 条)", size="1", color="gray"),
                rx.box(flex="1"),
                rx.button(
                    "清空",
                    on_click=ReqEditorState.clear_comments,
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            # 已有评论列表
            rx.foreach(ReqEditorState.comments, _comment_item),
            # 输入新评论
            rx.hstack(
                rx.input(
                    placeholder="输入审阅意见...",
                    value=ReqEditorState.new_comment,
                    on_change=ReqEditorState.set_new_comment,
                    width="100%",
                ),
                rx.button(
                    rx.icon("send", size=14),
                    "发表",
                    on_click=ReqEditorState.add_comment,
                    color_scheme="blue",
                    size="2",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        padding="16px",
        background="#fafbfc",
        border_top=f"1px solid {_BORDER_COLOR}",
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  主页面入口
# ═══════════════════════════════════════════════════════════════════════════

def req_editor_page():
    """需求文档编辑器页面 (F-T-006)

    页面结构：
    - 顶部工具栏（模板/导入/校验/保存/封存 + Copilot 切换）
    - Copilot 建议面板（可折叠）
    - 元信息输入行（标题、课程 ID）
    - 消息提示条 + 格式校验错误 + 封存横幅
    - 左右分栏：编辑器 | 实时预览
    - 底部审阅评论区域
    """
    return rx.center(
        rx.box(
            rx.vstack(
                # 页面标题
                rx.hstack(
                    rx.heading("需求文档编辑器", size="5"),
                    rx.text("F-T-006", size="1", color="gray"),
                    rx.box(flex="1"),
                    _meta_inputs(),
                    spacing="4",
                    align="center",
                    width="100%",
                    padding="16px 20px",
                    background="white",
                    border_bottom=f"1px solid {_BORDER_COLOR}",
                ),
                # 工具栏
                _toolbar(),
                # Copilot 面板
                rx.box(
                    _copilot_panel(),
                    padding="0 20px",
                    width="100%",
                ),
                # 消息 / 错误 / 封存横幅
                rx.box(
                    rx.vstack(
                        _message_bar(),
                        _validation_errors_display(),
                        _sealed_banner(),
                        spacing="2",
                        width="100%",
                    ),
                    padding="8px 20px",
                    width="100%",
                ),
                # 左右分栏：编辑器 + 预览
                rx.hstack(
                    _editor_panel(),
                    _preview_panel(),
                    spacing="0",
                    align="start",
                    width="100%",
                    background="white",
                ),
                # 审阅评论
                _comment_section(),
                spacing="0",
                width="100%",
                align="stretch",
            ),
            max_width="1440px",
            width="100%",
            border_radius="12px",
            overflow="hidden",
            box_shadow="0 4px 24px rgba(0,0,0,0.06)",
            background="white",
        ),
        min_height="100vh",
        width="100%",
        background="linear-gradient(180deg, #f1f5f9 0%, #ffffff 100%)",
        padding="16px",
    )
