#!/bin/bash
# tests/reflex/lib/common.sh — TDD 测试公共工具库
# 提供 run_feature_tests() 函数，显示 TDD 红绿灯状态

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

# run_feature_tests <功能点编号> <功能名称> <测试文件路径>
# 返回值: 0=GREEN, 非0=RED
run_feature_tests() {
    local feature="$1"
    local name="$2"
    local test_file="$3"

    echo ""
    echo -e "${BOLD}=== TDD 测试: ${feature} ${name} ===${NC}"
    echo "  测试文件: $(basename "${test_file}")"
    echo ""

    python -m pytest "${test_file}" -v --tb=short --no-header \
        --rootdir="$(dirname "$(dirname "${test_file}")")" 2>&1

    local rc=$?

    echo ""
    if [ "${rc}" -eq 0 ]; then
        echo -e "  ${GREEN}${BOLD}🟢 GREEN: ${feature} 全部测试通过${NC}"
    else
        echo -e "  ${RED}${BOLD}🔴 RED: ${feature} 测试失败（TDD 预期状态）${NC}"
        echo -e "  ${YELLOW}  → 请实现 oaepp/states/ 中对应的 State 类${NC}"
        echo -e "  ${YELLOW}  → 实现后重新运行此脚本，应显示 🟢 GREEN${NC}"
    fi

    return "${rc}"
}
