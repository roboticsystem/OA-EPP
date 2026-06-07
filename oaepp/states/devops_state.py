import reflex as rx
import json
import httpx

from . import GlobalState

class DevOpsState(GlobalState):
    logs: list[dict] = []
    current_step: int = 0
    total_steps: int = 0
    status: str = "idle"
    failed_step: int = 0
    error_log: str = ""

    steps_to_run: list[str] = [
        "gh repo create my-repo --public",
        "gh secret set MY_SECRET",
        "git checkout -b main"
    ]

    def _reset_state(self, start_from_step: int = 0):
        self.status = "running"
        self.logs = []
        self.error_log = ""
        self.current_step = start_from_step + 1
        self.total_steps = len(self.steps_to_run)

    async def execute_scripts(self, start_from_step: int = 0):
        # 违规全局常量移入方法内部
        API_URL = "http://localhost:8000/api/devops/script"
        self._reset_state(start_from_step)
        yield

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"steps": self.steps_to_run[start_from_step:]}
                async with client.stream("POST", API_URL, json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if data["type"] == "progress":
                                self.current_step = data["current"]
                            elif data["type"] == "output":
                                self.logs.append({"text": data["data"], "is_error": False})
                            elif data["type"] in ("error", "step_failed"):
                                self.logs.append({"text": data["data"], "is_error": True})
                            elif data["type"] == "summary":
                                self.status = data["status"]
                                self.error_log = data.get("error_log", "")
                                self.failed_step = data.get("failed_step", 0)
                        except json.JSONDecodeError:
                            self.logs.append({"text": line, "is_error": True})
                        yield
        except Exception as e:
            self.status = "failed"
            self.logs.append({"text": f"API 连接异常: {str(e)}", "is_error": True})
            yield

    async def retry_failed(self):
        if self.failed_step > 0:
            async for _ in self.execute_scripts(start_from_step=self.failed_step - 1):
                yield
