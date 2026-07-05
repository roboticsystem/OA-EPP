#!/bin/bash
# F-T-005 学生名单导入 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-005" "学生名单导入" "${SCRIPT_DIR}/test_F_T_005_roster_import.py"
exit $?
