#!/bin/sh
set -eu

cd /app

echo "[start.sh] 初始化数据库..."
python scripts/init_db_and_seed.py || echo "[start.sh] 数据库初始化失败（可能已存在），继续启动..."

# ── 先启动 Nginx，确保端口 80 始终可达 ──────────────────────────────────
# 之前 Nginx 在 Reflex 就绪后才启动，导致 Reflex 编译期间（~28s）端口 80
# 无进程监听 → Caddy 连不上容器 → 502 Bad Gateway。
# 现在 Nginx 先启动，Reflex 未就绪时 Nginx 返回自身的 502 错误页，
# 但至少 Caddy 能成功建立连接，不会直接向用户显示 Bad Gateway。
echo "[start.sh] 启动 Nginx..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# ── 清理编译缓存（仅首次启动或缓存损坏时） ────────────────────────────
# 之前每次启动都 rm -rf /app/.web，导致每次重启都要重新编译前端（~11s），
# 大幅延长启动窗口。现在只在缓存标记文件不存在时清理。
if [ -f /app/.web/.cache_valid ]; then
    echo "[start.sh] 复用已有编译缓存，跳过清理..."
else
    echo "[start.sh] 清理旧构建缓存..."
    rm -rf /app/.web
fi

# ── 启动 Reflex ──────────────────────────────────────────────────────────
echo "[start.sh] 启动 Reflex (生产模式)..."
# --single-port 模式下前后端共享同一端口，无需显式指定 --backend-port
reflex run --env prod --single-port --frontend-port 8000 &
REFLEX_PID=$!

# ── 等待 Reflex 就绪 ────────────────────────────────────────────────────
echo "[start.sh] 等待 Reflex 就绪..."
READY=0
for i in $(seq 1 60); do
    if curl -sf -o /dev/null http://127.0.0.1:8000/api/status 2>/dev/null; then
        echo "[start.sh] Reflex 已就绪（${i}s）"
        READY=1
        break
    fi
    if ! kill -0 "$REFLEX_PID" 2>/dev/null; then
        echo "[start.sh] Reflex 进程异常退出！"
        break
    fi
    sleep 1
done

# 就绪后写入缓存标记，避免下次重启重复编译
if [ "$READY" -eq 1 ]; then
    mkdir -p /app/.web
    touch /app/.web/.cache_valid
else
    echo "[start.sh] 警告：Reflex 未能在 60s 内就绪，Nginx 将继续运行"
fi

# ── 进程守护：Nginx 退出 → 容器退出；Reflex 退出 → 自动重启 ────────────
echo "[start.sh] 监控进程状态..."
while kill -0 "$NGINX_PID" 2>/dev/null; do
    if ! kill -0 "$REFLEX_PID" 2>/dev/null; then
        echo "[start.sh] Reflex 进程意外退出，尝试重启..."
        reflex run --env prod --single-port --frontend-port 8000 &
        REFLEX_PID=$!
    fi
    sleep 2
done

echo "[start.sh] Nginx 退出，容器关闭"
exit 1
