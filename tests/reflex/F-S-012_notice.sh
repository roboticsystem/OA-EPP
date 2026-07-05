#!/bin/bash
# F-S-012 公告通知 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-012" "公告通知" "${SCRIPT_DIR}/test_F_S_012_notice.py"
exit $?
