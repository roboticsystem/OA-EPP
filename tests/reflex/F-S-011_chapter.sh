#!/bin/bash
# F-S-011 章节内容 — TDD 测试运行器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
run_feature_tests "F-S-011" "章节内容" "${SCRIPT_DIR}/test_F_S_011_chapter.py"
exit $?
