"""F-S-012 公告通知 — 学生端页面（最终版）

功能：
  - 分类标签页：全部 / 课程公告 / 截止提醒 / 成绩通知 / 未读
  - 通知卡片：图标、分类标签、优先级徽章、未读标记、课程名
  - 点击标记已读 / 一键全部已读
  - 分页加载（含页码跳转）
  - 骨架屏加载态、空状态、错误重试
  - 页面挂载自动加载 + 手动刷新
  - Toast 提示消息
"""
import os
import reflex as rx
import requests

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ── 分类配置 ──────────────────────────────────────────────────

CATEGORY_META = {
    "announcement": {"label": "课程公告", "icon": "megaphone",   "color": "blue"},
    "deadline":     {"label": "截止提醒", "icon": "clock",       "color": "orange"},
    "grade":        {"label": "成绩通知", "icon": "bar-chart-3", "color": "green"},
    "system":       {"label": "系统通知", "icon": "settings",    "color": "purple"},
    "graded":       {"label": "已批改",   "icon": "check-circle", "color": "teal"},
}

TABS = [
    ("all",          "全部"),
    ("announcement", "课程公告"),
    ("deadline",     "截止提醒"),
    ("grade",        "成绩通知"),
    ("system",       "系统通知"),
    ("graded",       "已批改"),
    ("unread",       "未读"),
]

# ── 状态管理 ──────────────────────────────────────────────────

