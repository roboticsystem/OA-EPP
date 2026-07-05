"""F-S-012 公告与通知 — 教师端页面

路由: /notifications/teacher（由 app.py 自动发现注册）
页面函数: notifications_teacher_page()
状态类: TeacherNoticeState（内联定义于本文件，继承 rx.State）

截图匹配要素：
- 标题"📢 公告与通知管理"
- 发送新通知区域：标题输入框 + 分类下拉 + 发送按钮（同行）
- 提示"通知将发送给所有已注册的学生"
- 已发送的通知列表（分类筛选 + 展开/折叠）
- 列表项：分类标签 + "共 X 人 · 已读 X 人 · 时间"
- 展开后显示内容和"修改重发""删除"按钮
"""

import reflex as rx
from sqlmodel import select, func

try:
    from oaepp.components.layout import page_layout
except ImportError:
    from components.layout import page_layout

try:
    from oaepp.components.common import empty_state, loading_spinner
except ImportError:
    from components.common import empty_state, loading_spinner

try:
    from oaepp.models import Notification, User
except ImportError:
    from models import Notification, User


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


# ═══════════════════════════════════════════════════════════════
# TeacherNoticeState — 教师端公告通知状态（内联于页面文件）
# ═══════════════════════════════════════════════════════════════

class TeacherNoticeState(rx.State):
    """教师端公告通知状态 — 直接继承 rx.State"""

    # 列表
    notices: list[dict] = []
    current_tab: str = "all"
    current_page: int = 1
    page_size: int = 12
    total: int = 0
    total_pages: int = 1
    loading: bool = True
    error: str = ""

    # 创建表单
    create_title: str = ""
    create_content: str = ""
    create_category: str = "announcement"
    creating: bool = False
    create_error: str = ""

    # 编辑
    edit_id: int = 0
    edit_title: str = ""
    edit_content: str = ""
    edit_category: str = "announcement"
    editing: bool = False
    edit_error: str = ""

    # 删除确认
    delete_target: dict = {}
    deleting: bool = False
    delete_error: str = ""

    # ── 计算属性 ──

    @rx.var
    def has_data(self) -> bool:
        return len(self.notices) > 0

    @rx.var
    def show_pagination(self) -> bool:
        return self.total_pages > 1

    @rx.var
    def can_go_prev(self) -> bool:
        return self.current_page > 1

    @rx.var
    def can_go_next(self) -> bool:
        return self.current_page < self.total_pages

    @rx.var
    def is_editing(self) -> bool:
        return self.edit_id > 0

    @rx.var
    def show_delete_dialog(self) -> bool:
        return bool(self.delete_target)

    @rx.var
    def delete_title(self) -> str:
        return self.delete_target.get("title", "") if self.delete_target else ""

    # ── 列表加载（按 title+category 分组） ──

    def switch_tab(self, tab: str):
        if tab == self.current_tab:
            return
        self.current_tab = tab
        self.current_page = 1
        return self.load_notices()

    def go_page(self, page: int):
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return
        self.current_page = page
        return self.load_notices()

    def refresh(self):
        return self.load_notices()

    def load_notices(self):
        self.loading = True
        self.error = ""
        yield
        try:
            with rx.session() as session:
                stmt = (
                    select(
                        Notification.title,
                        Notification.category,
                        func.min(Notification.id).label("id"),
                        func.min(Notification.body).label("body"),
                        func.min(Notification.created_at).label("created_at"),
                        func.count().label("sent_count"),
                        func.sum(
                            func.case((Notification.is_read == True, 1), else_=0)  # noqa: E712
                        ).label("read_count"),
                    )
                )
                if self.current_tab != "all":
                    stmt = stmt.where(Notification.category == self.current_tab)
                stmt = stmt.group_by(Notification.title, Notification.category)
                stmt = stmt.order_by(func.max(Notification.created_at).desc())

                count_stmt = select(func.count()).select_from(stmt.subquery())
                self.total = session.exec(count_stmt).one()

                offset = (self.current_page - 1) * self.page_size
                rows = session.exec(stmt.offset(offset).limit(self.page_size)).all()

            self.notices = []
            for row in rows:
                created_at = str(row.created_at) if row.created_at else ""
                self.notices.append({
                    "id": row.id,
                    "title": row.title,
                    "category": row.category,
                    "content": row.body or "",
                    "created_at": created_at,
                    "total_students": row.sent_count or 0,
                    "read_count": row.read_count or 0,
                })
            self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        except Exception as e:
            self.error = f"加载失败: {e}"
            self.notices = []
        self.loading = False

    # ── 创建通知 ──

    def set_create_title(self, v: str): self.create_title = v
    def set_create_content(self, v: str): self.create_content = v
    def set_create_category(self, v: str): self.create_category = v

    def create_notification(self):
        self.create_error = ""
        title = self.create_title.strip()
        if not title:
            self.create_error = "请输入通知标题"
            return

        self.creating = True
        yield
        try:
            with rx.session() as session:
                students = session.exec(
                    select(User.id).where(User.role == "student")
                ).all()
                if not students:
                    self.create_error = "没有可发送的学生"
                    self.creating = False
                    return

                body = self.create_content.strip()
                category = self.create_category
                notifs = [
                    Notification(
                        title=title, body=body, category=category,
                        user_id=uid, is_read=False,
                    )
                    for uid in students
                ]
                session.add_all(notifs)
                session.commit()
                count = len(students)

            self.create_title = ""
            self.create_content = ""
            self.create_category = "announcement"
            self.create_error = ""
            self.current_page = 1
            self.load_notices()
            self.creating = False
            return rx.toast.success(f"通知「{title}」已发布给 {count} 名学生")
        except Exception as e:
            self.create_error = f"创建失败: {e}"
            self.creating = False

    # ── 编辑通知 ──

    def start_edit(self, nid: int):
        for n in self.notices:
            if n.get("id") == nid:
                self.edit_id = nid
                self.edit_title = n.get("title", "")
                self.edit_content = n.get("content", "")
                self.edit_category = n.get("category", "announcement")
                self.edit_error = ""
                return
        try:
            with rx.session() as session:
                notif = session.exec(
                    select(Notification).where(Notification.id == nid)
                ).first()
                if notif:
                    self.edit_id = nid
                    self.edit_title = notif.title
                    self.edit_content = notif.body or ""
                    self.edit_category = notif.category
                    self.edit_error = ""
        except Exception:
            pass

    def cancel_edit(self):
        self.edit_id = 0
        self.edit_error = ""

    def set_edit_title(self, v: str): self.edit_title = v
    def set_edit_content(self, v: str): self.edit_content = v
    def set_edit_category(self, v: str): self.edit_category = v

    def update_notification(self):
        self.edit_error = ""
        new_title = self.edit_title.strip()
        if not new_title:
            self.edit_error = "标题不能为空"
            return

        self.editing = True
        yield
        try:
            with rx.session() as session:
                notif = session.exec(
                    select(Notification).where(Notification.id == self.edit_id)
                ).first()
                if not notif:
                    self.edit_error = "通知不存在"
                    self.editing = False
                    return
                old_title = notif.title
                old_category = notif.category

                group = session.exec(
                    select(Notification).where(
                        Notification.title == old_title,
                        Notification.category == old_category,
                    )
                ).all()
                for n in group:
                    n.title = new_title
                    n.body = self.edit_content.strip()
                    n.category = self.edit_category
                    session.add(n)
                session.commit()
                updated_count = len(group)

            self.edit_id = 0
            self.load_notices()
            self.editing = False
            return rx.toast.success(f"已更新 {updated_count} 条通知")
        except Exception as e:
            self.edit_error = f"更新失败: {e}"
            self.editing = False

    # ── 删除通知 ──

    def confirm_delete(self, n: dict):
        self.delete_target = n
        self.delete_error = ""

    def cancel_delete(self):
        self.delete_target = {}
        self.delete_error = ""

    def delete_notification(self):
        title = self.delete_target.get("title", "")
        category = self.delete_target.get("category", "")
        if not title:
            self.delete_error = "通知不存在"
            self.delete_target = {}
            return

        self.deleting = True
        yield
        try:
            with rx.session() as session:
                group = session.exec(
                    select(Notification).where(
                        Notification.title == title,
                        Notification.category == category,
                    )
                ).all()
                deleted_count = len(group)
                for n in group:
                    session.delete(n)
                session.commit()
            self.delete_target = {}
            self.load_notices()
            self.deleting = False
            return rx.toast.success(f"已删除 {deleted_count} 条通知")
        except Exception as e:
            self.delete_error = f"删除失败: {e}"
            self.deleting = False


