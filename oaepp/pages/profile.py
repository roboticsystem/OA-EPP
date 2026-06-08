"""
个人资料页面 — student profile (F-S-002).

与 oaepp/app.py 配合（app.py 已注册 route="/profile"）。
使用 ProfileState（继承 rx.State）实现资料查看/编辑和密码修改。
"""

import reflex as rx

try:
    from states.profile import ProfileState
except ImportError:
    from oaepp.states.profile import ProfileState


# ── 辅助：表单字段 ───────────────────────────────────────────────────────

def _field(label: str, value: rx.Var[str], on_change=None, *, placeholder: str = "", disabled: bool = False, type_: str = "text") -> rx.Component:
    props = dict(value=value, placeholder=placeholder, disabled=disabled, type_=type_, width="100%")
    if on_change is not None and not disabled:
        props["on_change"] = on_change
    return rx.box(
        rx.text(label, font_size="12px", font_weight="500", color="#6b7280", margin_bottom="4px"),
        rx.input(**props),
    )


# ── 个人资料卡片 ─────────────────────────────────────────────────────────

def _profile_card() -> rx.Component:
    return rx.box(
        # 头像行
        rx.hstack(
            rx.box(
                rx.text(ProfileState.display_name_initial, font_weight="bold", font_size="24px", color="#1d4ed8"),
                width="64px", height="64px", border_radius="50%", bg="#dbeafe",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.box(
                rx.heading(ProfileState.username, size="5", color="#1f2937"),
                rx.text(ProfileState.student_class, font_size="14px", color="#9ca3af"),
            ),
            gap="5", align="center", margin_bottom="24px",
        ),
        # 表单 2 列
        rx.hstack(
            rx.vstack(
                _field("姓名", ProfileState.edit_username, ProfileState.set_edit_username, placeholder="请输入姓名"),
                _field("邮箱", ProfileState.edit_email, ProfileState.set_edit_email, placeholder="请输入邮箱"),
                spacing="4", flex="1",
            ),
            rx.vstack(
                _field("班级", ProfileState.edit_class, ProfileState.set_edit_class, placeholder="请输入班级"),
                _field("手机号", ProfileState.edit_phone, ProfileState.set_edit_phone, placeholder="请输入手机号"),
                spacing="4", flex="1",
            ),
            gap="5",
        ),
        # 个人简介（全宽）
        rx.box(height="16px"),
        _field("个人简介", ProfileState.edit_bio, ProfileState.set_edit_bio, placeholder="一句话介绍自己"),

        # 状态消息
        rx.cond(ProfileState.profile_message != "", rx.text(ProfileState.profile_message, color="#16a34a", font_size="13px", margin_top="12px")),
        rx.cond(ProfileState.profile_error != "", rx.text(ProfileState.profile_error, color="#dc2626", font_size="13px", margin_top="12px")),

        # 保存按钮
        rx.hstack(
            rx.button("保存修改", on_click=ProfileState.save_profile, color_scheme="blue", size="2",
                       disabled=~ProfileState.profile_has_changes),
            justify="end", margin_top="20px",
        ),
        bg="white", border_radius="12px", border="1px solid #f3f4f6",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)", padding="24px", margin_bottom="24px",
    )


# ── 密码修改卡片 ─────────────────────────────────────────────────────────

def _password_card() -> rx.Component:
    return rx.box(
        rx.text("修改密码", font_weight="600", font_size="14px", color="#374151", margin_bottom="16px"),
        _field("当前密码", ProfileState.old_password, ProfileState.set_old_password, placeholder="请输入当前密码", type_="password"),
        rx.box(height="16px"),
        _field("新密码", ProfileState.new_password, ProfileState.set_new_password, placeholder="至少 8 位", type_="password"),
        rx.box(height="16px"),
        _field("确认新密码", ProfileState.confirm_password, ProfileState.set_confirm_password, placeholder="再次输入新密码", type_="password"),
        rx.cond(ProfileState.password_message != "", rx.text(ProfileState.password_message, color="#16a34a", font_size="13px", margin_top="12px")),
        rx.cond(ProfileState.password_error != "", rx.text(ProfileState.password_error, color="#dc2626", font_size="13px", margin_top="12px")),
        rx.button("确认修改密码", on_click=ProfileState.change_password, color_scheme="blue", size="2", margin_top="16px"),
        bg="white", border_radius="12px", border="1px solid #f3f4f6",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)", padding="24px", max_width="400px",
    )


# ── 页面导出 — app.py 已注册为 route="/profile" ─────────────────────────

def profile_page() -> rx.Component:
    return rx.box(
        # 页面标题
        rx.box(
            rx.heading("个人资料", size="6", color="#1f2937"),
            rx.text("管理账号信息与密码修改", font_size="14px", color="#9ca3af", margin_top="2px"),
            margin_bottom="24px",
        ),
        _profile_card(),
        _password_card(),
        padding="32px", max_width="720px", margin="0 auto",
        min_height="100vh", bg="#f9fafb",
        on_mount=ProfileState.load_profile,
    )
