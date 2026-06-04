#!/bin/bash
# F-T-014 在线批改 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-014" "在线批改" "${SCRIPT_DIR}/test_F_T_014_grading.py"
exit $?
