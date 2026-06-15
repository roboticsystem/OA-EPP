"""F-S-012 公告通知 — NoticeState

提供公告通知的完整状态管理（学生端 + 教师端），所有数据操作通过
Reflex ORM（rx.session() + SQLModel）直连 MySQL。

学生端功能：
  - 分类标签页筛选、分页加载
  - 标记单条已读 / 一键全部已读
  - 未读计数、骨架屏、空状态、错误处理

教师端功能：
  - 通知列表（分页 + 分类筛选）
  - 创建通知（标题/内容/分类/优先级）
  - 编辑通知（内联编辑）
  - 删除通知（单条 + 同组批量）

依赖：
  - oaepp.models: Notification, User（ORM 模型）
  - oaepp.states: GlobalState（继承基类）
"""

from __future__ import annotations
from typing import Optional
import reflex as rx
from sqlmodel import select, func

try:
    from oaepp.models import Notification, User
except ModuleNotFoundError:
    from models import Notification, User

try:
    from oaepp.states import GlobalState
except ModuleNotFoundError:
    try:
        from states import GlobalState
    except ModuleNotFoundError:
        GlobalState = rx.State

# ── 分类常量 ──
VALID_CATEGORIES = ("announcement", "deadline", "grade", "system", "graded")


# ═══════════════════════════════════════════════════════════════
# NoticeState — 统一的公告通知状态（继承 GlobalState）
# ═══════════════════════════════════════════════════════════════

