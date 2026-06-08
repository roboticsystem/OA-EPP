"""F-S-012 公告通知 — 教师端管理页面（最终版）

功能：
  - 通知列表（按 title+category 分组，含已读统计）
  - 创建通知（标题/内容/分类/课程范围/优先级）
  - 编辑通知（内联面板）
  - 删除通知（确认弹窗 + 批量删除同组）
  - 分类筛选 & 分页
  - 骨架屏 / 空状态 / 错误重试
  - Toast 消息提示
"""
import os
import reflex as rx
import requests

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ── 分类配置 ──────────────────────────────────────────────────

CATEGORY_META = {
    "all":          {"label": "全部",     "icon": "layout-list", "color": "gray"},
    "announcement": {"label": "课程公告", "icon": "megaphone",   "color": "blue"},
    "deadline":     {"label": "截止提醒", "icon": "clock",       "color": "orange"},
    "grade":        {"label": "成绩通知", "icon": "bar-chart-3", "color": "green"},
}
CATEGORY_OPTIONS = ["announcement", "deadline", "grade"]
PRIORITY_OPTIONS = ["normal", "important", "urgent"]

# ── 状态管理 ──────────────────────────────────────────────────

class TeacherNotificationsState(rx.State):
    """教师端通知管理状态"""

    # 列表数据
    notifications: list[dict] = []
    total: int = 0
    current_page: int = 1
    page_size: int = 12
    total_pages: int = 1
    current_tab: str = "all"
    loading: bool = True
    error: str = ""

    # 创建表单
    show_create: bool = False
    create_title: str = ""
    create_content: str = ""
    create_category: str = "announcement"
    create_priority: str = "normal"
    create_course_id: int = 0
    creating: bool = False
    create_error: str = ""
    create_success: str = ""

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

    # 全局提示
    toast_message: str = ""
    toast_open: bool = False

    # ── 计算属性 ──

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
    def has_data(self) -> bool:
        return len(self.notifications) > 0

    @rx.var
    def show_delete_dialog(self) -> bool:
        return bool(self.delete_target)

    @rx.var
    def delete_title(self) -> str:
        return self.delete_target.get("title", "") if self.delete_target else ""

    # ── 列表操作 ──

    def switch_tab(self, tab: str):
        if tab == self.current_tab:
            return
        self.current_tab = tab
        self.current_page = 1
        return self.load_notifications()

    def go_page(self, page: int):
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return
        self.current_page = page
        return self.load_notifications()

    def refresh(self):
        return self.load_notifications()

    def load_notifications(self):
        self.loading = True
        self.error = ""
        try:
            params = {"page": self.current_page, "page_size": self.page_size}
            if self.current_tab != "all":
                params["category"] = self.current_tab

            resp = requests.get(
                f"{API_BASE}/api/teacher/notifications",
                params=params, headers=_auth_headers(), timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.notifications = data.get("items", [])
                self.total = data.get("total", 0)
                self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
            elif resp.status_code == 401:
                self.error = "请先以教师身份登录"
                self.notifications = []
            else:
                self.error = f"加载失败 (HTTP {resp.status_code})"
                self.notifications = []
        except requests.exceptions.ConnectionError:
            self.error = "无法连接服务器，请确认后端已启动"
        except requests.exceptions.Timeout:
            self.error = "请求超时，请稍后重试"
        except Exception as e:
            self.error = f"加载出错: {e}"
        finally:
            self.loading = False

    # ── 创建 ──

    def toggle_create(self):
        self.show_create = not self.show_create
        if not self.show_create:
            self.reset_create_form()

    def reset_create_form(self):
        self.create_title = ""
        self.create_content = ""
        self.create_category = "announcement"
        self.create_priority = "normal"
        self.create_course_id = 0
        self.create_error = ""
        self.create_success = ""

    def set_create_title(self, v: str): self.create_title = v
    def set_create_content(self, v: str): self.create_content = v
    def set_create_category(self, v: str): self.create_category = v
    def set_create_priority(self, v: str): self.create_priority = v
    def set_create_course_id(self, v: str):
        try:
            self.create_course_id = int(v) if v else 0
        except ValueError:
            self.create_course_id = 0

    def create_notification(self):
        self.create_error = ""
        self.create_success = ""
        if not self.create_title.strip():
            self.create_error = "请输入通知标题"
            return
        self.creating = True
        try:
            body = {
                "title": self.create_title.strip(),
                "content": self.create_content.strip(),
                "category": self.create_category,
                "priority": self.create_priority,
            }
            if self.create_course_id > 0:
                body["course_id"] = self.create_course_id

            resp = requests.post(
                f"{API_BASE}/api/teacher/notifications",
                json=body, headers=_auth_headers(), timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.create_success = f"✓ 已发送给 {data.get('sent_count', 0)} 名学生"
                self.reset_create_form()
                self.show_create = False
                self.current_page = 1
                self.toast_message = f"通知已发布，共发送 {data.get('sent_count', 0)} 条"
                self.toast_open = True
                return self.load_notifications()
            elif resp.status_code == 409:
                self.create_error = "请勿在 30 秒内重复提交相同通知"
            elif resp.status_code == 422:
                detail = resp.json().get("detail", "参数错误")
                self.create_error = str(detail[0].get("msg", detail)) if isinstance(detail, list) else str(detail)
            elif resp.status_code == 401:
                self.create_error = "请先以教师身份登录"
            else:
                self.create_error = f"创建失败 (HTTP {resp.status_code})"
        except requests.exceptions.ConnectionError:
            self.create_error = "无法连接服务器"
        except Exception as e:
            self.create_error = f"创建出错: {e}"
        finally:
            self.creating = False

    # ── 编辑 ──

    def start_edit(self, nid: int):
        for n in self.notifications:
            if n.get("id") == nid:
                self.edit_id = nid
                self.edit_title = n.get("title", "")
                self.edit_content = n.get("body", "")
                self.edit_category = n.get("category", "announcement")
                self.edit_error = ""
                self.show_create = False
                break

    def cancel_edit(self):
        self.edit_id = 0
        self.edit_error = ""

    def set_edit_title(self, v: str): self.edit_title = v
    def set_edit_content(self, v: str): self.edit_content = v
    def set_edit_category(self, v: str): self.edit_category = v

    def update_notification(self):
        self.edit_error = ""
        self.editing = True
        try:
            body = {
                "title": self.edit_title.strip(),
                "content": self.edit_content.strip(),
                "category": self.edit_category,
            }
            resp = requests.put(
                f"{API_BASE}/api/teacher/notifications/{self.edit_id}",
                json=body, headers=_auth_headers(), timeout=10,
            )
            if resp.status_code == 200:
                self.edit_id = 0
                self.toast_message = "通知已更新"
                self.toast_open = True
                return self.load_notifications()
            elif resp.status_code == 401:
                self.edit_error = "请先以教师身份登录"
            else:
                self.edit_error = resp.json().get("detail", "更新失败")
        except Exception as e:
            self.edit_error = f"更新出错: {e}"
        finally:
            self.editing = False

    # ── 删除 ──

    def confirm_delete(self, n: dict):
        self.delete_target = n
        self.delete_error = ""

    def cancel_delete(self):
        self.delete_target = {}
        self.delete_error = ""

    def delete_notification(self):
        nid = self.delete_target.get("id", 0)
        self.deleting = True
        self.delete_error = ""
        try:
            resp = requests.delete(
                f"{API_BASE}/api/teacher/notifications/{nid}",
                headers=_auth_headers(), timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.delete_target = {}
                self.toast_message = f"已删除 {data.get('deleted_count', 0)} 条通知"
                self.toast_open = True
                return self.load_notifications()
            elif resp.status_code == 401:
                self.delete_error = "请先以教师身份登录"
            else:
                self.delete_error = "删除失败，请重试"
        except Exception as e:
            self.delete_error = f"删除出错: {e}"
        finally:
            self.deleting = False

    def dismiss_toast(self):
        self.toast_open = False


def _auth_headers() -> dict:
    """获取认证请求头"""
    token = os.environ.get("DEV_TEACHER_TOKEN", "")
    if not token:
        token = os.environ.get("DEV_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


# ── UI 组件 ───────────────────────────────────────────────────

def skeleton_row() -> rx.Component:
    """骨架屏行"""
    return rx.card(
        rx.hstack(
            rx.skeleton(width="44px", height="44px", border_radius="12px"),
            rx.vstack(
                rx.skeleton(width="120px", height="16px"),
                rx.skeleton(width="240px", height="20px"),
                rx.skeleton(width="160px", height="14px"),
                spacing="2",
            ),
            rx.hstack(
                rx.skeleton(width="50px", height="28px"),
                rx.skeleton(width="50px", height="28px"),
                spacing="2",
            ),
            spacing="4", justify="between", width="100%", align="center",
        ),
        padding="16px",
    )


def notification_row(n: dict) -> rx.Component:
    """通知行（教师视角）"""
    meta = CATEGORY_META.get(n.get("category", "announcement"), CATEGORY_META["announcement"])
    total_s = n.get("total_students", 0)
    read_c = n.get("read_count", 0)
    nid = n.get("id", 0)

    # 计算已读进度百分比
    progress_pct = (read_c / total_s * 100) if total_s > 0 else 0
    progress_color = "green" if progress_pct >= 80 else ("orange" if progress_pct >= 40 else "red")

    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(meta["icon"], size=20, color=f"{meta['color']}.500"),
                width="44px", height="44px", border_radius="12px",
                bg=f"{meta['color']}.50",
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.hstack(
                    rx.badge(meta["label"], color_scheme=meta["color"], variant="soft", size="1"),
                    rx.badge(
                        f"已读 {read_c}/{total_s}",
                        color_scheme="gray", variant="outline", size="1",
                    ),
                    spacing="2",
                ),
                rx.text(n.get("title", ""), font_weight="bold", font_size="md"),
                rx.cond(
                    n.get("body", ""),
                    rx.text(
                        n.get("body", ""), font_size="sm", color="gray.500",
                        overflow="hidden", white_space="nowrap",
                        text_overflow="ellipsis", max_width="500px",
                    ),
                ),
                rx.hstack(
                    rx.text(n.get("created_at", ""), font_size="xs", color="gray.400"),
                    rx.text(f"发送给 {total_s} 名学生", font_size="xs", color="gray.400"),
                    spacing="3",
                ),
                # 已读进度条
                rx.cond(
                    total_s > 0,
                    rx.hstack(
                        rx.progress(
                            value=progress_pct, width="200px", size="1",
                            color_scheme=progress_color,
                        ),
                        rx.text(f"{progress_pct:.0f}%", font_size="xs", color=f"{progress_color}.500"),
                        spacing="2",
                    ),
                ),
                spacing="1", align="start", flex="1",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14), "编辑",
                    size="1", color_scheme="blue", variant="ghost",
                    on_click=TeacherNotificationsState.start_edit(nid),
                ),
                rx.button(
                    rx.icon("trash-2", size=14), "删除",
                    size="1", color_scheme="red", variant="ghost",
                    on_click=TeacherNotificationsState.confirm_delete(n),
                ),
                spacing="1", flex_shrink="0",
            ),
            spacing="4", width="100%", justify="between", align="start",
        ),
        padding="16px 20px",
        _hover={"shadow": "sm"},
    )


