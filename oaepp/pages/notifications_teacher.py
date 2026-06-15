"""F-S-012 公告与通知 — 教师端页面

路由: /notifications/teacher（由 app.py 自动发现注册）
页面函数: notifications_teacher_page()
状态类: 使用 states.notice.NoticeState

截图匹配要素：
- 标题"📢 公告与通知管理"
- 发送新通知区域：标题输入框 + 分类下拉 + 发送按钮（同行）
- 提示"通知将发送给所有已注册的学生"
- 已发送的通知列表（分类筛选 + 展开/折叠）
- 列表项：分类标签 + "共 X 人 · 已读 X 人 · 时间"
- 展开后显示内容和"修改重发""删除"按钮
"""

import reflex as rx

from oaepp.components.layout import page_layout
from oaepp.components.common import empty_state, loading_spinner

try:
    from oaepp.states.notice import NoticeState
except ModuleNotFoundError:
    from states.notice import NoticeState


# ── 分类配置 ──
CATEGORY_MAP = {
    "announcement": ("公告", "blue"),
    "deadline": ("截止提醒", "orange"),
    "grade": ("成绩通知", "green"),
}

CATEGORY_OPTIONS = [
    ("announcement", "公告"),
    ("deadline", "截止提醒"),
    ("grade", "成绩通知"),
]

CATEGORY_TABS = [
    ("all", "全部", "inbox"),
    ("announcement", "公告", "megaphone"),
    ("deadline", "截止提醒", "clock"),
    ("grade", "成绩通知", "graduation-cap"),
]


def category_badge(cat: str) -> rx.Component:
    """分类标签徽章"""
    label, color = CATEGORY_MAP.get(cat, ("通知", "gray"))
    return rx.badge(label, color_scheme=color, size="1", variant="soft")


def tab_button(tab: str, label: str, icon_name: str) -> rx.Component:
    """分类筛选按钮"""
    is_active = NoticeState.current_tab == tab
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14),
            rx.text(label),
            spacing="1",
        ),
        size="2",
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        on_click=NoticeState.switch_tab_teacher(tab),
    )


def create_form() -> rx.Component:
    """发送新通知表单 — 直接显示，无折叠"""
    return rx.vstack(
        rx.hstack(
            rx.icon("send", size=18, color="blue.500"),
            rx.heading("发送新通知", size="4"),
            spacing="2", align="center",
        ),
        # 标题 + 分类 + 发送按钮 同行
        rx.hstack(
            rx.vstack(
                rx.text("标题 *", font_size="sm", color="gray.600"),
                rx.input(
                    placeholder="如：期末考试成绩已公布",
                    value=NoticeState.create_title,
                    on_change=NoticeState.set_create_title,
                    width="100%",
                ),
                spacing="1", align="start", width="60%",
            ),
            rx.vstack(
                rx.text("分类", font_size="sm", color="gray.600"),
                rx.select.root(
                    rx.select.trigger(placeholder="选择分类"),
                    rx.select.content(
                        rx.select.group(
                            *[rx.select.item(label, value=v) for v, label in CATEGORY_OPTIONS]
                        ),
                    ),
                    value=NoticeState.create_category,
                    on_change=NoticeState.set_create_category,
                    width="100%",
                ),
                spacing="1", align="start", width="25%",
            ),
            rx.vstack(
                rx.text("", font_size="sm"),  # 占位对齐
                rx.button(
                    rx.icon("send", size=14), "发送通知",
                    color_scheme="blue",
                    variant="solid",
                    on_click=NoticeState.create_notification,
                    loading=NoticeState.creating,
                    width="100%",
                ),
                spacing="1", align="start", width="15%",
            ),
            width="100%", spacing="2", align="end",
        ),
        rx.vstack(
            rx.text("通知内容 *", font_size="sm", color="gray.600"),
            rx.text_area(
                placeholder="输入通知正文…",
                value=NoticeState.create_content,
                on_change=NoticeState.set_create_content,
                width="100%",
                rows="3",
            ),
            spacing="1", align="start", width="100%",
        ),
        rx.text(
            "通知将发送给所有已注册的学生",
            font_size="xs", color="gray.400",
        ),
        rx.cond(
            NoticeState.create_error,
            rx.text(NoticeState.create_error, color="red.500", font_size="sm"),
            rx.fragment(),
        ),
        width="100%",
        padding="16px",
        border="1px solid var(--gray-200)",
        border_radius="8px",
        spacing="3",
    )


def edit_form() -> rx.Component:
    """编辑通知表单"""
    return rx.vstack(
        rx.heading("修改通知", size="4"),
        rx.hstack(
            rx.input(
                placeholder="通知标题",
                value=NoticeState.edit_title,
                on_change=NoticeState.set_edit_title,
                width="60%",
            ),
            rx.select.root(
                rx.select.trigger(placeholder="选择分类"),
                rx.select.content(
                    rx.select.group(
                        *[rx.select.item(label, value=v) for v, label in CATEGORY_OPTIONS]
                    ),
                ),
                value=NoticeState.edit_category,
                on_change=NoticeState.set_edit_category,
                width="25%",
            ),
            width="100%", spacing="2",
        ),
        rx.text_area(
            placeholder="通知内容",
            value=NoticeState.edit_content,
            on_change=NoticeState.set_edit_content,
            width="100%",
            rows="3",
        ),
        rx.hstack(
            rx.button(
                "保存修改", color_scheme="blue",
                on_click=NoticeState.update_notification,
                loading=NoticeState.editing,
            ),
            rx.button(
                "取消", variant="outline",
                on_click=NoticeState.cancel_edit,
            ),
            spacing="2",
        ),
        rx.cond(
            NoticeState.edit_error,
            rx.text(NoticeState.edit_error, color="red.500", font_size="sm"),
            rx.fragment(),
        ),
        width="100%",
        padding="16px",
        border="1px solid var(--gray-200)",
        border_radius="8px",
        spacing="3",
    )


