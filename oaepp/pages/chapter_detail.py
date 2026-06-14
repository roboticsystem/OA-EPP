"""Chapter Detail 页面 — F-S-011 章节内容浏览

显示章节 Markdown 内容，支持上下导航和资源查看。
"""

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.components.layout import page_wrapper
from oaepp.states.chapter import ChapterState

chapter_page_component = None

if rx is not None:

    def _type_badge(ch_type: str) -> rx.Component:
        color_map = {
            "作业": "bg-purple-100 text-purple-600",
            "考试": "bg-red-100 text-red-600",
            "签到": "bg-green-100 text-green-600",
        }
        cls = color_map.get(ch_type, "bg-gray-100 text-gray-600")
        return rx.badge(ch_type, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")

    def _status_badge(status: str) -> rx.Component:
        color_map = {
            "已完成": "bg-green-100 text-green-600",
            "进行中": "bg-blue-100 text-blue-600",
            "待开始": "bg-gray-100 text-gray-500",
        }
        cls = color_map.get(status, "bg-gray-100 text-gray-600")
        return rx.badge(status, class_name=f"px-2 py-0.5 rounded text-xs font-medium {cls}")

    def chapter_page() -> rx.Component:
        """章节内容详情页面"""
        return page_wrapper(
            rx.box(
                # 标题 + 元数据
                rx.cond(
                    ChapterState.chapter_loading,
                    rx.text("加载中...", class_name="text-gray-400 text-sm"),
                    rx.cond(
                        ChapterState.current_chapter,
                        rx.vstack(
                            # 章节标题和元数据
                            rx.box(
                                rx.hstack(
                                    rx.heading(
                                        ChapterState.current_chapter["title"],
                                        class_name="text-xl font-bold text-gray-800",
                                    ),
                                    _type_badge(ChapterState.current_chapter.get("chapter_type", "")),
                                    _status_badge(ChapterState.current_chapter.get("status", "未开始")),
                                    spacing="3",
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text(f"第 {ChapterState.current_chapter['chapter_no']} 章",
                                            class_name="text-sm text-gray-500"),
                                    rx.text(f"截止: {ChapterState.current_chapter.get('deadline', '—')}",
                                            class_name="text-sm text-gray-500"),
                                    rx.text(f"评分: {ChapterState.current_chapter.get('grading_criteria', '—')}",
                                            class_name="text-sm text-gray-500"),
                                    spacing="4",
                                    class_name="mt-2",
                                ),
                                class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6",
                            ),

                            # Markdown 内容
                            rx.box(
                                rx.html(
                                    ChapterState.chapter_content_html,
                                    class_name="prose prose-sm max-w-none",
                                ),
                                class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6",
                                width="100%",
                            ),

                            # 上下导航
                            rx.hstack(
                                rx.cond(
                                    ChapterState.prev_chapter,
                                    rx.button(
                                        rx.hstack(
                                            rx.html('<svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>'),
                                            rx.text("上一章", class_name="text-sm"),
                                            spacing="1",
                                            align="center",
                                        ),
                                        on_click=ChapterState.go_to_chapter(ChapterState.prev_chapter["id"]),
                                        class_name="bg-white border border-gray-200 rounded-lg px-4 py-2 text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer",
                                    ),
                                    rx.box(),
                                ),
                                rx.cond(
                                    ChapterState.next_chapter,
                                    rx.button(
                                        rx.hstack(
                                            rx.text("下一章", class_name="text-sm"),
                                            rx.html('<svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>'),
                                            spacing="1",
                                            align="center",
                                        ),
                                        on_click=ChapterState.go_to_chapter(ChapterState.next_chapter["id"]),
                                        class_name="bg-white border border-gray-200 rounded-lg px-4 py-2 text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer",
                                    ),
                                    rx.box(),
                                ),
                                justify="between",
                                width="100%",
                                class_name="mb-6",
                            ),

                            # 返回课程页链接
                            rx.link(
                                rx.hstack(
                                    rx.html('<svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>'),
                                    rx.text("返回课程列表", class_name="text-sm"),
                                    spacing="1",
                                    align="center",
                                ),
                                href="/courses",
                                class_name="text-blue-600 hover:text-blue-700",
                            ),

                            spacing="4",
                            width="100%",
                        ),
                        rx.text("请选择一个章节查看", class_name="text-gray-400 text-sm"),
                    ),
                ),
                class_name="p-6 w-full",
            ),
            current_page="/courses",
        )

    chapter_page_component = chapter_page
