#!/bin/bash
# F-D-004 CI 自动化 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-004" "CI自动化" "${SCRIPT_DIR}/test_F_D_004_ci.py"
exit $?
