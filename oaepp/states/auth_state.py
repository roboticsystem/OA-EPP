import reflex as rx


class AuthState(rx.State):
    student_id: str = ""
    password: str = ""
    error_message: str = ""

    def set_student_id_value(self, value: str):
        self.student_id = value

    def set_password_value(self, value: str):
        self.password = value

    def login(self):
        if not self.student_id or not self.password:
            self.error_message = "请输入学号/邮箱和密码"
            return

        if self.password == self.student_id:
            self.error_message = ""
            return rx.redirect("/dashboard")

        self.error_message = "学号或密码错误，请重试。"