# ── 创建表单 ──

def create_form() -> rx.Component:
    """创建通知表单"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("circle-plus", size=18, color="blue.500"),
                rx.text("发布新通知", font_weight="bold", font_size="md"),
                spacing="2",
            ),
            rx.form(
                rx.vstack(
                    # 标题
                    rx.vstack(
                        rx.text("标题 *", font_size="xs", font_weight="bold", color="gray.500"),
                        rx.input(
                            placeholder="请输入通知标题",
                            value=TeacherNotificationsState.create_title,
                            on_change=TeacherNotificationsState.set_create_title,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    # 内容
                    rx.vstack(
                        rx.text("内容", font_size="xs", font_weight="bold", color="gray.500"),
                        rx.text_area(
                            placeholder="请输入通知正文内容（支持多行文本）",
                            value=TeacherNotificationsState.create_content,
                            on_change=TeacherNotificationsState.set_create_content,
                            width="100%", min_height="120px",
                        ),
                        spacing="1", width="100%",
                    ),
                    # 分类 + 优先级 + 课程
                    rx.hstack(
                        rx.vstack(
                            rx.text("分类", font_size="xs", font_weight="bold", color="gray.500"),
                            rx.select(
                                CATEGORY_OPTIONS,
                                value=TeacherNotificationsState.create_category,
                                on_change=TeacherNotificationsState.set_create_category,
                                width="160px",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("优先级", font_size="xs", font_weight="bold", color="gray.500"),
                            rx.select(
                                PRIORITY_OPTIONS,
                                value=TeacherNotificationsState.create_priority,
                                on_change=TeacherNotificationsState.set_create_priority,
                                width="160px",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("课程 ID（可选）", font_size="xs", font_weight="bold", color="gray.500"),
                            rx.input(
                                placeholder="留空 = 全部学生",
                                value=TeacherNotificationsState.create_course_id.to(str),
                                on_change=TeacherNotificationsState.set_create_course_id,
                                width="160px", type="number",
                            ),
                            spacing="1",
                        ),
                        spacing="4", width="100%", flex_wrap="wrap",
                    ),
                    # 错误提示
                    rx.cond(
                        TeacherNotificationsState.create_error != "",
                        rx.callout(
                            rx.text(TeacherNotificationsState.create_error, font_size="sm"),
                            icon="circle-alert", color_scheme="red", width="100%",
                        ),
                    ),
                    # 成功提示
                    rx.cond(
                        TeacherNotificationsState.create_success != "",
                        rx.callout(
                            rx.text(TeacherNotificationsState.create_success, font_size="sm"),
                            icon="circle-check", color_scheme="green", width="100%",
                        ),
                    ),
                    # 按钮
                    rx.hstack(
                        rx.button(
                            rx.icon("send", size=14), "发布通知",
                            type_="submit", color_scheme="blue",
                            loading=TeacherNotificationsState.creating,
                        ),
                        rx.button(
                            "取消", variant="outline",
                            on_click=TeacherNotificationsState.toggle_create,
                        ),
                        spacing="3",
                    ),
                    spacing="4", width="100%", align="start",
                ),
                on_submit=TeacherNotificationsState.create_notification,
                width="100%",
            ),
            spacing="4", width="100%",
        ),
        variant="classic",
        css={"border": "2px solid var(--blue-400)", "background": "var(--blue-50)"},
        margin_bottom="20px",
    )


# ── 编辑表单 ──

def edit_form() -> rx.Component:
    """编辑通知表单"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("pencil", size=18, color="yellow.600"),
                rx.text("编辑通知", font_weight="bold", font_size="md"),
                spacing="2",
            ),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("标题", font_size="xs", font_weight="bold", color="gray.500"),
                        rx.input(
                            value=TeacherNotificationsState.edit_title,
                            on_change=TeacherNotificationsState.set_edit_title,
                            width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("内容", font_size="xs", font_weight="bold", color="gray.500"),
                        rx.text_area(
                            value=TeacherNotificationsState.edit_content,
                            on_change=TeacherNotificationsState.set_edit_content,
                            width="100%", min_height="100px",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("分类", font_size="xs", font_weight="bold", color="gray.500"),
                        rx.select(
                            CATEGORY_OPTIONS,
                            value=TeacherNotificationsState.edit_category,
                            on_change=TeacherNotificationsState.set_edit_category,
                            width="200px",
                        ),
                        spacing="1",
                    ),
                    rx.cond(
                        TeacherNotificationsState.edit_error != "",
                        rx.callout(
                            rx.text(TeacherNotificationsState.edit_error, font_size="sm"),
                            icon="circle-alert", color_scheme="red", width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            "保存修改", type_="submit", color_scheme="blue",
                            loading=TeacherNotificationsState.editing,
                        ),
                        rx.button(
                            "取消", variant="outline",
                            on_click=TeacherNotificationsState.cancel_edit,
                        ),
                        spacing="3",
                    ),
                    spacing="4", width="100%", align="start",
                ),
                on_submit=TeacherNotificationsState.update_notification,
                width="100%",
            ),
            spacing="4", width="100%",
        ),
        variant="classic",
        css={"border": "2px solid var(--yellow-500)", "background": "var(--yellow-50)"},
        margin_bottom="20px",
    )


