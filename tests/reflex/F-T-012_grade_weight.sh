#!/bin/bash
# F-T-012 成绩权重配置 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-T-012" "成绩权重配置" "${SCRIPT_DIR}/test_F_T_012_grade_weight.py"
exit $?
