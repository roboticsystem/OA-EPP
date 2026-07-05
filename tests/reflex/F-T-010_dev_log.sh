#!/bin/bash
# F-T-010 开发日志导出 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-010" "开发日志导出" "${SCRIPT_DIR}/test_F_T_010_dev_log.py"
exit $?