# ── 删除确认对话框 ──

def delete_dialog() -> rx.Component:
    """删除确认弹窗"""
    return rx.cond(
        TeacherNotificationsState.show_delete_dialog,
        rx.box(
            # 遮罩
            rx.box(
                position="fixed", top="0", left="0", right="0", bottom="0",
                bg="rgba(0,0,0,0.4)", z_index="100",
                on_click=TeacherNotificationsState.cancel_delete,
            ),
            # 对话框
            rx.card(
                rx.vstack(
                    rx.icon("triangle-alert", size=40, color="red.400"),
                    rx.text("确认删除", font_weight="bold", font_size="lg"),
                    rx.text(
                        f"确定删除通知「{TeacherNotificationsState.delete_title}」吗？",
                        font_size="sm", color="gray.500", text_align="center",
                    ),
                    rx.text(
                        "删除后将同时移除该通知在所有学生中的记录，此操作不可恢复。",
                        font_size="xs", color="red.400", text_align="center",
                    ),
                    rx.cond(
                        TeacherNotificationsState.delete_error != "",
                        rx.text(TeacherNotificationsState.delete_error, color="red.500", font_size="sm"),
                    ),
                    rx.hstack(
                        rx.button(
                            "取消", variant="outline",
                            on_click=TeacherNotificationsState.cancel_delete,
                        ),
                        rx.button(
                            "确认删除", color_scheme="red",
                            loading=TeacherNotificationsState.deleting,
                            on_click=TeacherNotificationsState.delete_notification,
                        ),
                        spacing="4",
                    ),
                    spacing="4", align="center",
                ),
                padding="32px",
                box_shadow="0 20px 60px rgba(0,0,0,0.2)",
                position="fixed", top="50%", left="50%",
                transform="translate(-50%, -50%)",
                z_index="101", max_width="420px", width="90%",
            ),
        ),
    )


