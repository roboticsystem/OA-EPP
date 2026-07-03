"""课堂点名页面（占位）

F-S-052 考勤功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

attendance_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def attendance_page():
        return page_layout(
            title="课堂点名",
            content=empty_state("考勤功能开发中，敬请期待...", icon="user_check"),
        )
