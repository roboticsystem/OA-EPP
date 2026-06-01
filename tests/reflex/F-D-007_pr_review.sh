#!/bin/bash
# F-D-007 PR 审查提示词 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-007" "PR审查提示词" "${SCRIPT_DIR}/test_F_D_007_pr_review.py"
exit $?
