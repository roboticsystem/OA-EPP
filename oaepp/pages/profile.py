"""
Profile page component — student personal profile (F-S-002).

Translates prototype/profile.html into Reflex Python components.
Uses ProfileState for two-way data binding.
"""

import reflex as rx

try:
    from states.profile import ProfileState
except ImportError:
    from oaepp.states.profile import ProfileState


# ── Sidebar ──────────────────────────────────────────────────────────────

def _sidebar() -> rx.Component:
    """Left sidebar with nav links and user info."""
    nav_items = [
        ("/dashboard", "📋 仪表盘"),
        ("/courses", "📚 课程列表"),
        ("/assignments", "📝 作业提交"),
        ("/grades", "📈 成绩与反馈"),
        ("/attendance", "✅ 课堂签到"),
        ("/exam", "✏️ 在线考试"),
        ("/profile", "👤 个人资料"),
    ]

    def _nav_link(href: str, label: str):
        is_active = href == "/profile"
        return rx.link(
            rx.text(label, font_size="14px"),
            href=href,
            padding="8px 12px",
            border_radius="8px",
            color=rx.cond(is_active, "#1d4ed8", "#4b5563"),
            bg=rx.cond(is_active, "#eff6ff", "transparent"),
            font_weight=rx.cond(is_active, "500", "400"),
            _hover={"bg": "#f9fafb"},
            width="100%",
        )

    return rx.box(
        # Logo area
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text("OA", font_weight="bold", font_size="12px", color="white"),
                    width="32px",
                    height="32px",
                    bg="#2563eb",
                    border_radius="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text("OA-EPP", font_weight="bold", font_size="14px", color="#1f2937"),
                gap="2",
                align="center",
            ),
            padding="20px",
            border_bottom="1px solid #f3f4f6",
        ),
        # Nav links
        rx.box(
            *[_nav_link(href, label) for href, label in nav_items],
            padding="12px",
            flex="1",
        ),
        # User footer
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text(ProfileState.display_name_initial, font_weight="bold", font_size="14px", color="#1d4ed8"),
                    width="32px",
                    height="32px",
                    border_radius="50%",
                    bg="#dbeafe",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.box(
                    rx.text(ProfileState.full_name, font_size="14px", font_weight="500", color="#1f2937"),
                    rx.text(ProfileState.student_no, font_size="12px", color="#9ca3af"),
                ),
                gap="3",
                align="center",
            ),
            rx.link("退出登录", href="/", font_size="12px", color="#9ca3af", _hover={"color": "#ef4444"}, margin_top="12px", display="block", text_align="center"),
            padding="16px",
            border_top="1px solid #f3f4f6",
        ),
        width="224px",
        bg="white",
        border_right="1px solid #e5e7eb",
        min_height="100vh",
        position="fixed",
        left="0",
        top="0",
        display="flex",
        flex_direction="column",
    )


# ── Form field helper ────────────────────────────────────────────────────

def _field(label: str, value: rx.Var[str], on_change=None, *, placeholder: str = "", disabled: bool = False, type_: str = "text") -> rx.Component:
    """Reusable form field: label + input."""
    props = dict(
        value=value,
        placeholder=placeholder,
        disabled=disabled,
        type_=type_,
        width="100%",
        variant="surface" if not disabled else "soft",
    )
    if on_change is not None and not disabled:
        props["on_change"] = on_change
    return rx.box(
        rx.text(label, font_size="12px", font_weight="500", color="#6b7280", margin_bottom="4px"),
        rx.input(**props),
    )


# ── Profile card ─────────────────────────────────────────────────────────

