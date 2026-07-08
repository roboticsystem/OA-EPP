#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批改嵌入式系统课程论文"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

src = "/Users/mac/Desktop/OA-EPP/《嵌入式系统》非全研究生课程报告-4250705008-黄元-基于STM32 的pwm波生成.docx"
dst = "/Users/mac/Desktop/OA-EPP/批改_嵌入式系统课程报告-4250705008-黄元-基于STM32的pwm波生成.docx"

doc = Document(src)

# ========== 评分分析 ==========

hard_fails = []

# 检查硬性不合格项
has_complete_code = False     # 只有代码片段，无完整可运行工程
has_script_diagrams = False   # 无Svgbob/PlantUML/dot图

if not has_complete_code:
    hard_fails.append("(3) 无完整示例程序")
if not has_script_diagrams:
    hard_fails.append("(8) 无 Svgbob/PlantUML/dot 等脚本图")

# 知识点错误明细
knowledge_errors = []
knowledge_errors.append({
    "location": "关键代码说明 > 超声波测距",
    "issue": "距离计算公式 (pulseWidthUs * 10U) / 116U 存在科学性错误",
    "detail": (
        "标准HC-SR04距离公式: 距离(mm) = pulseWidth(us) * 10 / 58 = pulseWidth / 5.8。"
        "学生使用116作为分母(等于2*58)，导致计算结果偏小一倍。"
        "正确公式应为 (pulseWidthUs * 10U) / 58U 或 pulseWidthUs / 5.8。"
    ),
    "deduction": 5
})

knowledge_errors.append({
    "location": "全文",
    "issue": "章节编号体系不统一",
    "detail": (
        "学习目标用'1'，实验步骤用'2'，关键代码说明用'二、'，PICSimLab步骤用'三、'，"
        "总结又回到'6'。编号体系混乱，不符合标准教材章节规范。"
    ),
    "deduction": 3
})

knowledge_errors.append({
    "location": "关键代码说明",
    "issue": "仅提供代码片段，无完整可编译工程源码",
    "detail": (
        "缺少完整的main.c、FreeRTOS任务实现、定时器初始化代码、CubeMX生成代码等。"
        "仅有几个宏定义和信号量获取片段，无法独立编译运行。"
    ),
    "deduction": 5
})

knowledge_errors.append({
    "location": "全文",
    "issue": "所有图示均为CubeMX截图，无Svgbob/PlantUML/dot脚本生成图",
    "detail": (
        "课程要求优先使用Svgbob、PlantUML、dot等脚本生成图。"
        "文中13张图全部为CubeMX/Win11截图，不符合一图二表三文字规范。"
        "缺少接线原理的Svgbob图、程序流图等。"
    ),
    "deduction": 5
})

knowledge_errors.append({
    "location": "全文",
    "issue": "全文无任何表格",
    "detail": (
        "标准要求一图二表三文字，应有表格组织引脚配置、寄存器参数、对比数据等信息。"
        "例如：引脚分配表、TIM配置参数表等。"
    ),
    "deduction": 3
})

knowledge_errors.append({
    "location": "三、PICSimLab 实验步骤",
    "issue": "PICSimLab演示步骤过于简略",
    "detail": (
        "缺少：命令行启动命令、具体的PICSimLab板卡选择、频率配置、各模块具体参数设置。"
        "结果分析部分缺少对波形和数据的具体分析。"
    ),
    "deduction": 3
})

knowledge_errors.append({
    "location": "1 学习目标",
    "issue": "学习目标阈值与代码实现不一致",
    "detail": (
        "学习目标写的是'超声波距离小于100，电机转速降低'，"
        "但代码中ULTRASONIC_LIMIT_MM定义为1000U(即1000mm)。"
        "阈值不一致(100 vs 1000)，且缺少单位说明。"
    ),
    "deduction": 2
})

# 总扣分
total_deduction = sum(e["deduction"] for e in knowledge_errors) + len(hard_fails) * 5

# 计算各维度得分
scores = {}
scores["章节结构规范性"] = max(0, 15 - 3)  # 编号不一致扣3分
scores["知识点准确性"] = max(0, 15 - 7)  # 公式错误5分+阈值不一致2分
scores["图文并茂规范"] = max(0, 20 - 8)  # 无脚本图5分+无表格3分
scores["示例程序完整性"] = max(0, 20 - 5)  # 无完整代码5分
scores["PicSimLab仿真完整性"] = max(0, 15 - 3)  # 步骤简略3分
scores["表达流畅与可读性"] = max(0, 15 - 2)  # 编号混乱2分