class NoticeState(GlobalState):
    """公告通知状态管理 — 学生端 + 教师端共用"""

    # ── 学生端状态变量 ──
    notices: list[dict] = []
    unread_count: int = 0
    category_counts: dict = {}

    # ── 学生端筛选 & 分页 ──
    current_tab: str = "all"
    current_page: int = 1
    page_size: int = 12
    total: int = 0
    total_pages: int = 1

    # ── 学生端 UI 状态 ──
    loading: bool = True
    error: str = ""

    # ── 教师端创建表单 ──
    show_create: bool = False
    create_title: str = ""
    create_content: str = ""
    create_category: str = "announcement"
    create_priority: str = "normal"
    create_course_id: int = 0
    creating: bool = False
    create_error: str = ""
    create_success: str = ""

    # ── 教师端编辑 ──
    edit_id: int = 0
    edit_title: str = ""
    edit_content: str = ""
    edit_category: str = "announcement"
    editing: bool = False
    edit_error: str = ""

    # ── 教师端删除确认 ──
    delete_target: dict = {}
    deleting: bool = False
    delete_error: str = ""

    # ═══════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════

    def _get_user_id(self) -> int:
        """从 current_user 获取用户 ID"""
        user_id = 0
        if self.current_user:
            user_id = self.current_user.get("id", 0)
            if not user_id:
                user_id = self.current_user.get("user_id", 0)
        return user_id

    @staticmethod
    def _notif_to_dict(n: Notification) -> dict:
        """将 ORM 对象转为前端 dict"""
        return {
            "id": n.id,
            "user_id": n.user_id,
            "title": n.title,
            "content": n.body or "",
            "category": n.category,
            "is_read": bool(n.is_read),
            "created_at": str(n.created_at) if n.created_at else "",
        }

    # ═══════════════════════════════════════════════════════════
    # 计算属性
    # ═══════════════════════════════════════════════════════════

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

    @rx.var
    def unread_badge_text(self) -> str:
        if self.unread_count == 0:
            return ""
        return f"{self.unread_count} 条未读" if self.unread_count <= 99 else "99+ 条未读"

    @rx.var
    def is_editing(self) -> bool:
        return self.edit_id > 0

    @rx.var
    def show_delete_dialog(self) -> bool:
        return bool(self.delete_target)

    @rx.var
    def delete_title(self) -> str:
        return self.delete_target.get("title", "") if self.delete_target else ""

    # ═══════════════════════════════════════════════════════════
    # 学生端 — 列表加载
    # ═══════════════════════════════════════════════════════════

    def switch_tab(self, tab: str):
        """切换分类标签（学生端）"""
        if tab == self.current_tab:
            return
        self.current_tab = tab
        self.current_page = 1
        return self.load_notices()

    def go_page(self, page: int):
        """跳转页码（学生端）"""
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return
        self.current_page = page
        return self.load_notices()

    def refresh(self):
        """手动刷新"""
        return self.load_notices()

    def load_notices(self):
        """从数据库加载通知列表（学生端视图，带分类筛选和分页）"""
        self.loading = True
        self.error = ""
        try:
            user_id = self._get_user_id()

            with rx.session() as session:
                # 构建查询
                stmt = select(Notification)
                if user_id:
                    stmt = stmt.where(Notification.user_id == user_id)
                if self.current_tab == "unread":
                    stmt = stmt.where(Notification.is_read == False)  # noqa: E712
                elif self.current_tab != "all":
                    stmt = stmt.where(Notification.category == self.current_tab)

                # 查询总数
                count_stmt = select(func.count()).select_from(stmt.subquery())
                self.total = session.exec(count_stmt).one()

                # 查询分页数据
                offset = (self.current_page - 1) * self.page_size
                stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(self.page_size)
                rows = session.exec(stmt).all()

                # 查询未读计数
                if user_id:
                    unread_stmt = (
                        select(func.count())
                        .where(Notification.user_id == user_id)
                        .where(Notification.is_read == False)  # noqa: E712
                    )
                    self.unread_count = session.exec(unread_stmt).one()
                else:
                    self.unread_count = 0

                # 查询各分类计数
                if user_id:
                    cat_rows = session.exec(
                        select(Notification.category, func.count())
                        .where(Notification.user_id == user_id)
                        .group_by(Notification.category)
                    ).all()
                    self.category_counts = {cat: cnt for cat, cnt in cat_rows}
                else:
                    self.category_counts = {}

            # 格式化数据
            self.notices = [self._notif_to_dict(n) for n in rows]
            self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)

        except Exception as e:
            self.error = f"加载失败: {e}"
            self.notices = []
        finally:
            self.loading = False

    # ═══════════════════════════════════════════════════════════
    # 学生端 — 标记已读
    # ═══════════════════════════════════════════════════════════

    def mark_as_read(self, nid: int):
        """标记单条通知已读（仅标记当前用户自己的通知）"""
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
                    # 更新本地状态
                    for n in self.notices:
                        if n.get("id") == nid:
                            n["is_read"] = True
                            break
                    self.unread_count = max(0, self.unread_count - 1)
            return rx.toast.success("已标记为已读")
        except Exception:
            return rx.toast.error("操作失败，请重试")

    def mark_all_read(self):
        """一键全部已读"""
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

    # ═══════════════════════════════════════════════════════════
    # 教师端 — 列表加载（按 title+category 分组）
    # ═══════════════════════════════════════════════════════════

    def switch_tab_teacher(self, tab: str):
        """切换分类标签（教师端）"""
        if tab == self.current_tab:
            return
        self.current_tab = tab
        self.current_page = 1
        return self.load_teacher_notices()

    def go_page_teacher(self, page: int):
        """跳转页码（教师端）"""
        page = max(1, min(page, self.total_pages))
        if page == self.current_page:
            return
        self.current_page = page
        return self.load_teacher_notices()

    def load_teacher_notices(self):
        """从数据库加载通知列表（教师端视图，按 title+category 分组）"""
        self.loading = True
        self.error = ""
        try:
            with rx.session() as session:
                # 构建分组查询
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

                # 先查总数
                count_stmt = select(func.count()).select_from(stmt.subquery())
                self.total = session.exec(count_stmt).one()

                # 分页
                offset = (self.current_page - 1) * self.page_size
                rows = session.exec(stmt.offset(offset).limit(self.page_size)).all()

            self.notices = []
            for row in rows:
                created_at = ""
                if row.created_at:
                    created_at = str(row.created_at)
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
        finally:
            self.loading = False

    # ═══════════════════════════════════════════════════════════
    # 教师端 — 创建通知
    # ═══════════════════════════════════════════════════════════

    def toggle_create(self):
        self.show_create = not self.show_create
        if not self.show_create:
            self._reset_create_form()

    def _reset_create_form(self):
        self.create_title = ""
        self.create_content = ""
        self.create_category = "announcement"
        self.create_priority = "normal"
        self.create_course_id = 0
        self.create_error = ""
        self.create_success = ""
        self.creating = False

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
        """创建通知 — 为所有学生各写入一条 Notification 记录"""
        self.create_error = ""
        self.create_success = ""
        title = self.create_title.strip()
        if not title:
            self.create_error = "请输入通知标题"
            return

        self.creating = True
        try:
            with rx.session() as session:
                # 获取所有学生 user_id
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
                        title=title,
                        body=body,
                        category=category,
                        user_id=uid,
                        is_read=False,
                    )
                    for uid in students
                ]
                session.add_all(notifs)
                session.commit()

            self.create_success = f"通知已发布，已发送给 {len(students)} 名学生"
            self._reset_create_form()
            self.show_create = False
            self.current_page = 1
            self.load_teacher_notices()
            return rx.toast.success(f"通知「{title}」已发布给 {len(students)} 名学生")

        except Exception as e:
            self.create_error = f"创建失败: {e}"
            self.creating = False

    # ═══════════════════════════════════════════════════════════
    # 教师端 — 编辑通知
    # ═══════════════════════════════════════════════════════════

    def start_edit(self, nid: int):
        """进入编辑模式 — 从当前通知列表获取数据"""
        for n in self.notices:
            if n.get("id") == nid:
                self.edit_id = nid
                self.edit_title = n.get("title", "")
                self.edit_content = n.get("content", "")
                self.edit_category = n.get("category", "announcement")
                self.edit_error = ""
                self.show_create = False
                return
        # 如果列表中没有，从数据库加载
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
                    self.show_create = False
        except Exception:
            pass

    def cancel_edit(self):
        self.edit_id = 0
        self.edit_error = ""

    def set_edit_title(self, v: str): self.edit_title = v
    def set_edit_content(self, v: str): self.edit_content = v
    def set_edit_category(self, v: str): self.edit_category = v

    def update_notification(self):
        """更新通知 — 按 title+category 批量更新同组通知"""
        self.edit_error = ""
        new_title = self.edit_title.strip()
        if not new_title:
            self.edit_error = "标题不能为空"
            return

        self.editing = True
        try:
            with rx.session() as session:
                # 先获取原始 title 和 category
                notif = session.exec(
                    select(Notification).where(Notification.id == self.edit_id)
                ).first()
                if not notif:
                    self.edit_error = "通知不存在"
                    self.editing = False
                    return
                old_title = notif.title
                old_category = notif.category

                # 按 title+category 批量更新同组
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
            self.load_teacher_notices()
            return rx.toast.success(f"已更新 {updated_count} 条通知")

        except Exception as e:
            self.edit_error = f"更新失败: {e}"
            self.editing = False

    # ═══════════════════════════════════════════════════════════
    # 教师端 — 删除通知
    # ═══════════════════════════════════════════════════════════

    def confirm_delete(self, n: dict):
        self.delete_target = n
        self.delete_error = ""

    def cancel_delete(self):
        self.delete_target = {}
        self.delete_error = ""

    def delete_notification(self):
        """删除通知 — 按 title+category 批量删除同组"""
        title = self.delete_target.get("title", "")
        category = self.delete_target.get("category", "")
        if not title:
            self.delete_error = "通知不存在"
            self.delete_target = {}
            return

        self.deleting = True
        self.delete_error = ""
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
            self.load_teacher_notices()
            return rx.toast.success(f"已删除 {deleted_count} 条通知")

        except Exception as e:
            self.delete_error = f"删除失败: {e}"
            self.deleting = False