def _profile_card() -> rx.Component:
    return rx.box(
        # Avatar + name row
        rx.hstack(
            rx.box(
                rx.text(ProfileState.display_name_initial, font_weight="bold", font_size="24px", color="#1d4ed8"),
                width="64px",
                height="64px",
                border_radius="50%",
                bg="#dbeafe",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.box(
                rx.heading(ProfileState.full_name, size="5", color="#1f2937"),
                rx.text(ProfileState.profile_subtitle, font_size="14px", color="#9ca3af"),
            ),
            gap="5",
            align="center",
            margin_bottom="24px",
        ),
        # Form layout (2 cols)
        rx.box(
            rx.hstack(
                rx.vstack(
                    _field("姓名", ProfileState.edit_name, ProfileState.set_edit_name, placeholder="请输入姓名"),
                    _field("邮箱", ProfileState.edit_email, ProfileState.set_edit_email, placeholder="请输入邮箱"),
                    spacing="4",
                    flex="1",
                ),
                rx.vstack(
                    _field("学号（只读）", ProfileState.student_no, disabled=True),
                    _field("班级", ProfileState.edit_class, ProfileState.set_edit_class, placeholder="请输入班级"),
                    spacing="4",
                    flex="1",
                ),
                gap="5",
            ),
            margin_bottom="4",
        ),
        # Status messages
        rx.cond(
            ProfileState.profile_message != "",
            rx.text(ProfileState.profile_message, color="#16a34a", font_size="13px", margin_top="12px"),
        ),
        rx.cond(
            ProfileState.profile_error != "",
            rx.text(ProfileState.profile_error, color="#dc2626", font_size="13px", margin_top="12px"),
        ),
        # Save button
        rx.hstack(
            rx.button(
                "保存修改",
                on_click=ProfileState.save_profile,
                color_scheme="blue",
                size="2",
                disabled=~ProfileState.profile_has_changes,
            ),
            justify="end",
            margin_top="20px",
        ),
        bg="white",
        border_radius="12px",
        border="1px solid #f3f4f6",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)",
        padding="24px",
        margin_bottom="24px",
    )


# ── GitHub binding card (placeholder) ───────────────────────────────────

def _github_card() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text("🔗 GitHub 账号绑定", font_weight="600", font_size="14px", color="#374151"),
            rx.badge("即将开放", color_scheme="gray", variant="soft"),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="16px",
        ),
        rx.input(placeholder="GitHub 用户名", disabled=True, width="100%", variant="soft"),
        rx.text("绑定功能即将开放，敬请期待。", font_size="12px", color="#9ca3af", margin_top="8px"),
        rx.box(
            rx.text("绑定功能将在后续版本中开放，届时您可以在此绑定 GitHub 账号。", font_size="12px", color="#a16207"),
            margin_top="12px",
            bg="#fef9c3",
            border="1px solid #fde68a",
            border_radius="8px",
            padding="12px 16px",
        ),
        bg="white",
        border_radius="12px",
        border="1px solid #f3f4f6",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)",
        padding="24px",
        margin_bottom="24px",
    )


# ── Password change card ─────────────────────────────────────────────────

def _password_card() -> rx.Component:
    return rx.box(
        rx.text("修改密码", font_weight="600", font_size="14px", color="#374151", margin_bottom="16px"),
        _field("当前密码", ProfileState.old_password, ProfileState.set_old_password, placeholder="请输入当前密码", type_="password"),
        rx.box(height="16px"),
        _field("新密码", ProfileState.new_password, ProfileState.set_new_password, placeholder="至少 8 位", type_="password"),
        rx.box(height="16px"),
        _field("确认新密码", ProfileState.confirm_password, ProfileState.set_confirm_password, placeholder="再次输入新密码", type_="password"),
        # Status
        rx.cond(
            ProfileState.password_message != "",
            rx.text(ProfileState.password_message, color="#16a34a", font_size="13px", margin_top="12px"),
        ),
        rx.cond(
            ProfileState.password_error != "",
            rx.text(ProfileState.password_error, color="#dc2626", font_size="13px", margin_top="12px"),
        ),
        rx.button(
            "确认修改密码",
            on_click=ProfileState.change_password,
            color_scheme="blue",
            size="2",
            margin_top="16px",
        ),
        bg="white",
        border_radius="12px",
        border="1px solid #f3f4f6",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)",
        padding="24px",
        max_width="400px",
    )


# ── Page export ──────────────────────────────────────────────────────────

def profile_page() -> rx.Component:
    """Student profile page — view / edit info and change password."""
    return rx.flex(
        _sidebar(),
        rx.box(
            rx.box(
                rx.heading("个人资料", size="6", color="#1f2937"),
                rx.text("管理账号信息与密码修改", font_size="14px", color="#9ca3af", margin_top="2px"),
                margin_bottom="24px",
            ),
            _profile_card(),
            _github_card(),
            _password_card(),
            margin_left="224px",
            flex="1",
            padding="32px",
            max_width="896px",
        ),
        min_height="100vh",
        bg="#f9fafb",
        on_mount=ProfileState.load_profile,
    )
