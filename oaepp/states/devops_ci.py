"""F-D-004 CI 自动化状态模型。"""

import reflex as rx


class CIState(rx.State):
    ci_enabled: bool = True
    last_run_status: str = "not_started"
    workflow_url: str = ".github/workflows/ci.yml"
    CI_STEPS: tuple[str, ...] = ("ruff", "pytest")
    lint_enabled: bool = True
    test_enabled: bool = True

    async def trigger_ci(self):
        self.last_run_status = "queued"
