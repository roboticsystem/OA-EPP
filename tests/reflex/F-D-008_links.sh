#!/bin/bash
# F-D-008 快捷链接面板 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-D-008" "快捷链接面板" "${SCRIPT_DIR}/test_F_D_008_links.py"
exit $?
