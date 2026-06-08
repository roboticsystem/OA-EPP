#!/bin/sh
set -eu

cd /app

echo "[start.sh] 初始化数据库..."
python scripts/init_db_and_seed.py || echo "[start.sh] 数据库初始化失败（可能已存在），继续启动..."

echo "[start.sh] 启动 Reflex (生产模式)..."
reflex run --env prod --host 0.0.0.0 --port 8000 &
REFLEX_PID=$!

echo "[start.sh] 启动 Nginx..."
nginx -g 'daemon off;' &
NGINX_PID=$!

while kill -0 "$REFLEX_PID" 2>/dev/null && kill -0 "$NGINX_PID" 2>/dev/null; do
    sleep 1
done

exit 1