import reflex as rx
from oaepp.states.auth_state import AuthState
from oaepp.states.course_state import CourseState


def login_page() -> rx.Component:
    """
    简单的登录演示页面
    用于选择学生和加载课程信息
    """
    return rx.box(
        rx.vstack(
            rx.heading("学生登录", size="xl", color_scheme="blue"),
            
            rx.vstack(
                rx.text("选择学生账号"),
                rx.select(
                    ["STU001 - 张三", "STU002 - 李四"],
                    on_change=lambda value: AuthState.set_student(
                        int(value.split()[0].replace("STU", "")),
                        value.split(" - ")[1] if " - " in value else "",
                        ""
                    ),
                ),
                width="100%",
            ),
            
            rx.button(
                "进入课程页面",
                on_click=lambda: (
                    AuthState.set_student(1, "张三", ""),
                    rx.redirect("/courses")
                ),
                color_scheme="blue",
                size="lg",
            ),
            
            spacing="4",
            padding="8",
            max_width="400px",
            margin="100px auto",
            border="1px solid #e0e0e0",
            border_radius="8px",
        ),
        width="100%",
        min_height="100vh",
    )


@rx.page(route="/", title="学生登录")
def index():
    return login_page()
