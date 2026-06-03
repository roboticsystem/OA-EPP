import reflex as rx

from oaepp.states.auth_state import AuthState


def login():
    return rx.center(
        rx.box(
            rx.vstack(
                rx.box(
                    "✓",
                    width="4rem",
                    height="4rem",
                    border_radius="1rem",
                    background="#2563eb",
                    color="white",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    font_size="2rem",
                    font_weight="bold",
                    margin_bottom="1rem",
                ),
                rx.heading("工程实践管理平台", size="6"),
                rx.text(
                    "OA-EPP · Engineering Practice Platform",
                    color="#6b7280",
                    font_size="0.9rem",
                ),
                rx.box(height="1.5rem"),
                rx.box(
                    rx.vstack(
                        rx.heading("账号登录", size="4", align="left", width="100%"),
                        rx.cond(
                            AuthState.error_message != "",
                            rx.box(
                                AuthState.error_message,
                                background="#fef2f2",
                                color="#b91c1c",
                                border="1px solid #fecaca",
                                border_radius="0.5rem",
                                padding="0.75rem",
                                width="100%",
                                font_size="0.875rem",
                            ),
                        ),
                        rx.vstack(
                            rx.text("学号 / 邮箱", color="#4b5563", font_size="0.875rem"),
                            rx.input(
                                placeholder="请输入学号或邮箱",
                                value=AuthState.student_id,
                                on_change=AuthState.set_student_id_value,
                                width="100%",
                            ),
                            align_items="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("密码", color="#4b5563", font_size="0.875rem"),
                            rx.input(
                                placeholder="请输入密码",
                                type="password",
                                value=AuthState.password,
                                on_change=AuthState.set_password_value,
                                width="100%",
                            ),
                            rx.text(
                                "初始密码为学号，请登录后及时修改",
                                color="#9ca3af",
                                font_size="0.75rem",
                            ),
                            align_items="start",
                            width="100%",
                        ),
                        rx.button(
                            "登 录",
                            on_click=AuthState.login,
                            width="100%",
                            background="#2563eb",
                            color="white",
                        ),
                        rx.hstack(
                            rx.divider(),
                            rx.text("或", color="#9ca3af", font_size="0.75rem"),
                            rx.divider(),
                            width="100%",
                        ),
                        rx.text(
                            "忘记密码？请联系教师或助教重置。",
                            color="#9ca3af",
                            font_size="0.75rem",
                            text_align="center",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    background="white",
                    border_radius="1rem",
                    box_shadow="0 10px 25px rgba(0,0,0,0.08)",
                    padding="2rem",
                    width="100%",
                ),
                rx.hstack(
                    rx.link("学生端", href="/dashboard", color="#2563eb"),
                    rx.link("教师端", href="/dashboard", color="#6b7280"),
                    spacing="6",
                    font_size="0.75rem",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            width="100%",
            max_width="28rem",
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)",
        padding="1rem",
    )
