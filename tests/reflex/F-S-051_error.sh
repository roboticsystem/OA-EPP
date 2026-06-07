#!/bin/bash
# F-S-051 异常提示 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-051" "异常提示" "${SCRIPT_DIR}/test_F_S_051_error.py"
exit $?
