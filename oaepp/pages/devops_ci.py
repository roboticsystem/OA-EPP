"""F-D-004 CI 自动化状态页面。"""

try:
    import reflex as rx
except Exception:
    rx = None


devops_ci_page = None
if rx is not None:
    try:
        from states.devops_ci import CIState
    except ImportError:
        from oaepp.states.devops_ci import CIState

    def devops_ci_page():
        return rx.vstack(
            rx.heading("F-D-004 CI 自动化", size="5"),
            rx.text("CI 状态：", CIState.last_run_status),
            rx.text("Workflow：", CIState.workflow_url),
            rx.text("Lint：", rx.cond(CIState.lint_enabled, "已启用", "未启用")),
            rx.text("Pytest：", rx.cond(CIState.test_enabled, "已启用", "未启用")),
            rx.button("触发 CI", on_click=CIState.trigger_ci),
            spacing="3",
            align="start",
            padding="24px",
        )
