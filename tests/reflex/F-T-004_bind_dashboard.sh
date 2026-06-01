#!/bin/bash
# F-T-004 绑定状态看板 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-004" "绑定状态看板" "${SCRIPT_DIR}/test_F_T_004_bind_dashboard.py"
exit $?
