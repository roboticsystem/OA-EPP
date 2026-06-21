"""F-S-012 公告与通知 — 学生端页面

路由: /notifications（由 app.py 自动发现注册）
页面函数: notifications_page()
状态类: NoticeState（内联定义于本文件，继承 rx.State）

截图匹配要素：
- 标题"📢 公告与通知" + 右上角红色未读数字徽章 + 浅黄色背景
- 分类标签：全部 / 公告 / 截止提醒 / 成绩通知
- 未读项：蓝色竖线左边框 + 粗体标题 + "● 未读"标记
- 已读项：灰色标题
- 底部"全部标记已读"灰色填充按钮
"""

import reflex as rx
from sqlmodel import select, func

from oaepp.components.layout import page_layout
from oaepp.components.common import empty_state, loading_spinner
from oaepp.models import Notification, User
from oaepp.states import GlobalState


# ── 分类配置 ──
CATEGORY_MAP = {
    "announcement": ("公告", "blue"),
    "deadline": ("截止提醒", "orange"),
    "grade": ("成绩通知", "green"),
}

CATEGORY_TABS = [
    ("all", "全部", "inbox"),
    ("announcement", "公告", "megaphone"),
    ("deadline", "截止提醒", "clock"),
    ("grade", "成绩通知", "graduation-cap"),
]


# ═══════════════════════════════════════════════════════════════
# NoticeState — 学生端公告通知状态（内联于页面文件）
# ═══════════════════════════════════════════════════════════════

class NoticeState(rx.State):
    """学生端公告通知状态 — 直接继承 rx.State，通过 get_state 访问 GlobalState"""

    notices: list[dict] = []
    unread_count: int = 0

    current_tab: str = "all"
    current_page: int = 1
    page_size: int = 12
    total: int = 0
    total_pages: int = 1

    loading: bool = True
    error: str = ""

    # ── 辅助方法 ──

    def _get_user_id(self) -> int:
        """从 GlobalState.current_user 获取真实 user_id"""
        gs = self.get_state(GlobalState)
        if not gs.current_user:
            return 0
        student_no = gs.current_user.get("student_no", "")
        if not student_no:
            return 0
        try:
            with rx.session() as session:
                u = session.exec(
                    select(User.id).where(User.student_no == student_no)
                ).first()
                if u:
                    return u
        except Exception:
            pass
        return 0

    @staticmethod
    def _notif_to_dict(n: Notification) -> dict:
        return {
            "id": n.id,
            "title": n.title,
            "content": n.body or "",
            "category": n.category,
            "is_read": bool(n.is_read),
            "created_at": str(n.created_at) if n.created_at else "",
        }

    # ── 计算属性 ──

    @rx.var
    def has_unread(self) -> bool:
        return self.unread_count > 0

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

    # ── 列表加载 ──

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
            user_id = self._get_user_id()
            with rx.session() as session:
                stmt = select(Notification)
                if user_id:
                    stmt = stmt.where(Notification.user_id == user_id)
                cat = self.current_tab
                if cat == "unread":
                    stmt = stmt.where(Notification.is_read == False)  # noqa: E712
                elif cat != "all":
                    stmt = stmt.where(Notification.category == cat)

                count_stmt = select(func.count()).select_from(stmt.subquery())
                self.total = session.exec(count_stmt).one()

                offset = (self.current_page - 1) * self.page_size
                stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(self.page_size)
                rows = session.exec(stmt).all()

                if user_id:
                    unread_stmt = (
                        select(func.count())
                        .where(Notification.user_id == user_id)
                        .where(Notification.is_read == False)  # noqa: E712
                    )
                    self.unread_count = session.exec(unread_stmt).one()
                else:
                    self.unread_count = 0

            self.notices = [self._notif_to_dict(n) for n in rows]
            self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        except Exception as e:
            self.error = f"加载失败: {e}"
            self.notices = []
        self.loading = False

    # ── 标记已读 ──

    def mark_as_read(self, nid: int):
        try:
            user_id = self._get_user_id()
            if not user_id:
                return rx.toast.error("请先登录")
            with rx.session() as session:
                notif = session.exec(
                    select(Notification).where(
                        Notification.id == nid,
                        Notification.user_id == user_id,
                    )
                ).first()
                if notif and not notif.is_read:
                    notif.is_read = True
                    session.add(notif)
                    session.commit()
                    for n in self.notices:
                        if n.get("id") == nid:
                            n["is_read"] = True
                            break
                    self.unread_count = max(0, self.unread_count - 1)
            return rx.toast.success("已标记为已读")
        except Exception:
            return rx.toast.error("操作失败，请重试")

    def mark_all_read(self):
        try:
            user_id = self._get_user_id()
            if not user_id:
                return rx.toast.error("请先登录")
            with rx.session() as session:
                unread = session.exec(
                    select(Notification).where(
                        Notification.user_id == user_id,
                        Notification.is_read == False,  # noqa: E712
                    )
                ).all()
                for n in unread:
                    n.is_read = True
                    session.add(n)
                session.commit()
            for n in self.notices:
                n["is_read"] = True
            self.unread_count = 0
            return rx.toast.success("已全部标记为已读")
        except Exception:
            return rx.toast.error("操作失败，请重试")


