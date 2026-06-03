#!/bin/bash
# F-S-050 响应式布局 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-050" "响应式布局" "${SCRIPT_DIR}/test_F_S_050_responsive.py"
exit $?
