#!/bin/bash
# F-S-003 GitHub 账号绑定 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-003" "GitHub账号绑定" "${SCRIPT_DIR}/test_F_S_003_github_bind.py"
exit $?