# 硬性不合格额外扣分
hard_deduction = len(hard_fails) * 5
total = sum(scores.values()) - hard_deduction
total = max(0, total)

print("=== 评分结果 ===")
print(f"章节结构规范性: {scores['章节结构规范性']}/15")
print(f"知识点准确性: {scores['知识点准确性']}/15")
print(f"图文并茂规范: {scores['图文并茂规范']}/20")
print(f"示例程序完整性: {scores['示例程序完整性']}/20")
print(f"PicSimLab仿真完整性: {scores['PicSimLab仿真完整性']}/15")
print(f"表达流畅与可读性: {scores['表达流畅与可读性']}/15")
print(f"硬性不合格扣分: -{hard_deduction}")
print(f"总分: {total}/100")
print(f"\n硬性不合格项: {hard_fails}")
print(f"\n知识错误明细:")
for e in knowledge_errors:
    print(f"  - {e['location']}: {e['issue']} (扣{e['deduction']}分)")
    print(f"    {e['detail']}")

# ========== 在文档末尾添加评语 ==========

doc.add_paragraph("")
doc.add_paragraph("")

# 分隔线
sep = doc.add_paragraph()
run = sep.add_run("=" * 50)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

# 红色评语标题
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_p.add_run("【教师评阅意见】")
run.bold = True
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
run.font.name = "微软雅黑"

doc.add_paragraph("")

# 总分
total_p = doc.add_paragraph()
total_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = total_p.add_run(f"总分：{total} / 100")
run.bold = True
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

doc.add_paragraph("")

# 各维度得分
def add_score_line(doc, label, score, max_score):
    p = doc.add_paragraph()
    run = p.add_run(f"{label}：{score} / {max_score}")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
    return p

add_score_line(doc, "1. 章节结构规范性", scores["章节结构规范性"], 15)
add_score_line(doc, "2. 知识点准确性", scores["知识点准确性"], 15)
add_score_line(doc, "3. 图文并茂规范", scores["图文并茂规范"], 20)
add_score_line(doc, "4. 示例程序完整性", scores["示例程序完整性"], 20)
add_score_line(doc, "5. PicSimLab 仿真完整性", scores["PicSimLab仿真完整性"], 15)
add_score_line(doc, "6. 表达流畅与可读性", scores["表达流畅与可读性"], 15)

doc.add_paragraph("")

# 主要扣分点
deduction_p = doc.add_paragraph()
run = deduction_p.add_run("主要扣分点：")
run.bold = True
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

for e in knowledge_errors:
    p = doc.add_paragraph()
    run = p.add_run(f"  \u2022 {e['issue']}（-{e['deduction']}分）")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
    p2 = doc.add_paragraph()
    run2 = p2.add_run(f"    {e['detail']}")
    run2.font.size = Pt(10)
    run2.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

doc.add_paragraph("")

# 不符合要求项
fail_p = doc.add_paragraph()
run = fail_p.add_run("不符合要求项：")
run.bold = True
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

for f in hard_fails:
    p = doc.add_paragraph()
    run = p.add_run(f"  \u2022 {f}（-5分）")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

doc.add_paragraph("")

# 综合评语
comment_p = doc.add_paragraph()
run = comment_p.add_run("综合评语：")
run.bold = True
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

comment_text = (
    "该生完成了基于STM32和FreeRTOS的超声波测距与直流电机调速实验的基本框架搭建，"
    "使用了CubeMX进行工程配置，并能在PICSimLab中进行仿真验证。"
    "主要不足包括：(1) 未提供完整的可编译运行工程源码，仅展示代码片段；"
    "(2) 超声波测距公式存在科学性错误（分母应为58而非116），导致距离计算值偏小一倍；"
    "(3) 全文无任何Svgbob/PlantUML/dot脚本生成图，所有图示均为CubeMX截图，不符合课程规范；"
    "(4) 无表格组织数据；(5) 章节编号体系混乱，不符合标准教材格式。"
    "建议补充完整工程源码，修正距离计算公式，增加Svgbob原理图和表格，统一章节编号。"
)
p = doc.add_paragraph()
run = p.add_run(comment_text)
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

# 保存为新文件
doc.save(dst)
print(f"\n✅ 已保存批改后文档: {dst}")
print(f"文件大小: {os.path.getsize(dst) / 1024:.1f} KB")
