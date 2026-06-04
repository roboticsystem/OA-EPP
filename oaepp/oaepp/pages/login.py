import reflex as rx


class LoginState(rx.State):
    student_id: str = ""
    password: str = ""
    error_msg: str = ""
    is_logged_in: bool = False

    def login(self):
        if not self.student_id.strip():
            self.error_msg = "请输入学号"
            return
        if not self.password.strip():
            self.error_msg = "请输入密码"
            return
        self.error_msg = ""
        self.is_logged_in = True
        return rx.redirect("/")

    def logout(self):
        self.is_logged_in = False
        self.student_id = ""
        self.password = ""
        return rx.redirect("/login")


def login_page() -> rx.Component:
    return rx.box(
        rx.center(
            rx.vstack(
                rx.box(
                    rx.html(
                        '<svg class="w-9 h-9 text-white" fill="none" stroke="currentColor" '
                        'viewBox="0 0 24 24">'
                        '<path stroke-linecap="round" stroke-linejoin="round" '
                        'stroke-width="2" '
                        'd="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 '
                        "0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 "
                        "3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00"
                        "-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 "
                        "3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01"
                        "-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 "
                        "3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                        '</path></svg>'
                    ),
                    width="4rem", height="4rem",
                    bg="#2563eb", border_radius="1rem",
                    display="flex", align_items="center",
                    justify_content="center",
                ),
                rx.text("工程实践管理平台", font_size="1.5rem",
                        font_weight="bold", color="#1f2937"),
                rx.text("OA-EPP · Engineering Practice Platform",
                        font_size="0.875rem", color="#6b7280",
                        margin_bottom="1.5rem"),
                rx.cond(
                    LoginState.error_msg != "",
                    rx.box(
                        rx.text(LoginState.error_msg),
                        bg="#fef2f2", border="1px solid #fecaca",
                        color="#b91c1c", font_size="0.875rem",
                        padding="0.75rem 1rem", border_radius="0.5rem",
                        width="100%",
                    ),
                ),
                rx.vstack(
                    rx.text("学号", font_size="0.875rem",
                            font_weight="500", color="#4b5563"),
                    rx.input(
                        placeholder="请输入学号",
                        value=LoginState.student_id,
                        on_change=LoginState.set_student_id,
                        width="100%",
                        padding="0.625rem 1rem",
                        border="1px solid #d1d5db",
                        border_radius="0.5rem",
                        font_size="0.875rem",
                    ),
                    rx.text("密码", font_size="0.875rem",
                            font_weight="500", color="#4b5563"),
                    rx.input(
                        placeholder="请输入密码", type="password",
                        value=LoginState.password,
                        on_change=LoginState.set_password,
                        width="100%",
                        padding="0.625rem 1rem",
                        border="1px solid #d1d5db",
                        border_radius="0.5rem",
                        font_size="0.875rem",
                    ),
                    rx.text("初始密码为学号，请登录后及时修改",
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.25rem"),
                    rx.button("登 录",
                              on_click=LoginState.login,
                              bg="#2563eb",
                              _hover={"bg": "#1d4ed8"},
                              color="white",
                              font_weight="600",
                              padding="0.625rem 0",
                              width="100%",
                              border_radius="0.5rem",
                              font_size="0.875rem",
                              margin_top="0.5rem"),
                    rx.hstack(
                        rx.box(border_top="1px solid #e5e7eb", flex="1"),
                        rx.text("或", font_size="0.75rem", color="#9ca3af",
                                margin_x="0.75rem"),
                        rx.box(border_top="1px solid #e5e7eb", flex="1"),
                        align="center",
                        width="100%",
                        margin_y="1.25rem",
                    ),
                    rx.text("忘记密码？请联系教师或助教重置。",
                            font_size="0.75rem", color="#9ca3af",
                            text_align="center"),
                    rx.hstack(
                        rx.link("学生端", href="/", font_size="0.75rem",
                                color="#2563eb", underline="hover"),
                        rx.link("教师端", href="/admin_students",
                                font_size="0.75rem", color="#6b7280",
                                underline="hover"),
                        justify="center",
                        gap="1.5rem",
                        margin_top="1.25rem",
                    ),
                    gap="0.5rem",
                    width="100%",
                ),
                bg="white",
                border_radius="1rem",
                box_shadow="0 10px 25px rgba(0,0,0,0.1)",
                padding="2rem",
                width="100%",
                max_width="28rem",
            ),
            width="100%",
            min_height="100vh",
        ),
        width="100%",
        min_height="100vh",
        bg="linear-gradient(135deg, #eff6ff, #dbeafe)",
    )