def sent_notification_row(n: dict) -> rx.Component:
    """已发送通知行 — 可展开/折叠，匹配截图布局"""
    cat = n.get("category", "announcement")
    nid = n.get("id", 0)
    total_students = n.get("total_students", 0)
    read_count = n.get("read_count", 0)
    title = n.get("title", "")
    content = n.get("content", "")
    created_at = n.get("created_at", "")

    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.trigger(
                rx.vstack(
                    # 第一行：标题（粗体）
                    rx.text(
                        title,
                        font_weight="bold", font_size="md", color="gray.800",
                    ),
                    # 第二行：分类标签 + 统计信息 + 时间
                    rx.hstack(
                        category_badge(cat),
                        rx.text(
                            "· 共 ", total_students,
                            " 人 · 已读 ", read_count,
                            " 人 · ", created_at,
                            font_size="xs", color="gray.400",
                        ),
                        spacing="2", align="center",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                padding="12px 16px",
                _hover={"bg": "var(--gray-50)"},
            ),
            rx.accordion.content(
                rx.vstack(
                    rx.text(content, font_size="sm", color="gray.600"),
                    rx.hstack(
                        rx.button(
                            rx.icon("pencil", size=14), "修改重发",
                            size="1", color_scheme="blue", variant="solid",
                            on_click=NoticeState.start_edit(nid),
                        ),
                        rx.button(
                            rx.icon("trash-2", size=14), "删除",
                            size="1", color_scheme="red", variant="outline",
                            on_click=NoticeState.confirm_delete(n),
                        ),
                        spacing="2",
                    ),
                    spacing="2", align="start",
                    padding="8px 16px 16px",
                ),
            ),
            value=f"notif_{nid}",
        ),
        width="100%",
        collapsible=True,
    )


def delete_dialog() -> rx.Component:
    """删除确认弹窗"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("确认删除"),
            rx.alert_dialog.description(
                rx.text("确定要删除通知「", NoticeState.delete_title, "」吗？")
            ),
            rx.hstack(
                rx.button(
                    "取消", variant="outline",
                    on_click=NoticeState.cancel_delete,
                ),
                rx.button(
                    "删除", color_scheme="red",
                    on_click=NoticeState.delete_notification,
                    loading=NoticeState.deleting,
                ),
                spacing="2", justify="end", width="100%",
            ),
        ),
        open=NoticeState.show_delete_dialog,
    )


def pagination_controls() -> rx.Component:
    """分页控制"""
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page_teacher(NoticeState.current_page - 1),
            is_disabled=~NoticeState.can_go_prev,
        ),
        rx.text(
            NoticeState.current_page,
            " / ",
            NoticeState.total_pages,
            font_size="sm", color="gray.500",
        ),
        rx.button(
            rx.icon("chevron-right", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page_teacher(NoticeState.current_page + 1),
            is_disabled=~NoticeState.can_go_next,
        ),
        width="100%", justify="center", spacing="4",
    )


def notifications_teacher_page() -> rx.Component:
    """教师端 — 公告与通知管理页面（由 app.py 自动发现注册为 /notifications/teacher）"""
    content = rx.vstack(
        # 创建/编辑表单切换（直接显示发送表单，无折叠按钮）
        rx.cond(
            NoticeState.is_editing,
            edit_form(),
            create_form(),
        ),

        # 分类筛选
        rx.hstack(
            rx.heading("已发送的通知", size="4"),
            rx.icon("inbox", size=18, color="gray.400"),
            rx.spacer(),
            *[tab_button(t, l, i) for t, l, i in CATEGORY_TABS],
            width="100%", align="center", spacing="2", wrap="wrap",
        ),

        # 内容区域
        rx.cond(
            NoticeState.loading,
            loading_spinner("加载通知中..."),
            rx.cond(
                NoticeState.error,
                rx.vstack(
                    rx.icon("alert-circle", size=32, color="red.500"),
                    rx.text(NoticeState.error, color="red.500"),
                    rx.button("重试", on_click=NoticeState.refresh),
                    spacing="2", align="center", padding="40px",
                ),
                rx.cond(
                    NoticeState.has_data,
                    rx.vstack(
                        rx.foreach(NoticeState.notices, sent_notification_row),
                        rx.cond(
                            NoticeState.show_pagination,
                            pagination_controls(),
                            rx.fragment(),
                        ),
                        width="100%", spacing="0",
                    ),
                    empty_state("暂无已发送的通知", icon="inbox"),
                ),
            ),
        ),

        # 删除确认弹窗
        delete_dialog(),

        # Toast 提示
        rx.toast.provider(),

        width="100%",
        max_width="900px",
        margin="0 auto",
        spacing="4",
        on_mount=NoticeState.load_teacher_notices,
    )

    return page_layout(title="公告与通知管理", content=content)