# ═══════════════════════════════════════════════════════════════
# UI 组件
# ═══════════════════════════════════════════════════════════════

def category_badge(cat: str) -> rx.Component:
    label, color = CATEGORY_MAP.get(cat, ("通知", "gray"))
    return rx.badge(label, color_scheme=color, size="1", variant="soft")


def tab_button(tab: str, label: str, icon_name: str) -> rx.Component:
    is_active = TeacherNoticeState.current_tab == tab
    return rx.button(
        rx.hstack(rx.icon(icon_name, size=14), rx.text(label), spacing="1"),
        size="2",
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        on_click=TeacherNoticeState.switch_tab(tab),
    )


def create_form() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("send", size=18, color="blue.500"),
            rx.heading("发送新通知", size="4"),
            spacing="2", align="center",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("标题 *", font_size="sm", color="gray.600"),
                rx.input(
                    placeholder="如：期末考试成绩已公布",
                    value=TeacherNoticeState.create_title,
                    on_change=TeacherNoticeState.set_create_title,
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
                    value=TeacherNoticeState.create_category,
                    on_change=TeacherNoticeState.set_create_category,
                    width="100%",
                ),
                spacing="1", align="start", width="25%",
            ),
            rx.vstack(
                rx.text("", font_size="sm"),
                rx.button(
                    rx.icon("send", size=14), "发送通知",
                    color_scheme="blue", variant="solid",
                    on_click=TeacherNoticeState.create_notification,
                    loading=TeacherNoticeState.creating,
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
                value=TeacherNoticeState.create_content,
                on_change=TeacherNoticeState.set_create_content,
                width="100%", rows="3",
            ),
            spacing="1", align="start", width="100%",
        ),
        rx.text("通知将发送给所有已注册的学生", font_size="xs", color="gray.400"),
        rx.cond(
            TeacherNoticeState.create_error,
            rx.text(TeacherNoticeState.create_error, color="red.500", font_size="sm"),
            rx.fragment(),
        ),
        width="100%", padding="16px",
        border="1px solid var(--gray-200)", border_radius="8px",
        spacing="3",
    )


