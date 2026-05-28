#!/bin/bash
# F-D-003 Secrets 管理 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-003" "Secrets管理" "${SCRIPT_DIR}/test_F_D_003_secrets.py"
exit $?
