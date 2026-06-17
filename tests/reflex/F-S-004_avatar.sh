#!/bin/bash
# F-S-004 头像上传 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-004" "头像上传" "${SCRIPT_DIR}/test_F_S_004_avatar.py"
exit $?
