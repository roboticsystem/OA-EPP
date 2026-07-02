#!/bin/sh
set -eu

cd /app

echo "[start.sh] 初始化数据库..."
python scripts/init_db_and_seed.py || echo "[start.sh] 数据库初始化失败（可能已存在），继续启动..."

echo "[start.sh] 清理旧构建缓存..."
rm -rf /app/.web

echo "[start.sh] 启动 Reflex (生产模式)..."
reflex run --env prod --single-port --frontend-port 8000 --backend-port 8000 &
REFLEX_PID=$!

# 等待 Reflex 编译完成并开始监听端口
echo "[start.sh] 等待 Reflex 就绪..."
for i in $(seq 1 60); do
    if curl -sf -o /dev/null http://127.0.0.1:8000/api/status 2>/dev/null; then
        echo "[start.sh] Reflex 已就绪（${i}s）"
        break
    fi
    if ! kill -0 "$REFLEX_PID" 2>/dev/null; then
        echo "[start.sh] Reflex 进程异常退出！"
        exit 1
    fi
    sleep 1
done

echo "[start.sh] 启动 Nginx..."
nginx -g 'daemon off;' &
NGINX_PID=$!

while kill -0 "$REFLEX_PID" 2>/dev/null && kill -0 "$NGINX_PID" 2>/dev/null; do
    sleep 1
done

exit 1