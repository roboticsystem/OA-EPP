#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# F-S-050 响应式布局与网络韧性 — VS Code 终端一键测试脚本
#
# 使用方式（在 VS Code 终端中执行）：
#   bash tests/reflex/F_S_050_test.sh
#
# 脚本会自动：
#   1. 定位 Python 解释器
#   2. 安装缺失依赖
#   3. 运行 TDD 自动化测试（F_S_050 + F_S_051）
#   4. 输出红绿灯结果
# ══════════════════════════════════════════════════════════════════════════════

set -e

# ── 颜色定义 ──────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── 定位项目根目录 ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║   F-S-050  响应式布局 & 网络韧性 — 自动化测试             ║${NC}"
echo -e "${BOLD}${CYAN}║   分支: F_S_050  关联: #19                                  ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: 定位 Python ──────────────────────────────────────────────────
echo -e "${BOLD}[1/4]${NC} 检测 Python 环境..."

PYTHON=""
for candidate in \
    "python" \
    "python3" \
    "py" \
    "/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe" \
    "/c/Program Files/Python312/python.exe"; do
    if command -v "$candidate" &>/dev/null || [ -x "$candidate" ]; then
        ver=$("$candidate" --version 2>&1) || continue
        PYTHON="$candidate"
        echo -e "  ${GREEN}✓${NC} 找到: ${PYTHON}  (${ver})"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}✗${NC} 未找到 Python，请先安装 Python 3.10+"
    echo "    安装方式: winget install Python.Python.3.12"
    exit 1
fi

# ── Step 2: 安装依赖 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[2/4]${NC} 检查依赖..."

REQUIRED_PKGS="pytest pytest-asyncio reflex sqlmodel aiomysql pymysql bcrypt"
MISSING=""
for pkg in $REQUIRED_PKGS; do
    if ! "$PYTHON" -c "import ${pkg//-/_}" 2>/dev/null; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo -e "  ${YELLOW}⚠${NC}  安装缺失依赖:${MISSING}"
    "$PYTHON" -m pip install --quiet $MISSING 2>&1 | tail -3
    echo -e "  ${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "  ${GREEN}✓${NC} 所有依赖已就绪"
fi

# ── Step 3: 环境变量 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/4]${NC} 配置测试环境变量..."

# 从项目 .env 加载数据库配置（如果存在）
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi
# 测试环境覆盖（SQLite 内存数据库，不依赖远程 MySQL）
export REFLEX_DB_URL="sqlite:///:memory:"
export PYTHONPATH="${PROJECT_ROOT}"

echo -e "  ${GREEN}✓${NC} 环境变量已设置"

# ── Step 4: 运行测试 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/4]${NC} 运行 TDD 测试..."
echo ""
echo -e "  ${CYAN}────────────────────────────────────────────${NC}"

cd "${PROJECT_ROOT}"

PASS_COUNT=0
FAIL_COUNT=0
FAILED_TESTS=""

# 测试 1: F_S_050 响应式布局
echo ""
echo -e "${BOLD}  测试组 1: F_S_050 响应式布局${NC}"
echo ""
if "$PYTHON" -m pytest tests/reflex/test_F_S_050_responsive.py \
    -v --tb=short --no-header \
    --rootdir="${PROJECT_ROOT}/tests/reflex" 2>&1; then
    PASS_COUNT=$((PASS_COUNT + 3))
    echo ""
    echo -e "    ${GREEN}${BOLD}🟢 F_S_050 全部通过 (3/3)${NC}"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILED_TESTS="$FAILED_TESTS  - F_S_050_responsive\n"
fi

# 测试 2: F_S_051 异常提示/网络韧性
echo ""
echo -e "${BOLD}  测试组 2: F_S_051 异常提示 & 网络韧性${NC}"
echo ""
if "$PYTHON" -m pytest tests/reflex/test_F_S_051_error.py \
    -v --tb=short --no-header \
    --rootdir="${PROJECT_ROOT}/tests/reflex" 2>&1; then
    PASS_COUNT=$((PASS_COUNT + 4))
    echo ""
    echo -e "    ${GREEN}${BOLD}🟢 F_S_051 全部通过 (4/4)${NC}"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILED_TESTS="$FAILED_TESTS  - F_S_051_error\n"
fi

# 回归测试: F_S_022 截止规则（确保未破坏已有功能）
echo ""
echo -e "${BOLD}  测试组 3: F_S_022 截止规则（回归验证）${NC}"
echo ""
if "$PYTHON" -m pytest tests/reflex/test_F_S_022_deadline.py \
    -v --tb=short --no-header \
    --rootdir="${PROJECT_ROOT}/tests/reflex" 2>&1; then
    PASS_COUNT=$((PASS_COUNT + 4))
    echo ""
    echo -e "    ${GREEN}${BOLD}🟢 F_S_022 全部通过 (4/4) — 无回归${NC}"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILED_TESTS="$FAILED_TESTS  - F_S_022_deadline\n"
fi

echo ""
echo -e "  ${CYAN}────────────────────────────────────────────${NC}"

# ── 结果汇总 ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║              测 试 结 果 汇 总                              ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}  ✅ 全部通过 — ${PASS_COUNT} 个测试${NC}"
    echo ""
    echo -e "  ${GREEN}  自动化测试已通过，请继续执行手动测试：${NC}"
    echo -e "  ${GREEN}    1. 响应式布局测试（见下方步骤）${NC}"
    echo -e "  ${GREEN}    2. 网络韧性测试（见下方步骤）${NC}"
    echo ""
    echo -e "  ${BOLD}手动测试步骤:${NC}"
    echo -e "    ${CYAN}cd oaepp${NC}"
    echo -e "    ${CYAN}reflex run${NC}"
    echo -e "    然后按测试指南逐项验证"
else
    echo -e "  ${RED}${BOLD}  ❌ ${FAIL_COUNT} 组测试失败${NC}"
    echo -e "  ${RED}失败项目:${NC}"
    echo -e "  ${RED}${FAILED_TESTS}${NC}"
fi

echo ""
exit $FAIL_COUNT
