class CIState:
    ci_enabled = True
    last_run_status = "not_started"
    workflow_url = ".github/workflows/ci.yml"
    CI_STEPS = ("ruff", "pytest")
    lint_enabled = True
    test_enabled = True

    async def trigger_ci(self):
        self.last_run_status = "queued"
