#!/usr/bin/env bash
# ============================================================
# OA-EPP 原型预览服务器
# 用法：bash start_prototype.sh [端口号]
#       默认端口：8088
# ============================================================

PORT=${1:-8088}
PROTO_DIR="$(cd "$(dirname "$0")/prototype" && pwd)"

# ── 检查端口占用 ──────────────────────────────────────────
if lsof -iTCP:"$PORT" -sTCP:LISTEN -t &>/dev/null 2>&1; then
  echo "⚠  端口 $PORT 已被占用，尝试使用端口 $((PORT + 1))"
  PORT=$((PORT + 1))
fi

# ── 启动 HTTP 服务器 ──────────────────────────────────────
cd "$PROTO_DIR" || { echo "❌ 找不到 prototype/ 目录"; exit 1; }
python3 -m http.server "$PORT" --bind 0.0.0.0 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
echo ""

# ── 端口转发提示 ──────────────────────────────────────────
echo "══════════════════════════════════════════════════"
echo "  OA-EPP 原型服务器已启动"
echo "══════════════════════════════════════════════════"
echo "  本地访问：http://localhost:$PORT"
echo ""
echo "  若使用 VS Code Remote / Codespaces，请设置端口转发："
echo "  方法一（VS Code 端口转发面板）："
echo "    1. 按 Ctrl+Shift+P → \"Forward a Port\""
echo "    2. 输入端口号：$PORT"
echo "    3. 在浏览器中打开转发后的 URL"
echo ""
echo "  方法二（命令行 SSH 隧道）："
echo "    ssh -L $PORT:localhost:$PORT <remote-host>"
echo "══════════════════════════════════════════════════"
echo "  首页入口：index.html / admin_students.html"
echo "  停止服务：kill $SERVER_PID"
echo "══════════════════════════════════════════════════"

# ── 自动尝试 VS Code 端口转发（需要 code CLI）─────────────
if command -v code &>/dev/null; then
  echo ""
  echo "  检测到 VS Code CLI，尝试自动转发端口 $PORT ..."
  # VS Code CLI 方式：写入 .vscode/settings.json portAttributes 仅作说明
  # 实际自动转发通过 Remote 扩展完成，此处仅打印提示
  echo "  提示：在 VS Code 「端口」面板可看到已监听的 $PORT，点击「在浏览器中打开」即可"
fi

wait "$SERVER_PID"