class NotificationsState(rx.State):
    """学生端通知状态管理"""

    # 数据
    notifications: list[dict] = []
    unread_count: int = 0
    category_counts: dict = {}

    # 筛选 & 分页
    current_tab: str = "all"
    current_page: int = 1
    page_size: int = 12
    total: int = 0
    total_pages: int = 1

    # UI
    loading: bool = True
    error: str = ""
    toast_message: str = ""
    toast_open: bool = False

    # ── 计算属性 ──

    @rx.var
    def has_unread(self) -> bool:
        return self.unread_count > 0

    @rx.var
    def has_data(self) -> bool:
        return len(self.notifications) > 0

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
    def unread_badge_text(self) -> str:
        if self.unread_count == 0:
            return ""
        return f"{self.unread_count} 条未读" if self.unread_count <= 99 else "99+ 条未读"

    # ── 操作方法 ──

    def switch_tab(self, tab: str):
        """切换分类标签"""
        if tab == self.current_tab:
            return
        self.current_tab = tab
        self.current_page = 1
        return self.load_notifications()

    def go_page(self, page: int):
        """跳转页码"""
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return
        self.current_page = page
        return self.load_notifications()

    def refresh(self):
        """手动刷新"""
        return self.load_notifications()

    def load_notifications(self):
        """加载通知列表"""
        self.loading = True
        self.error = ""
        try:
            params = {"page": self.current_page, "page_size": self.page_size}
            if self.current_tab == "unread":
                params["unread_only"] = True
            elif self.current_tab != "all":
                params["category"] = self.current_tab

            resp = requests.get(
                f"{API_BASE}/api/notifications",
                params=params,
                headers=_auth_headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.notifications = data.get("items", [])
                self.total = data.get("total", 0)
                self.unread_count = data.get("unread_count", 0)
                self.category_counts = data.get("category_counts", {})
                self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
            elif resp.status_code == 401:
                self.error = "请先登录后再查看通知"
                self.notifications = []
            elif resp.status_code == 404:
                self.error = "通知服务暂不可用"
                self.notifications = []
            else:
                self.error = f"加载失败 (HTTP {resp.status_code})"
                self.notifications = []
        except requests.exceptions.ConnectionError:
            self.error = "无法连接服务器，请确认服务已启动"
        except requests.exceptions.Timeout:
            self.error = "请求超时，请稍后重试"
        except Exception as e:
            self.error = f"加载出错: {e}"
        finally:
            self.loading = False

    def mark_read(self, nid: int):
        """标记单条已读"""
        try:
            resp = requests.post(
                f"{API_BASE}/api/notifications/{nid}/read",
                headers=_auth_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                self.unread_count = resp.json().get("unread_count", 0)
                for n in self.notifications:
                    if n.get("id") == nid:
                        n["is_read"] = True
        except Exception:
            self.toast_message = "操作失败，请重试"
            self.toast_open = True

    def mark_all_read(self):
        """一键全部已读"""
        try:
            resp = requests.post(
                f"{API_BASE}/api/notifications/read-all",
                headers=_auth_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                for n in self.notifications:
                    n["is_read"] = True
                self.unread_count = 0
                self.toast_message = "已全部标记为已读 ✓"
                self.toast_open = True
        except Exception:
            self.toast_message = "操作失败，请重试"
            self.toast_open = True

    def dismiss_toast(self):
        """关闭 Toast"""
        self.toast_open = False


def _auth_headers() -> dict:
    """获取认证请求头"""
    token = os.environ.get("DEV_TOKEN", "")
    if not token:
        token = os.environ.get("DEV_STUDENT_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


# ── UI 组件 ───────────────────────────────────────────────────

def skeleton_card() -> rx.Component:
    """骨架屏卡片"""
    return rx.card(
        rx.hstack(
            rx.skeleton(width="44px", height="44px", border_radius="12px"),
            rx.vstack(
                rx.skeleton(width="80px", height="16px"),
                rx.skeleton(width="240px", height="20px"),
                rx.skeleton(width="160px", height="14px"),
                spacing="2",
            ),
            spacing="4", align="center",
        ),
        padding="16px",
    )


def notification_card(n: dict) -> rx.Component:
    """通知卡片"""
    cat = n.get("category", "announcement")
    meta = CATEGORY_META.get(cat, CATEGORY_META["announcement"])
    is_read = n.get("is_read", False)
    priority = n.get("priority", "normal")
    nid = n.get("id", 0)

    return rx.card(
        rx.hstack(
            # 左侧图标
            rx.box(
                rx.icon(meta["icon"], size=20, color=f"{meta['color']}.500"),
                width="44px", height="44px",
                border_radius="12px",
                bg=rx.cond(is_read, "gray.100", f"{meta['color']}.50"),
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            # 内容区
            rx.vstack(
                rx.hstack(
                    rx.badge(meta["label"], color_scheme=meta["color"], variant="soft", size="1"),
                    rx.cond(
                        priority == "urgent",
                        rx.badge("紧急", color_scheme="red", variant="solid", size="1"),
                    ),
                    rx.cond(
                        (priority == "important") & (~is_read),
                        rx.badge("重要", color_scheme="yellow", variant="soft", size="1"),
                    ),
                    rx.cond(
                        ~is_read,
                        rx.text("● 未读", color=f"{meta['color']}.500", font_size="xs", font_weight="bold"),
                    ),
                    spacing="2",
                ),
                rx.text(
                    n.get("title", ""),
                    font_size="md", font_weight="bold",
                    color=rx.cond(is_read, "gray.500", "gray.900"),
                ),
                rx.cond(
                    n.get("content", ""),
                    rx.text(
                        n.get("content", ""),
                        font_size="sm", color="gray.500",
                        overflow="hidden", white_space="nowrap",
                        text_overflow="ellipsis", max_width="400px",
                    ),
                ),
                rx.hstack(
                    rx.text(n.get("created_at", ""), font_size="xs", color="gray.400"),
                    rx.cond(
                        n.get("course_name", ""),
                        rx.badge(
                            n.get("course_name", ""),
                            color_scheme="gray", variant="outline", size="1",
                        ),
                    ),
                    spacing="3",
                ),
                spacing="1", align="start", flex="1",
            ),
            # 右侧操作区
            rx.vstack(
                rx.cond(
                    ~is_read,
                    rx.box(
                        width="10px", height="10px", border_radius="50%",
                        bg=f"{meta['color']}.500",
                    ),
                ),
                rx.cond(
                    ~is_read,
                    rx.button(
                        "已读", size="1", variant="ghost", color_scheme=meta["color"],
                        on_click=NotificationsState.mark_read(nid),
                    ),
                ),
                spacing="3", align="center", flex_shrink="0",
            ),
            spacing="4", width="100%", align="center",
        ),
        padding="16px 20px",
        variant="ghost" if is_read else "classic",
        cursor="pointer" if not is_read else "default",
        _hover={"shadow": "md"} if not is_read else {},
    )


def tabs_bar() -> rx.Component:
    """分类标签栏 + 操作按钮"""
    return rx.hstack(
        rx.tabs.root(
            rx.tabs.list(
                *[rx.tabs.trigger(label, value=val) for val, label in TABS],
                size="2",
            ),
            value=NotificationsState.current_tab,
            on_change=NotificationsState.switch_tab,
            flex="1",
        ),
        rx.hstack(
            rx.cond(
                NotificationsState.has_unread,
                rx.button(
                    rx.icon("check-check", size=14),
                    "全部已读",
                    size="2", variant="ghost", color_scheme="blue",
                    on_click=NotificationsState.mark_all_read,
                ),
            ),
            rx.button(
                rx.icon("refresh-cw", size=14),
                variant="ghost", size="2", color_scheme="gray",
                on_click=NotificationsState.refresh,
            ),
            spacing="1",
        ),
        justify="between", width="100%",
        padding_bottom="12px",
        border_bottom="1px solid var(--gray-200)",
    )


def pagination_bar() -> rx.Component:
    """分页栏"""
    return rx.cond(
        NotificationsState.show_pagination,
        rx.hstack(
            rx.button(
                rx.icon("chevron-left", size=14),
                "上一页",
                size="2", variant="outline",
                on_click=NotificationsState.go_page(NotificationsState.current_page - 1),
                disabled=~NotificationsState.can_go_prev,
            ),
            rx.hstack(
                rx.text(f"第 {NotificationsState.current_page} 页", font_size="sm", color="gray.500"),
                rx.text("·", color="gray.300"),
                rx.text(f"共 {NotificationsState.total_pages} 页", font_size="sm", color="gray.400"),
                rx.text("·", color="gray.300"),
                rx.text(f"{NotificationsState.total} 条通知", font_size="sm", color="gray.400"),
                spacing="2",
            ),
            rx.button(
                "下一页",
                rx.icon("chevron-right", size=14),
                size="2", variant="outline",
                on_click=NotificationsState.go_page(NotificationsState.current_page + 1),
                disabled=~NotificationsState.can_go_next,
            ),
            spacing="3", justify="center", width="100%", padding_top="16px",
        ),
    )


def empty_state() -> rx.Component:
    """空状态"""
    return rx.center(
        rx.vstack(
            rx.icon("inbox", size=48, color="gray.300"),
            rx.text("暂无通知", color="gray.400", font_size="lg", font_weight="bold"),
            rx.text(
                "当有新的课程通知、截止提醒或成绩通知时，将在这里显示",
                color="gray.300", font_size="sm", text_align="center",
            ),
            spacing="3", padding_y="80px",
        ),
    )


def error_state() -> rx.Component:
    """错误状态"""
    return rx.center(
        rx.vstack(
            rx.icon("triangle-alert", size=48, color="red.300"),
            rx.text(NotificationsState.error, color="red.400", font_size="md", text_align="center"),
            rx.button(
                rx.icon("refresh-cw", size=14), "重新加载",
                size="2", color_scheme="blue",
                on_click=NotificationsState.load_notifications,
            ),
            spacing="3", padding_y="80px",
        ),
    )


def loading_state() -> rx.Component:
    """加载骨架屏"""
    return rx.vstack(
        *[skeleton_card() for _ in range(4)],
        spacing="3", width="100%", padding_y="16px",
    )


def toast_component() -> rx.Component:
    """Toast 提示"""
    return rx.cond(
        NotificationsState.toast_open,
        rx.box(
            rx.hstack(
                rx.icon("check-circle", size=18, color="green.500"),
                rx.text(NotificationsState.toast_message, font_size="sm"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=14),
                    variant="ghost", size="1", color_scheme="gray",
                    on_click=NotificationsState.dismiss_toast,
                ),
                spacing="2", width="100%",
            ),
            padding="12px 16px", border_radius="10px",
            bg="white", box_shadow="0 4px 20px rgba(0,0,0,0.12)",
            position="fixed", bottom="24px", left="50%",
            transform="translateX(-50%)",
            z_index="1000", max_width="400px",
        ),
    )


def notifications_page() -> rx.Component:
    """学生端通知页面"""
    return rx.fragment(
        toast_component(),
        rx.container(
            rx.vstack(
                # 页头
                rx.hstack(
                    rx.vstack(
                        rx.heading("📬 公告与通知", size="7"),
                        rx.text("课程公告 · 作业截止 · 成绩发布", color="gray.500", font_size="sm"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        NotificationsState.unread_count > 0,
                        rx.badge(
                            NotificationsState.unread_badge_text,
                            color_scheme="red", variant="soft", size="2",
                        ),
                    ),
                    width="100%",
                ),
                # 标签栏
                tabs_bar(),
                # 内容区
                rx.cond(
                    NotificationsState.loading,
                    loading_state(),
                    rx.cond(
                        NotificationsState.error != "",
                        error_state(),
                        rx.cond(
                            ~NotificationsState.has_data,
                            empty_state(),
                            rx.vstack(
                                rx.foreach(
                                    NotificationsState.notifications,
                                    notification_card,
                                ),
                                pagination_bar(),
                                spacing="3", width="100%",
                            ),
                        ),
                    ),
                ),
                spacing="6", width="100%",
                padding="24px 32px",
                max_width="860px",
            ),
            size="4",
            on_mount=NotificationsState.load_notifications,
        ),
    )
