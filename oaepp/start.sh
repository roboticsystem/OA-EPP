#!/bin/sh
set -eu

cd /app

# Reflex 前后端分别监听 3000 / 8000；Nginx 对外统一暴露 80。
reflex run &
REFLEX_PID=$!

nginx -g 'daemon off;' &
NGINX_PID=$!

# 任一关键进程退出，都让容器退出（避免只剩 Nginx 欢迎页）。
# BusyBox /bin/sh 不支持 wait -n，因此用可移植轮询。
while kill -0 "$REFLEX_PID" 2>/dev/null && kill -0 "$NGINX_PID" 2>/dev/null; do
	sleep 1
done

exit 1