"""
ProfileState — Reflex state for the student profile page (F-S-002).

All vars are automatically synced with the frontend.
Event handlers call the database module directly (no HTTP round-trip needed).
"""

import reflex as rx

try:
    from models.database import (
        get_student_profile,
        update_student_profile,
        verify_password,
        update_password,
    )
except ImportError:
    from oaepp.models.database import (
        get_student_profile,
        update_student_profile,
        verify_password,
        update_password,
    )


class ProfileState(rx.State):
    """State for viewing / editing student profile and changing password."""

    # ── Simulated auth (until login is built) ──
    current_student_id: int = 1

    # ── Profile data loaded from DB (display values) ──
    student_no: str = ""
    full_name: str = ""
    email: str = ""
    class_name: str = ""
    phone: str = ""

    # ── Editable form fields (two-way bound to inputs) ──
    edit_name: str = ""
    edit_email: str = ""
    edit_phone: str = ""
    edit_class: str = ""

    # ── Password change fields ──
    old_password: str = ""
    new_password: str = ""
    confirm_password: str = ""

    # ── UI feedback ──
    profile_message: str = ""
    profile_error: str = ""
    password_message: str = ""
    password_error: str = ""
    is_loading: bool = False

    @rx.var(cache=False)
    def display_name_initial(self) -> str:
        """First character of full_name (or '?') for the avatar circle."""
        name = self.full_name or self.edit_name
        return name[0] if name else "?"

    @rx.var(cache=False)
    def profile_subtitle(self) -> str:
        """Subtitle line e.g. '学号:2021001001 · 班:工程实践班A'."""
        parts = []
        if self.student_no:
            parts.append(f"学号：{self.student_no}")
        if self.class_name:
            parts.append(f"班级：{self.class_name}")
        return " · ".join(parts) if parts else "未加载"

    @rx.var(cache=False)
    def profile_has_changes(self) -> bool:
        """True when any editable field differs from the persisted value."""
        return (
            self.edit_name != self.full_name
            or self.edit_email != self.email
            or self.edit_phone != self.phone
            or self.edit_class != self.class_name
        )

    # ── Event handlers ────────────────────────────────────────────────

    async def load_profile(self):
        """Load student profile from the database (called on page mount)."""
        self.reset()
        self.is_loading = True
        try:
            profile = get_student_profile(self.current_student_id)
            if profile:
                self.student_no = profile["student_no"] or ""
                self.full_name = profile["full_name"] or ""
                self.email = profile["email"] or ""
                self.class_name = profile["class_name"] or ""
                self.phone = profile["phone"] or ""
                # Populate editable fields
                self.edit_name = self.full_name
                self.edit_email = self.email
                self.edit_phone = self.phone
                self.edit_class = self.class_name
            else:
                self.profile_error = "无法加载个人资料，请确认已登录"
        except Exception as e:
            self.profile_error = f"加载失败：{e}"
        finally:
            self.is_loading = False

    async def save_profile(self):
        """Persist editable fields to the database."""
        self.profile_message = ""
        self.profile_error = ""
        try:
            update_student_profile(
                student_id=self.current_student_id,
                full_name=self.edit_name,
                email=self.edit_email,
                class_name=self.edit_class,
                phone=self.edit_phone,
            )
            # Sync display fields so UI updates instantly
            self.full_name = self.edit_name
            self.email = self.edit_email
            self.phone = self.edit_phone
            self.class_name = self.edit_class
            self.profile_message = "✅ 个人资料已保存"
        except Exception as e:
            self.profile_error = f"保存失败：{e}"

    async def change_password(self):
        """Validate old password, then set new password."""
        self.password_message = ""
        self.password_error = ""

        # Client-side validation
        if len(self.new_password) < 8:
            self.password_error = "新密码至少需要 8 位"
            return
        if self.new_password != self.confirm_password:
            self.password_error = "两次输入的新密码不一致"
            return

        try:
            if not verify_password(self.current_student_id, self.old_password):
                self.password_error = "当前密码不正确"
                return
        except Exception as e:
            self.password_error = f"验证失败：{e}"
            return

        from werkzeug.security import generate_password_hash

        try:
            new_hash = generate_password_hash(self.new_password)
            update_password(self.current_student_id, new_hash)
            self.password_message = "✅ 密码修改成功"
            # Clear password fields
            self.old_password = ""
            self.new_password = ""
            self.confirm_password = ""
        except Exception as e:
            self.password_error = f"修改失败：{e}"

    # ── Input change handlers (called by on_change on each field) ─────

    async def set_edit_name(self, value: str):
        self.edit_name = value

    async def set_edit_email(self, value: str):
        self.edit_email = value

    async def set_edit_phone(self, value: str):
        self.edit_phone = value

    async def set_edit_class(self, value: str):
        self.edit_class = value

    async def set_old_password(self, value: str):
        self.old_password = value

    async def set_new_password(self, value: str):
        self.new_password = value

    async def set_confirm_password(self, value: str):
        self.confirm_password = value
