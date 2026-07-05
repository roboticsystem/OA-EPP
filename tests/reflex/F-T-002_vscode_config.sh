#!/bin/bash
# F-T-002 VSCode 配置下发 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-002" "VSCode配置下发" "${SCRIPT_DIR}/test_F_T_002_vscode_config.py"
exit $?
