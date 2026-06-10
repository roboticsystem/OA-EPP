"""F-D-006 自动化脚本Web执行界面 — ScriptExecuteState

职责：
- 管理预定义运维脚本列表
- 支持异步执行脚本，实时逐行推送输出到前端
- 区分普通行和错误行（stderr / 非零退出码）
- 跟踪执行进度（current_step / total_steps）
- 失败步骤支持重试

预定义脚本：
- repo_init.sh — GitHub 仓库初始化
- branch_protect.sh — 设置分支保护规则
- secrets_inject.sh — 注入 Secrets
- setup_ci.sh — 设置 CI 工作流
- commitlint_setup.sh — 配置 commitlint

执行流程：
1. 用户选择脚本 → 点击执行
2. State 异步生成器逐行 yield 输出
3. 前端实时更新 console
4. 完成后显示汇总状态（成功/失败）
5. 失败可点击重试
"""

from __future__ import annotations

import asyncio
import subprocess
import os
from enum import Enum
from typing import List, Optional

try:
    import reflex as rx
except Exception:
    rx = None


class LineType(Enum):
    """输出行类型"""
    NORMAL = "normal"
    ERROR = "error"
    SUCCESS = "success"


ScriptExecuteState = None

if rx is not None:

    class ScriptExecuteState(rx.State):
        """自动化脚本Web执行状态管理

        核心状态变量（TDD 要求）：
        - script_output: List[str] — 逐行记录输出（每行文本）
        - line_types: List[str] — 每行对应的类型标记（与 script_output 平行索引）
        - is_running: bool — 是否正在执行
        - current_step: int — 当前步骤（从 1 开始）
        - total_steps: int — 总步骤数
        - selected_script: Optional[str] — 当前选中的脚本
        - exit_code: Optional[int] — 执行完成后的退出码
        """

        script_output: List[str] = []
        line_types: List[str] = []
        is_running: bool = False
        current_step: int = 0
        total_steps: int = 0
        selected_script: str = ""
        exit_code: int = 0

        # 预定义可执行脚本列表（名称 → 显示名称 → 路径）
        available_scripts: List[dict] = [
            {
                "id": "repo_init",
                "name": "① 仓库初始化",
                "description": "克隆模板、初始化基础配置",
                "script_path": "scripts/devops/repo_init.sh",
            },
            {
                "id": "branch_protect",
                "name": "② 分支保护规则",
                "description": "配置 main 分支保护、PR 审查要求",
                "script_path": "scripts/devops/branch_protect.sh",
            },
            {
                "id": "secrets_inject",
                "name": "③ Secrets 注入",
                "description": "批量注入数据库、JWT 等密钥",
                "script_path": "scripts/devops/secrets_inject.sh",
            },
            {
                "id": "setup_ci",
                "name": "④ CI 工作流配置",
                "description": "设置 Ruff 检查 + pytest 工作流",
                "script_path": "scripts/devops/setup_ci.sh",
            },
            {
                "id": "commitlint_setup",
                "name": "⑤ Commitlint 规则",
                "description": "配置提交信息格式检查",
                "script_path": "scripts/devops/commitlint_setup.sh",
            },
        ]

        def __init__(self):
            super().__init__()
            self.script_output = []
            self.line_types = []
            self.is_running = False
            self.current_step = 0
            self.total_steps = 0
            self.selected_script = ""
            self.exit_code = 0

        def select_script(self, script_id: str):
            """选中一个脚本"""
            self.selected_script = script_id
            self.script_output = []
            self.line_types = []
            self.exit_code = 0
            self.current_step = 0
            self.total_steps = 0

        def clear_output(self):
            """清空输出控制台"""
            self.script_output = []
            self.line_types = []
            self.exit_code = 0
            self.current_step = 0
            self.total_steps = 0

        def _add_line(self, content: str, line_type: LineType = LineType.NORMAL):
            """添加一行输出 — 同步追加到 script_output 和 line_types"""
            self.script_output.append(content.strip())
            self.line_types.append(line_type.value)

        async def execute_script(self):
            """执行选中的脚本 — 异步生成器模式，支持实时逐行输出

            使用 yield 在每行输出后推送状态到前端，实现实时逐行推送。
            """
            if self.is_running:
                return

            if not self.selected_script:
                self._add_line("❌ 请先选择一个脚本", LineType.ERROR)
                return

            script_info = next(
                (s for s in self.available_scripts if s["id"] == self.selected_script),
                None
            )
            if not script_info:
                self._add_line(f"❌ 找不到脚本: {self.selected_script}", LineType.ERROR)
                return

            script_path = script_info["script_path"]

            self.is_running = True
            self.current_step = 1
            self.total_steps = self._estimate_total_steps(script_path)
            self.exit_code = 0

            self._add_line(f"🚀 开始执行: {script_info['name']}", LineType.SUCCESS)
            self._add_line(f"📄 脚本路径: {script_path}", LineType.NORMAL)
            self._add_line("=" * 60, LineType.NORMAL)
            yield

            # 异步子进程支持——用于测试环境方便 mock
            _process_runner = getattr(self, "_mock_demo_lines", self._run_real_process)
            async for decoded in _process_runner(script_path):
                line_type = self._classify_line(decoded)
                self._add_line(decoded, line_type)
                if "step" in decoded.lower() or "步骤" in decoded:
                    self.current_step = min(self.current_step + 1, self.total_steps)
                yield
                await asyncio.sleep(0.01)

            self.current_step = self.total_steps
            self._add_line("", LineType.NORMAL)
            self._add_line("=" * 60, LineType.NORMAL)

            if self.exit_code == 0:
                self._add_line("✅ 执行完成，全部步骤成功", LineType.SUCCESS)
            else:
                self._add_line(
                    f"❌ 执行失败，退出码: {self.exit_code}。请检查错误信息后重试。",
                    LineType.ERROR
                )

            self.is_running = False
            yield

        async def _run_real_process(self, script_path: str):
            """运行真实的 shell 脚本子进程，逐行产出输出。"""
            exists = os.path.exists(script_path)
            if not exists:
                self.exit_code = 1
                self._add_line(f"❌ 脚本文件不存在: {script_path}", LineType.ERROR)
                self._add_line("💡 提示：请确认脚本已放置在正确位置", LineType.ERROR)
                return

            try:
                process = await asyncio.create_subprocess_exec(
                    "bash", script_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=os.getcwd(),
                )

                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip("\n\r")
                    if not decoded:
                        continue
                    yield decoded

                self.exit_code = await process.wait()
            except Exception as e:
                self.exit_code = 1
                yield f"💥 执行异常: {str(e)}"

        async def retry_failed(self):
            """重试失败的执行（验收标准要求）"""
            if not self.is_running and self.exit_code != 0 and self.selected_script:
                await self.execute_script()

        def get_full_log(self) -> str:
            """获取完整可复制的错误日志（验收标准要求）"""
            return "\n".join(self.script_output)

        @rx.var
        def is_success(self) -> bool:
            """执行是否成功"""
            return self.exit_code == 0 and len(self.script_output) > 0

        @rx.var
        def is_failed(self) -> bool:
            """执行是否失败"""
            return self.exit_code != 0 and len(self.script_output) > 0

        @rx.var
        def progress_percent(self) -> int:
            """进度百分比（用于进度条）"""
            if self.total_steps <= 0:
                return 0
            return int((self.current_step / self.total_steps) * 100)

        def _estimate_total_steps(self, script_path: str) -> int:
            """粗略估算总步骤数（按 echo 输出的 step 个数）"""
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    content = f.read()
                step_count = content.lower().count("step")
                return max(step_count, 1) if step_count > 0 else 1
            except Exception:
                return 1

        def _classify_line(self, line: str) -> LineType:
            """ classify line by content

            错误行特征：
            - 以 error / fatal / fail / exception 开头
            - 包含 ❌ / ✗ 等错误标记
            - 包含 "error:" / "fatal:" / "failed:" 关键词
            """
            lower_line = line.lower()
            error_keywords = ["error:", "fatal:", "fail", "failed", "exception", "traceback"]
            error_markers = ["❌", "✗", "✖", "×"]

            # 检查标记
            for marker in error_markers:
                if marker in line:
                    return LineType.ERROR

            # 检查关键词
            for kw in error_keywords:
                if kw in lower_line:
                    return LineType.ERROR

            # 检查成功标记
            success_markers = ["✅", "✓", "✔"]
            for marker in success_markers:
                if marker in line:
                    return LineType.SUCCESS

            return LineType.NORMAL