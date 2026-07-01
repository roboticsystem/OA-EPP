#!/bin/bash
# F-S-021 提交版本记录 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-021" "提交版本记录" "${SCRIPT_DIR}/test_F_S_021_versions.py"
exit $?
