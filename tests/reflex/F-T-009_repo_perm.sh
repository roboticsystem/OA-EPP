#!/bin/bash
# F-T-009 仓库权限配置 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-009" "仓库权限配置" "${SCRIPT_DIR}/test_F_T_009_repo_perm.py"
exit $?
