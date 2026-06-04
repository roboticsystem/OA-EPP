#!/bin/bash
# F-T-003 账号实名核查 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-003" "账号实名核查" "${SCRIPT_DIR}/test_F_T_003_name_verify.py"
exit $?
