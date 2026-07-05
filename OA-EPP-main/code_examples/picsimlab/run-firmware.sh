#!/bin/bash
# ============================================================
# run-firmware.sh — 一键上传固件到 PicSimLab 并打开浏览器查看
# 用法：
#   ./run-firmware.sh <固件文件路径>           # .hex 或 .bin
#   ./run-firmware.sh firmware.hex             # AVR/PIC 板使用 loadhex
#   ./run-firmware.sh firmware.bin             # STM32/ESP32 板使用 loadbin
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$SCRIPT_DIR"
CONTAINER_NAME="picsimlab-vnc"
RCONTROL_HOST="127.0.0.1"
RCONTROL_PORT=5000
NOVNC_PORT=6080
FIRMWARE_DIR="/firmware"

# ---- 参数校验 ----
if [ $# -lt 1 ]; then
    echo "用法: $0 <固件文件路径.hex|.bin>"
    exit 1
fi

FIRMWARE_FILE="$(realpath "$1")"
if [ ! -f "$FIRMWARE_FILE" ]; then
    echo "错误: 文件不存在 — $FIRMWARE_FILE"
    exit 1
fi

FIRMWARE_NAME="$(basename "$FIRMWARE_FILE")"
FIRMWARE_EXT="${FIRMWARE_NAME##*.}"

# 根据扩展名选择加载命令
case "$FIRMWARE_EXT" in
    hex|HEX) LOAD_CMD="loadhex" ;;
    bin|BIN) LOAD_CMD="loadbin" ;;
    *)
        echo "错误: 不支持的文件格式 .$FIRMWARE_EXT（仅支持 .hex 和 .bin）"
        exit 1
        ;;
esac

# ---- 确保容器运行 ----
echo ">>> 检查容器状态..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ">>> 容器未运行，启动中..."
    cd "$COMPOSE_DIR" && docker compose up -d
    echo ">>> 等待服务就绪..."
    sleep 5
fi

# ---- 上传固件到容器 ----
echo ">>> 上传固件: $FIRMWARE_NAME"
docker cp "$FIRMWARE_FILE" "${CONTAINER_NAME}:${FIRMWARE_DIR}/${FIRMWARE_NAME}"

# ---- 通过远程控制接口加载固件 ----
echo ">>> 通过 rcontrol 发送 $LOAD_CMD 命令..."
REMOTE_PATH="${FIRMWARE_DIR}/${FIRMWARE_NAME}"

# 等待 rcontrol 端口可用（最多 30 秒）
for i in $(seq 1 30); do
    if nc -z "$RCONTROL_HOST" "$RCONTROL_PORT" 2>/dev/null; then
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "警告: rcontrol 端口 $RCONTROL_PORT 不可用，固件已上传到容器但未自动加载。"
        echo "       请在 PicSimLab GUI 中手动加载: $REMOTE_PATH"
        echo "       或稍后手动执行: echo '$LOAD_CMD $REMOTE_PATH' | nc $RCONTROL_HOST $RCONTROL_PORT"
    fi
    sleep 1
done

# 发送加载命令
RESPONSE=$(echo "$LOAD_CMD $REMOTE_PATH" | nc -w 3 "$RCONTROL_HOST" "$RCONTROL_PORT" 2>/dev/null || true)
if echo "$RESPONSE" | grep -qi "ok"; then
    echo ">>> 固件加载成功！"
elif [ -n "$RESPONSE" ]; then
    echo ">>> rcontrol 响应: $RESPONSE"
else
    echo ">>> 固件已上传到容器 $REMOTE_PATH"
    echo "    如果 rcontrol 未启用，请在 PicSimLab GUI 中手动加载。"
fi

# ---- 自动打开浏览器 ----
NOVNC_URL="http://${RCONTROL_HOST}:${NOVNC_PORT}/vnc.html?autoconnect=true"
echo ">>> 打开浏览器查看 PicSimLab..."
echo "    URL: $NOVNC_URL"

# 跨平台打开浏览器
if command -v xdg-open &>/dev/null; then
    xdg-open "$NOVNC_URL" 2>/dev/null &
elif command -v open &>/dev/null; then
    open "$NOVNC_URL" 2>/dev/null &
elif command -v start &>/dev/null; then
    start "$NOVNC_URL" 2>/dev/null &
else
    echo "    请手动在浏览器中打开上述 URL"
fi

echo ""
echo "=== 完成 ==="
echo "  VNC 密码: picsimlab"
echo "  远程控制: nc $RCONTROL_HOST $RCONTROL_PORT"
echo "  停止容器: cd $COMPOSE_DIR && docker compose down"
