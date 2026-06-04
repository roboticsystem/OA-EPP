#!/bin/bash
# F-D-006 脚本执行界面 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-006" "脚本执行界面" "${SCRIPT_DIR}/test_F_D_006_script_web.py"
exit $?
