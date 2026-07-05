#!/bin/bash
# F-D-005 协作者权限 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-005" "协作者权限" "${SCRIPT_DIR}/test_F_D_005_collab_perm.py"
exit $?