def edit_form() -> rx.Component:
    return rx.vstack(
        rx.heading("修改通知", size="4"),
        rx.hstack(
            rx.input(
                placeholder="通知标题",
                value=TeacherNoticeState.edit_title,
                on_change=TeacherNoticeState.set_edit_title,
                width="60%",
            ),
            rx.select.root(
                rx.select.trigger(placeholder="选择分类"),
                rx.select.content(
                    rx.select.group(
                        *[rx.select.item(label, value=v) for v, label in CATEGORY_OPTIONS]
                    ),
                ),
                value=TeacherNoticeState.edit_category,
                on_change=TeacherNoticeState.set_edit_category,
                width="25%",
            ),
            width="100%", spacing="2",
        ),
        rx.text_area(
            placeholder="通知内容",
            value=TeacherNoticeState.edit_content,
            on_change=TeacherNoticeState.set_edit_content,
            width="100%", rows="3",
        ),
        rx.hstack(
            rx.button(
                "保存修改", color_scheme="blue",
                on_click=TeacherNoticeState.update_notification,
                loading=TeacherNoticeState.editing,
            ),
            rx.button("取消", variant="outline", on_click=TeacherNoticeState.cancel_edit),
            spacing="2",
        ),
        rx.cond(
            TeacherNoticeState.edit_error,
            rx.text(TeacherNoticeState.edit_error, color="red.500", font_size="sm"),
            rx.fragment(),
        ),
        width="100%", padding="16px",
        border="1px solid var(--gray-200)", border_radius="8px",
        spacing="3",
    )


