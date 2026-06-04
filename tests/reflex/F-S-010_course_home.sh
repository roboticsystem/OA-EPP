#!/bin/bash
# F-S-010 课程主页 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-010" "课程主页" "${SCRIPT_DIR}/test_F_S_010_course_home.py"
exit $?
