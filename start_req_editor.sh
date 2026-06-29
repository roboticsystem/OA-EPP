#!/bin/bash
# ============================================================
# F-T-006 需求文档编辑器 — 本地启动脚本
# 在 VS Code 终端中直接运行: bash start_req_editor.sh
# ============================================================
set -e

# 定位到 oaepp 项目目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/oaepp"

echo "=============================================="
echo "  F-T-006 需求文档编辑器 — 启动中..."
echo "=============================================="
echo ""
echo "  Python:  $(python --version)"
echo "  目录:    $(pwd)"
echo ""

# 检查依赖
echo "[1/3] 检查依赖..."
python -c "import reflex; import markdown; print('  reflex + markdown OK')" 2>&1 || {
    echo "  依赖缺失，正在安装..."
    pip install reflex markdown sqlmodel pymysql -q
}

# 验证 State 可导入
echo "[2/3] 验证模块..."
python -c "
from oaepp.states.teacher_req_editor import ReqEditorState
from oaepp.pages.req_editor import req_editor_page
print('  ReqEditorState OK')
print('  req_editor_page  OK')
"

# 启动 Reflex 开发服务器
echo "[3/3] 启动 Reflex 开发服务器..."
echo ""
echo "  ============================================"
echo "   页面地址: http://localhost:8000/req-editor"
echo "   首页地址: http://localhost:8000/"
echo "  ============================================"
echo ""
echo "  按 Ctrl+C 停止服务器"
echo ""

reflex run --frontend-port 8000 --backend-port 8000
