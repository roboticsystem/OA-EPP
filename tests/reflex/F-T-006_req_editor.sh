#!/bin/bash
# F-T-006 需求文档编辑器 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-006" "需求文档编辑器" "${SCRIPT_DIR}/test_F_T_006_req_editor.py"
exit $?
