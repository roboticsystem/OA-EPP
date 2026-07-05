#!/bin/bash
# F-T-007 Issue-PR 关联规则 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-007" "Issue-PR关联规则" "${SCRIPT_DIR}/test_F_T_007_issue_pr.py"
exit $?
