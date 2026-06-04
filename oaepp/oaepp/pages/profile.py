import reflex as rx
from ..mock_data import MockData


def _input_field(label: str, value: str, disabled: bool = False) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="0.75rem", font_weight="500",
                color="#6b7280", margin_bottom="0.25rem"),
        rx.el.input(
            value=value,
            disabled=disabled,
            class_name=(
                "w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none "
                + ("border-gray-200 text-gray-800 focus:ring-2 focus:ring-blue-400"
                   if not disabled else
                   "border-gray-100 bg-gray-50 text-gray-500 cursor-not-allowed")
            ),
        ),
    )


def _password_input(placeholder: str) -> rx.Component:
    return rx.el.input(
        type_="password",
        placeholder=placeholder,
        class_name=(
            "w-full border border-gray-200 rounded-lg px-3 py-2.5 "
            "text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        ),
    )


def profile_page() -> rx.Component:
    from ..components.layout import protected_page
    p = MockData.PROFILE
    gh = MockData.GITHUB_BINDING
    body = rx.vstack(
        # Header
        rx.box(
            rx.text("个人资料", font_size="1.25rem",
                    font_weight="bold", color="#1f2937"),
            rx.text("管理账号信息与 GitHub 绑定",
                    font_size="0.875rem", color="#9ca3af",
                    margin_top="0.125rem"),
            margin_bottom="1.5rem",
            width="100%",
        ),
        # Profile card
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text(p["avatar_char"], font_size="1.5rem",
                            font_weight="bold", color="#1d4ed8"),
                    width="4rem", height="4rem",
                    border_radius="9999px", bg="#dbeafe",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text(p["name"], font_size="1.125rem",
                            font_weight="bold", color="#1f2937"),
                    rx.text(f"学号：{p['student_id']} · 班级：{p['class_name']}",
                            font_size="0.875rem", color="#9ca3af"),
                    gap="0",
                    align="start",
                ),
                gap="1.25rem",
                align="center",
                margin_bottom="1.5rem",
            ),
            rx.grid(
                _input_field("姓名", p["name"]),
                _input_field("学号（只读）", p["student_id"], disabled=True),
                _input_field("邮箱", p["email"]),
                _input_field("班级", p["class_name"], disabled=True),
                grid_template_columns="repeat(2, 1fr)",
                gap="1.25rem",
                margin_bottom="1.25rem",
            ),
            rx.hstack(
                rx.el.button("保存修改",
                    class_name="bg-blue-600 hover:bg-blue-700 text-white text-sm px-5 py-2 rounded-lg transition"),
                justify="end",
            ),
            class_name="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6",
            width="100%",
        ),
        # GitHub binding
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.html(
                        '<svg class="w-6 h-6 text-gray-700" fill="currentColor" viewBox="0 0 24 24">'
                        '<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111'
                        '.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387'
                        '-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 '
                        '1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604'
                        '-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303'
                        '-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404'
                        '1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 '
                        '2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 '
                        '5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 '
                        '8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>'
                    ),
                    rx.text("GitHub 账号绑定", font_size="0.875rem",
                            font_weight="600", color="#374151"),
                    gap="0.75rem",
                    align="center",
                ),
                _status_badge("已绑定 · 审核通过", "green"),
                justify="between",
                align="center",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text("GitHub 用户名", font_size="0.75rem",
                        font_weight="500", color="#6b7280",
                        margin_bottom="0.25rem"),
                rx.hstack(
                    rx.el.input(value=gh["username"], disabled=True,
                        class_name="flex-1 border border-gray-100 bg-gray-50 rounded-lg px-3 py-2.5 text-sm text-gray-600 cursor-not-allowed"),
                    rx.link("访问主页 →", href=gh["url"],
                            font_size="0.75rem", color="#3b82f6",
                            _hover={"text_decoration": "underline"},
                            white_space="nowrap"),
                    gap="0.5rem",
                    align="center",
                ),
                rx.text(f"GitHub 实名：Zhang San · 核查通过 ✓",
                        font_size="0.75rem", color="#9ca3af",
                        margin_top="0.25rem"),
                gap="0",
                align="stretch",
                margin_bottom="0.75rem",
            ),
            rx.box(
                rx.text("如需修改绑定账号，请向教师申请解除当前绑定后重新提交。",
                        font_size="0.75rem", color="#a16207"),
                class_name="bg-yellow-50 border border-yellow-100 rounded-lg px-4 py-3",
            ),
            class_name="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6",
            width="100%",
        ),
        # Password change
        rx.box(
            rx.text("修改密码", font_size="0.875rem",
                    font_weight="600", color="#374151",
                    margin_bottom="1rem"),
            rx.vstack(
                rx.box(
                    rx.text("当前密码", font_size="0.75rem",
                            font_weight="500", color="#6b7280",
                            margin_bottom="0.25rem"),
                    _password_input("请输入当前密码"),
                    width="100%",
                ),
                rx.box(
                    rx.text("新密码", font_size="0.75rem",
                            font_weight="500", color="#6b7280",
                            margin_bottom="0.25rem"),
                    _password_input("至少 8 位，包含字母和数字"),
                    width="100%",
                ),
                rx.box(
                    rx.text("确认新密码", font_size="0.75rem",
                            font_weight="500", color="#6b7280",
                            margin_bottom="0.25rem"),
                    _password_input("再次输入新密码"),
                    width="100%",
                ),
                rx.el.button("确认修改密码",
                    class_name="bg-blue-600 hover:bg-blue-700 text-white text-sm px-5 py-2 rounded-lg transition"),
                gap="1rem",
                align="start",
                max_width="24rem",
            ),
            class_name="bg-white rounded-xl border border-gray-100 shadow-sm p-6",
            width="100%",
        ),
        spacing="0",
        width="100%",
        max_width="56rem",
    )
    return protected_page(body, current_route="/profile")


def _status_badge(text: str, color: str) -> rx.Component:
    return rx.text(text,
                   class_name=f"text-xs bg-{color}-100 text-{color}-700 px-2 py-0.5 rounded-full")
