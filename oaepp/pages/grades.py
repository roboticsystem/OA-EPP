"""成绩看板页面（占位）

F-S-030 成绩功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

grades_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def grades_page():
        return page_layout(
            title="成绩看板",
            content=empty_state("成绩功能开发中，敬请期待...", icon="bar_chart_3"),
        )
