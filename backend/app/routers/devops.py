# 文件路径: backend/app/routers/devops.py
import asyncio
from fastapi import APIRouter, WebSocket

router = APIRouter()

# 允许执行的命令前缀白名单
ALLOWED_PREFIXES = ("gh ", "git ")


@router.websocket("/ws/devops/script")
async def script_websocket(ws: WebSocket):
    await ws.accept()

    # 接收前端传来的步骤列表 JSON
    data = await ws.receive_json()
    steps = data.get("steps", [])
    total_steps = len(steps)

    error_log_buffer = []  # 用于聚合完整错误日志

    for idx, cmd in enumerate(steps, start=1):
        # 安全校验
        if not any(cmd.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES):
            await ws.send_json({"type": "error", "data": f"非法命令被拒绝: {cmd}"})
            error_log_buffer.append(f"非法命令: {cmd}")
            await ws.send_json(
                {"type": "summary", "status": "failed", "exit_code": -1, "error_log": "\n".join(error_log_buffer),
                 "failed_step": idx})
            return

        # 推送当前进度
        await ws.send_json({"type": "progress", "current": idx, "total": total_steps, "cmd": cmd})

        # 执行子进程
        process = await asyncio.create_subprocess_exec(
            *cmd.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def read_stream(stream, is_error: bool):
            while True:
                line = await stream.readline()
                if not line: break
                decoded_line = line.decode().strip()
                if is_error: error_log_buffer.append(decoded_line)
                await ws.send_json({"type": "error" if is_error else "output", "data": decoded_line})

        await asyncio.gather(read_stream(process.stdout, False), read_stream(process.stderr, True))
        await process.wait()

        # 步骤失败则中断，并提示可重试
        if process.returncode != 0:
            await ws.send_json({"type": "step_failed", "failed_step": idx, "cmd": cmd})
            await ws.send_json({"type": "summary", "status": "failed", "exit_code": process.returncode,
                                "error_log": "\n".join(error_log_buffer), "failed_step": idx})
            return

    # 全部成功
    await ws.send_json({"type": "summary", "status": "success", "exit_code": 0, "error_log": "", "failed_step": None})
