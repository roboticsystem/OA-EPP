#!/bin/bash
# F-D-009 Commitlint 规则配置 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-009" "Commitlint规则配置" "${SCRIPT_DIR}/test_F_D_009_commitlint.py"
exit $?