# ═══════════════════════════════════════════════════════════════
# UI 组件
# ═══════════════════════════════════════════════════════════════

def notification_card(n: dict) -> rx.Component:
    """通知卡片 — 未读带蓝色左边框，匹配截图布局（无内容摘要）"""
    nid = n.get("id", 0)
    cat = n.get("category", "")
    cat_label, cat_color = CATEGORY_MAP.get(cat, ("通知", "gray"))
    is_read = n.get("is_read", True)

    return rx.hstack(
        rx.box(
            width="4px",
            height="100%",
            bg=rx.cond(is_read, "transparent", "blue.500"),
            border_radius="2px",
            flex_shrink=0,
        ),
        rx.text(
            n.get("title", ""),
            font_weight=rx.cond(is_read, "normal", "bold"),
            color=rx.cond(is_read, "gray.500", "gray.900"),
            font_size="md",
            flex_grow=1,
        ),
        rx.spacer(),
        rx.hstack(
            rx.badge(cat_label, color_scheme=cat_color, size="1", variant="soft"),
            rx.text(n.get("created_at", ""), font_size="xs", color="gray.400"),
            rx.cond(
                is_read,
                rx.fragment(),
                rx.hstack(
                    rx.icon("circle", size=8, color="blue.500"),
                    rx.text("未读", font_size="xs", color="blue.500"),
                    spacing="1",
                ),
            ),
            spacing="2", align="center",
        ),
        width="100%",
        padding="12px 16px",
        border_bottom="1px solid var(--gray-100)",
        on_click=NoticeState.mark_as_read(nid),
        cursor="pointer",
        _hover={"bg": "var(--gray-50)"},
        spacing="2", align="center",
    )


def tab_button(tab: str, label: str, icon_name: str) -> rx.Component:
    is_active = NoticeState.current_tab == tab
    return rx.button(
        rx.hstack(rx.icon(icon_name, size=14), rx.text(label), spacing="1"),
        size="2",
        variant=rx.cond(is_active, "solid", "ghost"),
        color_scheme=rx.cond(is_active, "blue", "gray"),
        on_click=NoticeState.switch_tab(tab),
    )


def pagination_controls() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page(NoticeState.current_page - 1),
            is_disabled=~NoticeState.can_go_prev,
        ),
        rx.text(
            NoticeState.current_page, " / ", NoticeState.total_pages,
            font_size="sm", color="gray.500",
        ),
        rx.button(
            rx.icon("chevron-right", size=16),
            size="1", variant="ghost",
            on_click=NoticeState.go_page(NoticeState.current_page + 1),
            is_disabled=~NoticeState.can_go_next,
        ),
        width="100%", justify="center", spacing="4",
    )


def notifications_page() -> rx.Component:
    """学生端 — 公告与通知页面"""
    content = rx.vstack(
        # 标题栏 + 未读徽章（浅黄色背景）
        rx.hstack(
            rx.heading("📢 公告与通知", size="6"),
            rx.spacer(),
            rx.cond(
                NoticeState.has_unread,
                rx.badge(
                    NoticeState.unread_count,
                    color_scheme="red", variant="solid", size="2",
                    border_radius="full",
                ),
                rx.fragment(),
            ),
            width="100%", align="center",
            padding="12px 16px",
            bg="#FFF8E1",
            border_radius="8px",
        ),
        # 分类标签
        rx.hstack(
            *[tab_button(t, l, i) for t, l, i in CATEGORY_TABS],
            width="100%", justify="center", spacing="2", wrap="wrap",
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
                        rx.foreach(NoticeState.notices, notification_card),
                        rx.cond(NoticeState.show_pagination, pagination_controls(), rx.fragment()),
                        width="100%", spacing="0",
                    ),
                    empty_state("暂无通知", icon="inbox"),
                ),
            ),
        ),
        # 全部标记已读按钮
        rx.cond(
            NoticeState.has_unread,
            rx.button(
                "全部标记已读",
                width="100%", variant="soft", color_scheme="gray",
                on_click=NoticeState.mark_all_read,
                margin_top="12px",
            ),
            rx.fragment(),
        ),
        rx.toast.provider(),
        width="100%", max_width="800px", margin="0 auto", spacing="4",
        on_mount=NoticeState.load_notices,
    )
    return page_layout(title="公告与通知", content=content)
