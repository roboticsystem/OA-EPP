#!/bin/sh
set -eu

cd /app

# Reflex 前后端分别监听 3000 / 8000；Nginx 对外统一暴露 80。
reflex run &
exec nginx -g 'daemon off;'