# ── 页面主体 ──

def tabs_bar() -> rx.Component:
    """分类标签栏"""
    return rx.hstack(
        rx.tabs.root(
            rx.tabs.list(
                *[rx.tabs.trigger(cfg["label"], value=cat)
                  for cat, cfg in CATEGORY_META.items()],
            ),
            value=TeacherNotificationsState.current_tab,
            on_change=TeacherNotificationsState.switch_tab,
            flex="1",
        ),
        rx.button(
            rx.icon("refresh-cw", size=14),
            variant="ghost", size="2", color_scheme="gray",
            on_click=TeacherNotificationsState.refresh,
        ),
        justify="between", width="100%",
        padding_bottom="12px",
        border_bottom="1px solid var(--gray-200)",
    )


def empty_state() -> rx.Component:
    """空状态"""
    return rx.center(
        rx.vstack(
            rx.icon("megaphone", size=48, color="gray.300"),
            rx.text("暂无通知", color="gray.400", font_size="lg", font_weight="bold"),
            rx.text("点击右上角「发布通知」创建第一条通知",
                    color="gray.300", font_size="sm"),
            spacing="3", padding_y="80px",
        ),
    )


def error_state() -> rx.Component:
    """错误状态"""
    return rx.center(
        rx.vstack(
            rx.icon("triangle-alert", size=48, color="red.300"),
            rx.text(TeacherNotificationsState.error, color="red.400", text_align="center"),
            rx.button(
                rx.icon("refresh-cw", size=14), "重新加载",
                size="2", color_scheme="blue",
                on_click=TeacherNotificationsState.load_notifications,
            ),
            spacing="3", padding_y="80px",
        ),
    )


