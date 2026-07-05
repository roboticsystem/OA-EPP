#!/bin/bash
# F-T-008 教师成绩导出 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-008" "教师成绩导出" "${SCRIPT_DIR}/test_F_T_008_grade_export.py"
exit $?
