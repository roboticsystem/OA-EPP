#!/bin/bash
# F-T-001 GitHub 账号映射表 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-001" "GitHub账号映射表" "${SCRIPT_DIR}/test_F_T_001_github_map.py"
exit $?