def sent_notification_row(n: dict) -> rx.Component:
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
                    rx.text(title, font_weight="bold", font_size="md", color="gray.800"),
                    rx.hstack(
                        category_badge(cat),
                        rx.text(
                            "· 共 ", total_students, " 人 · 已读 ",
                            read_count, " 人 · ", created_at,
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
                            on_click=TeacherNoticeState.start_edit(nid),
                        ),
                        rx.button(
                            rx.icon("trash-2", size=14), "删除",
                            size="1", color_scheme="red", variant="outline",
                            on_click=TeacherNoticeState.confirm_delete(n),
                        ),
                        spacing="2",
                    ),
                    spacing="2", align="start",
                    padding="8px 16px 16px",
                ),
            ),
            value=f"notif_{nid}",
        ),
        width="100%", collapsible=True,
    )


def delete_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("确认删除"),
            rx.alert_dialog.description(
                rx.text("确定要删除通知「", TeacherNoticeState.delete_title, "」吗？")
            ),
            rx.hstack(
                rx.button("取消", variant="outline", on_click=TeacherNoticeState.cancel_delete),
                rx.button(
                    "删除", color_scheme="red",
                    on_click=TeacherNoticeState.delete_notification,
                    loading=TeacherNoticeState.deleting,
                ),
                spacing="2", justify="end", width="100%",
            ),
        ),
        open=TeacherNoticeState.show_delete_dialog,
    )


def pagination_controls() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            size="1", variant="ghost",
            on_click=TeacherNoticeState.go_page(TeacherNoticeState.current_page - 1),
            is_disabled=~TeacherNoticeState.can_go_prev,
        ),
        rx.text(
            TeacherNoticeState.current_page, " / ", TeacherNoticeState.total_pages,
            font_size="sm", color="gray.500",
        ),
        rx.button(
            rx.icon("chevron-right", size=16),
            size="1", variant="ghost",
            on_click=TeacherNoticeState.go_page(TeacherNoticeState.current_page + 1),
            is_disabled=~TeacherNoticeState.can_go_next,
        ),
        width="100%", justify="center", spacing="4",
    )


def notifications_teacher_page() -> rx.Component:
    """教师端 — 公告与通知管理页面"""
    content = rx.vstack(
        # 创建/编辑表单切换
        rx.cond(TeacherNoticeState.is_editing, edit_form(), create_form()),

        # 分类筛选 + 列表标题
        rx.hstack(
            rx.heading("已发送的通知", size="4"),
            rx.icon("inbox", size=18, color="gray.400"),
            rx.spacer(),
            *[tab_button(t, l, i) for t, l, i in CATEGORY_TABS],
            width="100%", align="center", spacing="2", wrap="wrap",
        ),

        # 内容区域
        rx.cond(
            TeacherNoticeState.loading,
            loading_spinner("加载通知中..."),
            rx.cond(
                TeacherNoticeState.error,
                rx.vstack(
                    rx.icon("alert-circle", size=32, color="red.500"),
                    rx.text(TeacherNoticeState.error, color="red.500"),
                    rx.button("重试", on_click=TeacherNoticeState.refresh),
                    spacing="2", align="center", padding="40px",
                ),
                rx.cond(
                    TeacherNoticeState.has_data,
                    rx.vstack(
                        rx.foreach(TeacherNoticeState.notices, sent_notification_row),
                        rx.cond(TeacherNoticeState.show_pagination, pagination_controls(), rx.fragment()),
                        width="100%", spacing="0",
                    ),
                    empty_state("暂无已发送的通知", icon="inbox"),
                ),
            ),
        ),

        delete_dialog(),
        rx.toast.provider(),

        width="100%", max_width="900px", margin="0 auto", spacing="4",
        on_mount=TeacherNoticeState.load_notices,
    )
    return page_layout(title="公告与通知管理", content=content)
