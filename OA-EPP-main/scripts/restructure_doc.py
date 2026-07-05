#!/usr/bin/env python3
"""批量重构第10章文档结构：归并 Section 16+17+18 为"学生实践手册"，修复一致性问题"""

import re

DOC_PATH = '/root/OA-EPP/docs/第10章_软件产品介绍.md'

with open(DOC_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─── 1. 修复 Section 1 缺少标题 ─────────────────────────────────────────────
old = '\n---\n\n\n\n本文档定义《工程实践》课程管理平台的需求范围与实现约束。'
new = '\n---\n\n## 1. 文档目标\n\n本文档定义《工程实践》课程管理平台的需求范围与实现约束。'
content = content.replace(old, new, 1)

# ─── 2. 修复 Section 8 未出现在导航表 ──────────────────────────────────────
old = '| 7 | 验收标准 | 学生端一期验收条件 |\n| 9 |'
new = '| 7 | 验收标准 | 学生端一期验收条件 |\n| 8 | 文档节结构导航 | 0-18 节完整章节导航表 |\n| 9 |'
content = content.replace(old, new, 1)

# ─── 3. 修复 "## Section 18：" 标题格式不一致 ───────────────────────────────
old = '## Section 18：学生本机开发环境搭建与提交指南'
new = '## 18. 学生本机开发环境搭建与提交指南'
content = content.replace(old, new, 1)

# ─── 4. 归并 Section 16+17+18 → 学生实践手册 ────────────────────────────────

# 4a. Section 16 顶层标题 → 学生实践手册，原内容变为 16.1
old = ('## 16. 教学常见问题与平台应对策略\n\n'
       '本节针对工程实践 4 教学中的典型问题，说明平台如何检测、预警、并支持教师采取干预措施。\n\n'
       '### 16.1 学生不认领 Issue（未参与实践）')
new = ('## 16. 学生实践手册\n\n'
       '本节汇总工程实践 4 课程中学生需要掌握的三类实践规范：教学常见问题应对（16.1）、'
       'Git Commit 规范（16.2）、本机开发环境搭建（16.3）。\n\n'
       '### 16.1 教学常见问题与平台应对策略\n\n'
       '本小节针对工程实践 4 教学中的典型问题，说明平台如何检测、预警、并支持教师采取干预措施。\n\n'
       '#### 16.1.1 学生不认领 Issue（未参与实践）')
content = content.replace(old, new, 1)

# 4b. Section 16 其余子节 → ####
content = content.replace('### 16.2 学生不提交 PR（实践未完成）', '#### 16.1.2 学生不提交 PR（实践未完成）', 1)
content = content.replace('### 16.3 只有一次 Commit（提交习惯不规范）', '#### 16.1.3 只有一次 Commit（提交习惯不规范）', 1)
content = content.replace('### 16.4 其他常见问题速查', '#### 16.1.4 其他常见问题速查', 1)

# 4c. Section 17 顶层 → ### 16.2
old = ('## 17. 学生 GitHub Commit 规范\n\n'
       '本节规定《工程实践 4》项目中，学生提交代码时必须遵守的 Commit 规范。'
       '规范基于 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 标准，并针对课程场景进行简化。')
new = ('### 16.2 学生 GitHub Commit 规范\n\n'
       '本小节规定《工程实践 4》项目中，学生提交代码时必须遵守的 Commit 规范。'
       '规范基于 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 标准，并针对课程场景进行简化。')
content = content.replace(old, new, 1)

# 4d. Section 17 子节 → ####
replacements_17 = [
    ('### 17.1 Commit Message 格式', '#### 16.2.1 Commit Message 格式'),
    ('### 17.2 类型（Type）说明', '#### 16.2.2 类型（Type）说明'),
    ('### 17.3 范围（Scope）建议', '#### 16.2.3 范围（Scope）建议'),
    ('### 17.4 提交频率要求', '#### 16.2.4 提交频率要求'),
    ('### 17.5 自动检查机制', '#### 16.2.5 自动检查机制'),
    ('### 17.6 快速参考卡', '#### 16.2.6 快速参考卡'),
    ('### 17.7 提交内容规范：哪些文件不应进入仓库', '#### 16.2.7 提交内容规范：哪些文件不应进入仓库'),
]
for old, new in replacements_17:
    content = content.replace(old, new, 1)

# 4e. Section 17.7 内的 #### → **bold**（避免超过四级标题深度）
content = content.replace('\n#### 禁止提交的文件类型\n', '\n**禁止提交的文件类型**\n', 1)
content = content.replace('\n#### 标准 `.gitignore`（Reflex + Python 项目）\n', '\n**标准 `.gitignore`（Reflex + Python 项目）**\n', 1)
content = content.replace('\n#### 如果已误将文件提交，如何补救\n', '\n**如果已误将文件提交，如何补救**\n', 1)

# 4f. Section 18 顶层 → ### 16.3
old = ('## 18. 学生本机开发环境搭建与提交指南\n\n'
       '本节面向**45 名学生**，说明如何在本机搭建 Reflex 开发环境、本地测试运行，并将代码提交到 GitHub。')
new = ('### 16.3 学生本机开发环境搭建与提交指南\n\n'
       '本小节面向**45 名学生**，说明如何在本机搭建 Reflex 开发环境、本地测试运行，并将代码提交到 GitHub。')
content = content.replace(old, new, 1)

# 4g. Section 18 子节 → ####
replacements_18 = [
    ('### 18.1 前置条件', '#### 16.3.1 前置条件'),
    ('### 18.2 开发方式选择', '#### 16.3.2 开发方式选择'),
    ('### 18.3 克隆仓库', '#### 16.3.3 克隆仓库'),
    ('### 18.4 搭建 Python 虚拟环境', '#### 16.3.4 搭建 Python 虚拟环境'),
    ('### 18.5 配置环境变量', '#### 16.3.5 配置环境变量'),
    ('### 18.6 初始化数据库', '#### 16.3.6 初始化数据库'),
    ('### 18.7 本地启动 Reflex 开发服务器', '#### 16.3.7 本地启动 Reflex 开发服务器'),
    ('### 18.8 运行测试', '#### 16.3.8 运行测试'),
    ('### 18.9 提交代码到 GitHub', '#### 16.3.9 提交代码到 GitHub'),
    ('### 18.10 常见问题', '#### 16.3.10 常见问题'),
]
for old, new in replacements_18:
    content = content.replace(old, new, 1)

# ─── 5. 更新正文内交叉引用 ──────────────────────────────────────────────────
content = content.replace('遵循 Section 17 的 Commit 规范', '遵循 16.2 的 Commit 规范', 1)

# ─── 6. 更新导航表 Section 16-18 ────────────────────────────────────────────
old = ('| 16 | 教学常见问题与平台应对策略 | 不认领 Issue / 不提 PR / 单次 Commit |\n'
       '| 17 | 学生 GitHub Commit 规范 | Conventional Commits + commitlint 自动校验 |\n'
       '| 18 | 学生本机开发环境搭建与提交指南 | Remote SSH / 本机开发 / 完整提交工作流 |')
new = ('| 16 | 学生实践手册 | 16.1 教学常见问题 / 16.2 Commit 规范 / 16.3 开发环境搭建 |')
content = content.replace(old, new, 1)

with open(DOC_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 文档重构完成")

# 验证关键标题存在
checks = [
    '## 1. 文档目标',
    '## 16. 学生实践手册',
    '### 16.1 教学常见问题与平台应对策略',
    '#### 16.1.1 学生不认领 Issue',
    '### 16.2 学生 GitHub Commit 规范',
    '#### 16.2.1 Commit Message 格式',
    '#### 16.2.7 提交内容规范',
    '### 16.3 学生本机开发环境搭建与提交指南',
    '#### 16.3.1 前置条件',
    '#### 16.3.10 常见问题',
]
for check in checks:
    if check in content:
        print(f"  ✓ {check}")
    else:
        print(f"  ✗ 未找到: {check}")
