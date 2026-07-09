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

# ── 辅助函数 ─────────────────────────────────────────────────────────────

# 等待 Reflex 就绪。参数：Reflex 的 PID。
# 返回 0 表示就绪，1 表示超时（60s）或进程已崩溃。
wait_reflex_ready() {
    _pid="$1"
    for _i in $(seq 1 60); do
        if curl -sf -o /dev/null http://127.0.0.1:8000/api/status 2>/dev/null; then
            echo "[start.sh] Reflex 已就绪（${_i}s）"
            return 0
        fi
        if ! kill -0 "$_pid" 2>/dev/null; then
            echo "[start.sh] Reflex 进程异常退出！"
            return 1
        fi
        sleep 1
    done
    return 1
}

# 写入缓存标记，避免下次重启重复编译。
# 无论在初始启动还是守护重启后就绪，只要 Reflex 成功编译完成就写入。
mark_cache_valid() {
    mkdir -p /app/.web
    touch /app/.web/.cache_valid
    echo "[start.sh] 已写入编译缓存标记"
}

# ── 启动 Reflex ──────────────────────────────────────────────────────────

echo "[start.sh] 启动 Reflex (生产模式)..."
# --single-port 模式下前后端共享同一端口，无需显式指定 --backend-port
reflex run --env prod --single-port --frontend-port 8000 &
REFLEX_PID=$!

echo "[start.sh] 等待 Reflex 就绪..."
if wait_reflex_ready "$REFLEX_PID"; then
    mark_cache_valid
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
        echo "[start.sh] 等待 Reflex 重新就绪..."
        if wait_reflex_ready "$REFLEX_PID"; then
            mark_cache_valid
            echo "[start.sh] Reflex 已恢复"
        else
            echo "[start.sh] 警告：Reflex 重启后未能在 60s 内就绪，将继续尝试"
        fi
    fi
    # 兜底：若缓存标记尚未写入（如首次编译 >60s 但进程未崩溃），
    # 探测到 Reflex 实际已就绪时补写标记，确保后续重启复用缓存。
    if [ ! -f /app/.web/.cache_valid ] && curl -sf -o /dev/null http://127.0.0.1:8000/api/status 2>/dev/null; then
        mark_cache_valid
    fi
    sleep 2
done

echo "[start.sh] Nginx 退出，容器关闭"
exit 1
