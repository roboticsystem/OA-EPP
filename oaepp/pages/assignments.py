"""作业提交页面（占位）

F-S-020 作业功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

assignments_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def assignments_page():
        return page_layout(
            title="作业提交",
            content=empty_state("作业功能开发中，敬请期待...", icon="file_text"),
        )
