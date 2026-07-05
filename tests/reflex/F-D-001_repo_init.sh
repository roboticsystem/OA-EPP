#!/bin/bash
# F-D-001 仓库初始化 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-001" "仓库初始化" "${SCRIPT_DIR}/test_F_D_001_repo_init.py"
exit $?
