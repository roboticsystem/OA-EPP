"""在线考试页面（占位）

F-S-053 考试功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

exam_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def exam_page():
        return page_layout(
            title="在线考试",
            content=empty_state("考试功能开发中，敬请期待...", icon="clipboard_check"),
        )
