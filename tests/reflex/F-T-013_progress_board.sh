#!/bin/bash
# F-T-013 进度看板 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-013" "进度看板" "${SCRIPT_DIR}/test_F_T_013_progress_board.py"
exit $?
