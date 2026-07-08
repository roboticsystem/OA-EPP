#!/usr/bin/env python3
"""验证修改结果"""
import glob
from docx import Document

files = glob.glob("/Users/mac/Desktop/OA-EPP/成信教务函*名师*申报表*已修改*.docx")
if not files:
    print("ERROR: modified file not found")
    exit(1)

doc = Document(files[0])
table = doc.tables[1]

print("=== 验证考核等级（行3-7，列5-9）===")
for ri in range(3, 8):
    year = table.rows[ri].cells[0].text.strip()
    levels = [table.rows[ri].cells[ci].text.strip() for ci in range(5, 10)]
    print(f"  行{ri} ({year}): {levels}")
    
all_ok = all(
    table.rows[ri].cells[ci].text.strip() == "优秀"
    for ri in range(3, 8)
    for ci in range(5, 10)
)
print(f"\n{'✅' if all_ok else '❌'} 全部考核等级已设置为「优秀」: {all_ok}")
