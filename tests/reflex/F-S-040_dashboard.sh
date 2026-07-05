#!/bin/bash
# F-S-040 得分看板 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-040" "得分看板" "${SCRIPT_DIR}/test_F_S_040_dashboard.py"
exit $?
