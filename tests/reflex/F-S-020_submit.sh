#!/bin/bash
# F-S-020 作业提交 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-020" "作业提交" "${SCRIPT_DIR}/test_F_S_020_submit.py"
exit $?
