"""我的课程页面（占位）

F-S-010 课程功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

courses_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def courses_page():
        return page_layout(
            title="我的课程",
            content=empty_state("课程功能开发中，敬请期待...", icon="book_open"),
        )
