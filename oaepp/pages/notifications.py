"""F-S-012 公告通知 — Reflex 页面

公告与通知列表页面，支持：
- 分类标签页（全部/课程公告/截止提醒/成绩通知/未读）
- 通知卡片（未读标识、优先级标签）
- 标记已读/全部已读
- 分页加载
- 未读计数徽章
"""
import reflex as rx


class NotificationsPageState(rx.State):
    """通知页面状态管理"""

    # 数据
    notifications: list[dict] = []
    unread_count: int = 0
    category_counts: dict = {}

    # 筛选
    current_tab: str = "all"
    current_page: int = 1
    page_size: int = 15
    total: int = 0
    total_pages: int = 1

    # UI 状态
    loading: bool = True
    error: str = ""

    @rx.var
    def has_unread(self) -> bool:
        return self.unread_count > 0

    @rx.var
    def show_pagination(self) -> bool:
        return self.total > self.page_size

    def switch_tab(self, tab: str):
        """切换分类标签页"""
        self.current_tab = tab
        self.current_page = 1
        self.load_notifications()

    def go_page(self, page: int):
        """翻页"""
        if page < 1 or page > self.total_pages:
            return
        self.current_page = page
        self.load_notifications()

    def load_notifications(self):
        """加载通知列表（需通过 API 调用实现）"""
        self.loading = True
        self.error = ""
        # 实际数据加载通过前端 JS 调用 /api/notifications 实现
        # Reflex State 方法由前端触发
        self.loading = False

    def mark_read(self, nid: int):
        """标记单条通知为已读"""
        # 本地状态更新
        for n in self.notifications:
            if n.get("id") == nid:
                n["is_read"] = True
        self.unread_count = max(0, self.unread_count - 1)

    def mark_all_read(self):
        """标记全部通知为已读"""
        for n in self.notifications:
            n["is_read"] = True
        self.unread_count = 0


