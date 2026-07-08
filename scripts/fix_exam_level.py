#!/usr/bin/env python3
"""将表格中考核等级全部修改为'优秀'"""
import glob
from docx import Document

files = glob.glob("/Users/mac/Desktop/OA-EPP/成信教务函*名师*申报表*.docx")
if not files:
    print("ERROR: file not found")
    exit(1)

src_path = files[0]
print(f"处理文件: {src_path}")

doc = Document(src_path)

# 表格1是考核等级所在表
table = doc.tables[1]

# 行2: 考核等级标题行
# 行3-7: 2025-2021年考核等级（列5-9）
print(f"表格1: {len(table.rows)}行 x {len(table.columns)}列")

# 先查看行2的合并情况
print("\n行2（标题行）:")
for ci in range(10):
    cell = table.rows[2].cells[ci]
    print(f"  列{ci}: text='{cell.text.strip()}'")

# 查看行3-7
modified_count = 0
for ri in range(3, 8):  # rows 3-7
    print(f"\n行{ri}（处理后）:")
    for ci in range(5, 10):  # columns 5-9
        cell = table.rows[ri].cells[ci]
        old = cell.text.strip()
        if old == "":
            cell.text = "优秀"
            modified_count += 1
            print(f"  列{ci}: '' → '优秀'")
        else:
            print(f"  列{ci}: '{old}' (未修改)")

# 保存为新文件（保留原文件）
out_path = src_path.replace(".docx", "_已修改.docx")
if out_path == src_path:
    out_path = src_path.replace(".docx", "_已修改.docx")
doc.save(out_path)
print(f"\n✅ 共修改 {modified_count} 个单元格")
print(f"✅ 已保存: {out_path}")
