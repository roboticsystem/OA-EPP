"""课程学习页 (F-S-010 + F-S-011)"""

import reflex as rx
from oaepp.components.layout import page_layout
from oaepp.states.courses import CoursesState


def _status_badge(status: str) -> rx.Component:
    cls = {"已完成": "bg-green-100 text-green-600", "进行中": "bg-blue-100 text-blue-600"}.get(
        status, "bg-gray-100 text-gray-500"
    )
    return rx.badge(status, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")


def _type_badge(ch_type: str) -> rx.Component:
    cls = {
        "作业": "bg-purple-100 text-purple-600",
        "考试": "bg-red-100 text-red-600",
        "签到": "bg-green-100 text-green-600",
    }.get(ch_type, "bg-gray-100 text-gray-600")
    return rx.badge(ch_type, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")


def _course_card(course: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(course["name"], class_name="text-lg font-bold text-gray-800"),
                _status_badge("进行中"),
                justify="between",
                width="100%",
            ),
            rx.hstack(
                rx.text(f"学期: {course['term']}", class_name="text-xs text-gray-500"),
                rx.text(f"代码: {course['code']}", class_name="text-xs text-gray-500"),
                spacing="4",
            ),
            rx.text(f"{course['total_chapters']} 章节", class_name="text-sm text-gray-600"),
            spacing="3",
            align="start",
            width="100%",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-5 cursor-pointer hover:shadow-md transition-shadow",
        on_click=CoursesState.load_chapters(course["id"]),
    )


def _chapter_table() -> rx.Component:
    return rx.box(
        rx.cond(
            CoursesState.chapters_loading,
            rx.text("加载中...", class_name="text-gray-400 text-sm py-4"),
            rx.cond(
                CoursesState.chapters.length() == 0,
                rx.text("暂无章节数据", class_name="text-gray-400 text-sm py-4"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("章节号", class_name="text-xs font-semibold text-gray-500 uppercase"),
                            rx.table.column_header_cell("章节名", class_name="text-xs font-semibold text-gray-500 uppercase"),
                            rx.table.column_header_cell("类型", class_name="text-xs font-semibold text-gray-500 uppercase"),
                            class_name="bg-gray-50",
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            CoursesState.chapters,
                            lambda ch: rx.table.row(
                                rx.table.cell(f"第{ch['chapter_no']}章", class_name="text-sm text-gray-600"),
                                rx.table.cell(ch["title"], class_name="text-sm font-medium text-gray-800"),
                                rx.table.cell(_type_badge(ch["chapter_type"])),
                                class_name="border-b border-gray-100 hover:bg-gray-50",
                            ),
                        ),
                    ),
                ),
            ),
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden",
    )


def courses_page():
    """课程学习页面 — 自动注册路由 /courses"""
    return page_layout(
        title="课程学习",
        content=rx.vstack(
            # 加载按钮（初始状态）
            rx.cond(
                (CoursesState.courses.length() == 0) & ~CoursesState.courses_loading,
                rx.vstack(
                    rx.text("点击加载课程数据", class_name="text-sm text-gray-400"),
                    rx.button(
                        "加载课程",
                        on_click=CoursesState.load_courses(),
                        color_scheme="blue",
                    ),
                    spacing="3",
                    align="center",
                    class_name="py-8",
                ),
            ),
            # 加载中
            rx.cond(
                CoursesState.courses_loading,
                rx.text("加载中...", class_name="text-gray-400 text-sm"),
            ),
            # 课程卡片网格
            rx.cond(
                CoursesState.courses.length() > 0,
                rx.grid(
                    rx.foreach(CoursesState.courses, lambda c: _course_card(c)),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
            ),
            # 章节明细
            rx.cond(
                CoursesState.current_course,
                rx.vstack(
                    rx.heading(
                        f"{CoursesState.current_course['name']} — 章节明细",
                        class_name="text-lg font-bold text-gray-800",
                    ),
                    _chapter_table(),
                    spacing="4",
                    width="100%",
                ),
            ),
            # 错误提示
            rx.cond(
                CoursesState.error_message != "",
                rx.box(
                    rx.text(CoursesState.error_message, class_name="text-sm"),
                    class_name="bg-red-50 border border-red-200 text-red-600 rounded-lg p-4",
                ),
            ),
            spacing="4",
            width="100%",
        ),
    )
