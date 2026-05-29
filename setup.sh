#!/usr/bin/env bash
# ============================================================
# OA-EPP 一次性环境配置
# 用法：bash setup.sh
# 修复 pip/python 找不到的问题
# ============================================================

echo "======================================"
echo "  OA-EPP 环境配置"
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# ── 1. 确保虚拟环境存在且正常 ────────────────────────────
echo ""
echo "[1/3] 检查虚拟环境..."
if [ -f "$VENV_DIR/Scripts/python.exe" ]; then
    echo "  ✅ 虚拟环境已存在"
    "$VENV_DIR/Scripts/python.exe" --version
else
    echo "  ⚠ 虚拟环境不存在，正在创建..."
    python3 -m venv "$VENV_DIR" 2>/dev/null || python -m venv "$VENV_DIR" 2>/dev/null || {
        echo "  ❌ 无法创建虚拟环境，请安装 Python: https://www.python.org/downloads/"
        exit 1
    }
fi

# ── 2. 安装依赖 ─────────────────────────────────────────
echo ""
echo "[2/3] 安装项目依赖..."

# 检查并设置 pip 镜像源
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
"$VENV_DIR/Scripts/pip" install -i "$PIP_MIRROR" -r "$SCRIPT_DIR/requirements.txt" -q 2>&1 | tail -1
echo "  ✅ 根目录依赖已安装"

if [ -f "$SCRIPT_DIR/backend/requirements.txt" ]; then
    "$VENV_DIR/Scripts/pip" install -i "$PIP_MIRROR" -r "$SCRIPT_DIR/backend/requirements.txt" -q 2>&1 | tail -1
    echo "  ✅ 后端依赖已安装"
fi

# ── 3. 修复 Windows Store Python 占位程序 ────────────────
echo ""
echo "[3/3] 处理 Windows Store Python 占位程序..."
echo "  提示：你的系统 PATH 中可能存在 Windows Store Python 占位程序，"
echo "  这些占位程序会导致 python/pip 命令无法正常工作。"
echo ""
echo "  请手动执行以下操作来禁用它们："
echo "    设置 → 应用 → 应用执行别名 → 关闭 python.exe 和 python3.exe"
echo ""
echo "  或在 PowerShell（管理员）中运行："
echo '    Remove-Item "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe"'
echo '    Remove-Item "$env:LOCALAPPDATA\Microsoft\WindowsApps\python3.exe"'
echo ""

# ── 写入 shell 配置 ─────────────────────────────────────
PROFILE_FILE=""
if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        PROFILE_FILE="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        PROFILE_FILE="$HOME/.bash_profile"
    fi
fi

ALIAS_LINE="alias oa-activate='source \"$SCRIPT_DIR/activate.sh\"'"

if [ -n "$PROFILE_FILE" ] && ! grep -q "oa-activate" "$PROFILE_FILE" 2>/dev/null; then
    echo "# OA-EPP 快捷激活" >> "$PROFILE_FILE"
    echo "$ALIAS_LINE" >> "$PROFILE_FILE"
    echo "  ✅ 已在 $PROFILE_FILE 中添加快捷命令：oa-activate"
    echo "    重新打开终端后，输入 oa-activate 即可激活项目环境"
else
    echo "  提示：每次启动项目时，先运行："
    echo "    source \"$SCRIPT_DIR/activate.sh\""
fi

echo ""
echo "======================================"
echo "  ✅ 环境配置完成"
echo "======================================"
