#!/bin/bash
# F-D-002 分支保护 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-002" "分支保护" "${SCRIPT_DIR}/test_F_D_002_branch_protect.py"
exit $?
