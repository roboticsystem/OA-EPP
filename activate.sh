#!/usr/bin/env bash
# ============================================================
# 激活 OA-EPP 虚拟环境
# 用法：source activate.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 未找到虚拟环境，正在创建..."
    # 查找可用的 Python（跳过 Windows Store 占位程序）
    if command -v python3 &>/dev/null && ! python3 -c "print(1)" &>/dev/null 2>&1; then
        echo "  系统 python3 是 Windows Store 占位程序，跳过..."
    fi
    # 尝试直接查找已安装的 Python
    for py in \
        "$HOME/AppData/Local/Programs/Python/Python313/python.exe" \
        "$HOME/AppData/Local/Programs/Python/Python312/python.exe" \
        "$HOME/AppData/Local/Programs/Python/Python311/python.exe" \
        "/c/Program Files/Python313/python.exe" \
        "/c/Program Files/Python312/python.exe" \
        "/c/Python313/python.exe"; do
        if [ -x "$py" ]; then
            PYTHON="$py"
            break
        fi
    done
    if [ -z "$PYTHON" ]; then
        echo "❌ 未找到可用的 Python 解释器，请先安装 Python"
        echo "   下载地址：https://www.python.org/downloads/"
        exit 1
    fi
    echo "  使用 Python: $PYTHON"
    "$PYTHON" -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
fi

# 升级 pip（静默）
python -m pip install --upgrade pip -q 2>/dev/null

echo "✅ OA-EPP 虚拟环境已激活"
echo "   Python: $(python --version 2>&1)"
echo "   pip:    $(pip --version 2>&1)"
echo ""
echo "   退出虚拟环境：deactivate"
