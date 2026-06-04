import reflex as rx

from rxconfig import config
from .pages.login import login_page, LoginState
from .pages.dashboard import dashboard_page
from .pages.courses import courses_page
from .pages.assignments import assignments_page
from .pages.grades import grades_page
from .pages.attendance import attendance_page
from .pages.exam import exam_page
from .pages.profile import profile_page


def loading_indicator() -> rx.Component:
    return rx.center(
        rx.spinner(size="3"),
        min_height="100vh",
    )


style = {
    "font_family": "\"Microsoft YaHei\", \"Noto Sans SC\", sans-serif",
}

app = rx.App(
    style=style,
    stylesheets=[],
)

app.add_page(login_page, route="/login", title="OA-EPP · 登录")
app.add_page(dashboard_page, route="/", title="OA-EPP · 仪表盘")
app.add_page(courses_page, route="/courses", title="OA-EPP · 课程列表")
app.add_page(assignments_page, route="/assignments", title="OA-EPP · 作业提交")
app.add_page(grades_page, route="/grades", title="OA-EPP · 成绩与反馈")
app.add_page(attendance_page, route="/attendance", title="OA-EPP · 课堂签到")
app.add_page(exam_page, route="/exam", title="OA-EPP · 在线考试")
app.add_page(profile_page, route="/profile", title="OA-EPP · 个人资料")
