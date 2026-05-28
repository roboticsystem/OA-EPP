#!/bin/bash
# F-S-001 登录/退出 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-001" "登录/退出" "${SCRIPT_DIR}/test_F_S_001_login.py"
exit $?