def loading_state() -> rx.Component:
    """加载骨架屏"""
    return rx.vstack(
        *[skeleton_row() for _ in range(4)],
        spacing="3", width="100%", padding_y="16px",
    )


def pagination_bar() -> rx.Component:
    """分页栏"""
    return rx.cond(
        TeacherNotificationsState.show_pagination,
        rx.hstack(
            rx.button(
                rx.icon("chevron-left", size=14),
                "上一页",
                size="2", variant="outline",
                on_click=TeacherNotificationsState.go_page(TeacherNotificationsState.current_page - 1),
                disabled=~TeacherNotificationsState.can_go_prev,
            ),
            rx.hstack(
                rx.text(f"第 {TeacherNotificationsState.current_page} 页", font_size="sm", color="gray.500"),
                rx.text("·", color="gray.300"),
                rx.text(f"共 {TeacherNotificationsState.total_pages} 页", font_size="sm", color="gray.400"),
                rx.text("·", color="gray.300"),
                rx.text(f"{TeacherNotificationsState.total} 组通知", font_size="sm", color="gray.400"),
                spacing="2",
            ),
            rx.button(
                "下一页",
                rx.icon("chevron-right", size=14),
                size="2", variant="outline",
                on_click=TeacherNotificationsState.go_page(TeacherNotificationsState.current_page + 1),
                disabled=~TeacherNotificationsState.can_go_next,
            ),
            spacing="3", justify="center", width="100%", padding_top="16px",
        ),
    )


