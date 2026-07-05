#!/bin/bash
# F-T-011 需求转 Issues — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-011" "需求转Issues" "${SCRIPT_DIR}/test_F_T_011_issues_gen.py"
exit $?
