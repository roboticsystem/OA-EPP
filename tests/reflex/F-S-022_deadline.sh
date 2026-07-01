#!/bin/bash
# F-S-022 截止时间规则 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-022" "截止时间规则" "${SCRIPT_DIR}/test_F_S_022_deadline.py"
exit $?
