"""
ProfileState — Reflex state for the student profile page (F-S-002).

Inherits from GlobalState for shared app state (current_user, toast, etc.).
All vars are automatically synced with the frontend.
Event handlers call the database module directly (no HTTP round-trip needed).
"""

import reflex as rx

try:
    from states import GlobalState
except ImportError:
    from oaepp.states import GlobalState

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


class ProfileState(GlobalState if GlobalState is not None else rx.State):
    """State for viewing / editing student profile and changing password."""

    # ── User identity (data isolation) ──
    current_user_id: int = 1

    # ── Profile data ──
    username: str = ""        # student_no
    student_no: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    student_class: str = ""   # alias for class_name
    class_name: str = ""
    bio: str = ""

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
    error_message: str = ""   # generic error (used by tests)

    @rx.var(cache=False)
    def display_name_initial(self) -> str:
        """First character of full_name (or '?') for the avatar circle."""
        name = self.full_name or self.edit_name
        return name[0] if name else "?"

    @rx.var(cache=False)
    def profile_subtitle(self) -> str:
        """Subtitle line e.g. '学号:2021001001 · 班:工程实践班A'."""
        parts = []
        sid = self.student_no or self.username
        cls = self.class_name or self.student_class
        if sid:
            parts.append(f"学号：{sid}")
        if cls:
            parts.append(f"班级：{cls}")
        return " · ".join(parts) if parts else "未加载"

    @rx.var(cache=False)
    def profile_has_changes(self) -> bool:
        """True when any editable field differs from the persisted value."""
        return (
            self.edit_name != self.full_name
            or self.edit_email != self.email
            or self.edit_phone != self.phone
            or self.edit_class != (self.class_name or self.student_class)
        )

    # ── Event handlers ────────────────────────────────────────────────

    async def load_profile(self):
        """Load student profile from the database (called on page mount)."""
        self.reset()
        self.is_loading = True
        try:
            profile = get_student_profile(self.current_user_id)
            if profile:
                self.student_no = profile["student_no"] or ""
                self.username = self.student_no
                self.full_name = profile["full_name"] or ""
                self.email = profile["email"] or ""
                self.class_name = profile["class_name"] or ""
                self.student_class = self.class_name
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

    async def update_profile(self):
        """Persist editable fields to the database (test-compatible name)."""
        self.profile_message = ""
        self.profile_error = ""
        self.error_message = ""
        try:
            update_student_profile(
                student_id=self.current_user_id,
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
            self.student_class = self.edit_class
            self.profile_message = "✅ 个人资料已保存"
        except Exception as e:
            msg = f"保存失败：{e}"
            self.profile_error = msg
            self.error_message = msg

    async def save_profile(self):
        """Alias for update_profile (Reflex UI event handler)."""
        await self.update_profile()

    async def change_password(self, old_pw: str = "", new_pw: str = "", confirm_pw: str = ""):
        """Validate old password, then set new password.

        Accepts optional arguments for testability:
          change_password("old", "new", "new")
        When called without args (from Reflex UI), uses form state vars.
        """
        # Resolve inputs: args take priority, fall back to form fields
        _old = old_pw or self.old_password
        _new = new_pw or self.new_password
        _confirm = confirm_pw or self.confirm_password

        self.password_message = ""
        self.password_error = ""
        self.error_message = ""

        # Client-side validation
        if len(_new) < 8:
            msg = "新密码至少需要 8 位"
            self.password_error = msg
            self.error_message = msg
            return
        if _new != _confirm:
            msg = "两次输入的新密码不一致"
            self.password_error = msg
            self.error_message = msg
            return
        if _old == _new:
            msg = "新密码不能与旧密码相同"
            self.password_error = msg
            self.error_message = msg
            return

        try:
            if not verify_password(self.current_user_id, _old):
                msg = "当前密码不正确"
                self.password_error = msg
                self.error_message = msg
                return
        except Exception as e:
            msg = f"验证失败：{e}"
            self.password_error = msg
            self.error_message = msg
            return

        from werkzeug.security import generate_password_hash

        try:
            new_hash = generate_password_hash(_new)
            update_password(self.current_user_id, new_hash)
            self.password_message = "✅ 密码修改成功"
            # Clear password fields
            self.old_password = ""
            self.new_password = ""
            self.confirm_password = ""
        except Exception as e:
            msg = f"修改失败：{e}"
            self.password_error = msg
            self.error_message = msg

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