def notification_card(n: dict, index: int) -> rx.Component:
    """单条通知卡片组件"""
    cat = n.get("category", "announcement")
    is_read = n.get("is_read", False)
    priority = n.get("priority", "normal")

    # 分类配置
    cat_config = {
        "announcement": {"label": "课程公告", "icon": "📢", "color": "blue"},
        "deadline": {"label": "截止提醒", "icon": "⏰", "color": "orange"},
        "grade": {"label": "成绩通知", "icon": "📊", "color": "green"},
    }
    cfg = cat_config.get(cat, cat_config["announcement"])

    return rx.box(
        rx.hstack(
            # 图标
            rx.box(
                rx.text(cfg["icon"], font_size="1.2em"),
                border_radius="12px",
                padding="8px",
                bg=f"{cfg['color']}.50",
                width="40px",
                height="40px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            # 内容区
            rx.vstack(
                rx.hstack(
                    rx.badge(cfg["label"], color_scheme=cfg["color"], variant="subtle"),
                    rx.cond(
                        priority == "urgent",
                        rx.badge("紧急", color_scheme="red", variant="subtle"),
                    ),
                    rx.cond(
                        priority == "important",
                        rx.badge("重要", color_scheme="yellow", variant="subtle"),
                    ),
                    rx.cond(
                        ~is_read,
                        rx.text("● 未读", color="red.500", font_size="xs"),
                    ),
                    spacing="2",
                ),
                rx.heading(n.get("title", ""), size="sm", color=rx.cond(is_read, "gray.500", "gray.800")),
                rx.cond(
                    n.get("content", ""),
                    rx.text(n.get("content", ""), font_size="sm", color="gray.500", max_lines=2),
                ),
                rx.hstack(
                    rx.text(n.get("created_at", ""), font_size="xs", color="gray.400"),
                    rx.cond(
                        n.get("course_name", ""),
                        rx.text(n.get("course_name", ""), font_size="xs", color="gray.400"),
                    ),
                    spacing="3",
                ),
                spacing="1",
                align="start",
            ),
            # 未读圆点
            rx.cond(
                ~is_read,
                rx.box(
                    width="10px",
                    height="10px",
                    border_radius="50%",
                    bg=f"{cfg['color']}.500",
                    flex_shrink="0",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        padding="16px",
        border_radius="12px",
        border_width="1px",
        border_color=rx.cond(is_read, "gray.100", "gray.200"),
        bg="white",
        box_shadow=rx.cond(is_read, "none", "sm"),
        opacity=rx.cond(is_read, "0.75", "1"),
        cursor="pointer",
        _hover={"transform": "translateY(-1px)", "box_shadow": "md"},
        transition="all 0.2s",
    )


def category_tabs() -> rx.Component:
    """分类标签页组件"""
    return rx.hstack(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("全部", value="all"),
                rx.tabs.trigger("课程公告", value="announcement"),
                rx.tabs.trigger("截止提醒", value="deadline"),
                rx.tabs.trigger("成绩通知", value="grade"),
                rx.tabs.trigger("未读", value="unread"),
            ),
            width="100%",
            on_value_change=NotificationsPageState.switch_tab,
            value=NotificationsPageState.current_tab,
        ),
        rx.cond(
            NotificationsPageState.has_unread,
            rx.button(
                "全部标为已读",
                size="sm",
                color_scheme="blue",
                variant="ghost",
                on_click=NotificationsPageState.mark_all_read,
            ),
        ),
        justify="between",
        width="100%",
        padding_bottom="16px",
        border_bottom="1px solid",
        border_color="gray.100",
    )


def notifications_page() -> rx.Component:
    """公告与通知主页面"""
    return rx.container(
        rx.vstack(
            # 页面标题
            rx.hstack(
                rx.vstack(
                    rx.heading("公告与通知", size="lg"),
                    rx.text("课程公告 · 作业截止提醒 · 成绩发布通知", color="gray.500", font_size="sm"),
                    spacing="1",
                ),
                justify="between",
                width="100%",
            ),
            # 分类标签
            category_tabs(),
            # 通知列表
            rx.cond(
                NotificationsPageState.loading,
                rx.center(
                    rx.spinner(size="lg"),
                    rx.text("加载中…", color="gray.400"),
                    padding_y="80px",
                ),
                rx.cond(
                    NotificationsPageState.error != "",
                    rx.center(
                        rx.text(NotificationsPageState.error, color="red.400"),
                        padding_y="80px",
                    ),
                    rx.cond(
                        NotificationsPageState.notifications.length() == 0,
                        rx.center(
                            rx.text("暂无通知", color="gray.400"),
                            padding_y="80px",
                        ),
                        rx.vstack(
                            rx.foreach(
                                NotificationsPageState.notifications,
                                lambda n, idx: notification_card(n, idx),
                            ),
                            # 分页
                            rx.cond(
                                NotificationsPageState.show_pagination,
                                rx.hstack(
                                    rx.button(
                                        "上一页",
                                        size="sm",
                                        variant="outline",
                                        on_click=NotificationsPageState.go_page(
                                            NotificationsPageState.current_page - 1
                                        ),
                                        is_disabled=NotificationsPageState.current_page <= 1,
                                    ),
                                    rx.text(
                                        f"第 {NotificationsPageState.current_page} / {NotificationsPageState.total_pages} 页",
                                        font_size="sm",
                                        color="gray.500",
                                    ),
                                    rx.button(
                                        "下一页",
                                        size="sm",
                                        variant="outline",
                                        on_click=NotificationsPageState.go_page(
                                            NotificationsPageState.current_page + 1
                                        ),
                                        is_disabled=NotificationsPageState.current_page >= NotificationsPageState.total_pages,
                                    ),
                                    justify="center",
                                    width="100%",
                                    padding_top="16px",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                            max_height="calc(100vh - 260px)",
                            overflow_y="auto",
                        ),
                    ),
                ),
            ),
            spacing="6",
            width="100%",
            padding="32px",
            max_width="800px",
        ),
    )
