"""Courses 页面 — F-S-010 课程主页 + F-S-011 章节内容浏览
"""

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.components.layout import page_wrapper
from oaepp.states.chapter import ChapterState

courses_page_component = None

if rx is not None:

    def _status_badge(status: str) -> rx.Component:
        color_map = {
            "已完成": "bg-green-100 text-green-600",
            "进行中": "bg-blue-100 text-blue-600",
            "待开始": "bg-gray-100 text-gray-500",
        }
        cls = color_map.get(status, "bg-gray-100 text-gray-600")
        return rx.badge(status, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")

    def _type_badge(ch_type: str) -> rx.Component:
        color_map = {
            "作业": "bg-purple-100 text-purple-600",
            "考试": "bg-red-100 text-red-600",
            "签到": "bg-green-100 text-green-600",
        }
        cls = color_map.get(ch_type, "bg-gray-100 text-gray-600")
        return rx.badge(ch_type, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")

    def _progress_bar(value, max_val=100) -> rx.Component:
        return rx.box(
            rx.box(class_name="bg-blue-500 h-full rounded-full transition-all"),
            class_name="w-full bg-gray-200 rounded-full h-2",
        )

    def _course_card(course: dict) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(course.get("title", ""), class_name="text-lg font-bold text-gray-800"),
                    rx.cond(course.get("is_active", True), _status_badge("进行中"), _status_badge("已完成")),
                    justify="between",
                    width="100%",
                ),
                rx.hstack(
                    rx.text(f"学期: {course.get('semester', '')}", class_name="text-xs text-gray-500"),
                    rx.text(f"总分: {course.get('total_score', 0)}", class_name="text-xs text-gray-500"),
                    spacing="4",
                ),
                rx.hstack(
                    rx.text(f"{course.get('completed_chapters', 0)}/{course.get('total_chapters', 0)} 章节",
                            class_name="text-sm text-gray-600"),
                    justify="between",
                    width="100%",
                ),
                _progress_bar(course.get("completed_chapters", 0), course.get("total_chapters", 1)),
                rx.text(
                    rx.cond(course.get("deadline_reminder"), course.get("deadline_reminder"), "无截止提醒"),
                    class_name="text-xs text-gray-400 italic",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-5 cursor-pointer hover:shadow-md transition-shadow",
            width="100%",
            on_click=lambda: ChapterState.load_chapters(course.get("id", "")),
        )

    def _chapter_table() -> rx.Component:
        return rx.box(
            rx.cond(
                ChapterState.chapters_loading,
                rx.text("加载中...", class_name="text-gray-400 text-sm py-4"),
                rx.cond(
                    ChapterState.chapters.length() == 0,
                    rx.text("暂无章节数据", class_name="text-gray-400 text-sm py-4"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("章节号", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                rx.table.column_header_cell("章节名", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                rx.table.column_header_cell("类型", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                rx.table.column_header_cell("截止时间", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                rx.table.column_header_cell("状态", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                rx.table.column_header_cell("评分标准", class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider"),
                                class_name="bg-gray-50 border-b border-gray-200",
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                ChapterState.chapters,
                                lambda ch: rx.table.row(
                                    rx.table.cell(ch["chapter_no"], class_name="text-sm text-gray-600"),
                                    rx.table.cell(ch["title"], class_name="text-sm font-medium text-gray-800"),
                                    rx.table.cell(_type_badge(ch.get("chapter_type", ""))),
                                    rx.table.cell(ch.get("deadline", "—"), class_name="text-sm text-gray-500"),
                                    rx.table.cell(_status_badge(ch.get("status", "未开始"))),
                                    rx.table.cell(ch.get("grading_criteria", "—"), class_name="text-sm text-gray-500 max-w-xs truncate"),
                                    class_name="border-b border-gray-100 hover:bg-gray-50 cursor-pointer",
                                    on_click=lambda ch_id=ch["id"]: ChapterState.go_to_chapter(ch_id),
                                ),
                            ),
                        ),
                        width="100%",
                    ),
                ),
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden",
        )

    def courses_page() -> rx.Component:
        """课程学习页面"""
        return page_wrapper(
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.html(
                            '<svg class="w-6 h-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>'
                        ),
                    ),
                    rx.heading("课程学习", class_name="text-xl font-bold text-gray-800"),
                    spacing="3",
                    align="center",
                    class_name="mb-6",
                ),
                rx.cond(ChapterState.courses_loading, rx.text("加载中...", class_name="text-gray-400 text-sm mb-4")),
                rx.cond(
                    ChapterState.courses.length() > 0,
                    rx.grid(
                        rx.foreach(ChapterState.courses, lambda c: _course_card(c)),
                        columns="2",
                        spacing="4",
                        width="100%",
                        class_name="mb-8",
                    ),
                ),
                rx.cond(
                    ChapterState.current_course,
                    rx.vstack(
                        rx.hstack(
                            rx.heading(
                                f"{ChapterState.current_course['title']} — 章节明细",
                                class_name="text-lg font-bold text-gray-800",
                            ),
                            spacing="3",
                            align="center",
                            class_name="mb-4",
                        ),
                        _chapter_table(),
                        spacing="2",
                        width="100%",
                    ),
                ),
                rx.cond(
                    ChapterState.error_message != "",
                    rx.box(
                        rx.text(ChapterState.error_message, class_name="text-sm"),
                        class_name="bg-red-50 border border-red-200 text-red-600 rounded-lg p-4 mt-4",
                    ),
                ),
                width="100%",
            ),
            current_page="/courses",
        )

    courses_page_component = courses_page
