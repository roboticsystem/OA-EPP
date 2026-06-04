"""OA-EPP Reflex 应用 — 路由注册

创建应用实例并注册所有页面路由。
"""

import reflex as rx
from oaepp.components.layout import page_wrapper
from oaepp.pages.courses import content as courses_content
from oaepp.states.chapter import ChapterState

app = rx.App(
    style={
        "font_family": "system-ui, -apple-system, sans-serif",
    },
)


def courses_page() -> rx.Component:
    return page_wrapper(courses_content(), current_page="/courses")


@rx.page(route="/", title="课程学习 - OA-EPP", on_load=ChapterState.load_courses)
def index():
    return courses_page()


@rx.page(route="/courses", title="课程学习 - OA-EPP", on_load=ChapterState.load_courses)
def courses():
    return courses_page()