def toast_component() -> rx.Component:
    """Toast 提示"""
    return rx.cond(
        TeacherNotificationsState.toast_open,
        rx.box(
            rx.hstack(
                rx.icon("check-circle", size=18, color="green.500"),
                rx.text(TeacherNotificationsState.toast_message, font_size="sm"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=14),
                    variant="ghost", size="1", color_scheme="gray",
                    on_click=TeacherNotificationsState.dismiss_toast,
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


def notifications_teacher_page() -> rx.Component:
    """教师端通知管理页面"""
    return rx.fragment(
        toast_component(),
        rx.container(
            # 删除确认弹窗（独立于主布局）
            delete_dialog(),
            rx.vstack(
                # 页头
                rx.hstack(
                    rx.vstack(
                        rx.heading("📋 通知管理", size="7"),
                        rx.text("发布与管理课程通知公告", color="gray.500", font_size="sm"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=16), "发布通知",
                        color_scheme="blue",
                        on_click=TeacherNotificationsState.toggle_create,
                    ),
                    width="100%",
                ),
                # 创建表单
                rx.cond(TeacherNotificationsState.show_create, create_form()),
                # 编辑表单
                rx.cond(TeacherNotificationsState.is_editing, edit_form()),
                # 标签栏
                tabs_bar(),
                # 内容区
                rx.cond(
                    TeacherNotificationsState.loading,
                    loading_state(),
                    rx.cond(
                        TeacherNotificationsState.error != "",
                        error_state(),
                        rx.cond(
                            ~TeacherNotificationsState.has_data,
                            empty_state(),
                            rx.vstack(
                                rx.foreach(
                                    TeacherNotificationsState.notifications,
                                    notification_row,
                                ),
                                pagination_bar(),
                                spacing="3", width="100%",
                            ),
                        ),
                    ),
                ),
                spacing="6", width="100%",
                padding="24px 32px",
                max_width="1000px",
            ),
            size="4",
            on_mount=TeacherNotificationsState.load_notifications,
        ),
    )
