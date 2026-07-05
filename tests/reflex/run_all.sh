#!/bin/bash
# tests/reflex/run_all.sh — 全量 TDD 测试主运行器
# 遍历所有 F-*.sh 并汇总结果
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

echo "========================================"
echo "  OA-EPP Reflex TDD 全量测试"
echo "========================================"
echo ""

for script in "$SCRIPT_DIR"/F-*.sh; do
    bash "$script"
    if [ $? -eq 0 ]; then
        ((PASS++)) || true
    else
        ((FAIL++)) || true
    fi
    echo ""
done

echo "========================================"
echo "  汇总：🟢 $PASS 通过 | 🔴 $FAIL 失败"
echo "========================================"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
