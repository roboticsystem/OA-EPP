"""仪表盘页面（占位）

F-S-010 仪表盘功能开发中，当前提供占位页面避免 404。
"""
try:
    import reflex as rx
except Exception:
    rx = None

dashboard_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import empty_state

    def dashboard_page():
        return page_layout(
            title="仪表盘",
            content=empty_state("仪表盘功能开发中，敬请期待...", icon="layout_dashboard"),
        )
