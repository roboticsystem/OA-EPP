---
marp: true
theme: default
paginate: true
---

<!-- 幻灯片 1: 封面 -->

# F-D-009 Commit 消息格式自动校验

**工程实践4 · 邹圣杰**

**成都信息工程大学**

**2026年6月**

---

<!-- 幻灯片 2: 目录 -->

## 目录

1. 课题背景与痛点
2. 需求概述
3. 系统架构
4. 数据库设计
5. 功能演示
6. 技术亮点
7. TDD 测试结果
8. 项目总结

---

<!-- 幻灯片 3: 课题背景 -->

## 课题背景

### 为什么需要 Commit 消息格式校验？

45 人协作开发同一仓库，commit 消息面临三大问题：

```
😵 Git log 中常见的混乱 commit 消息：

  1. "fix bug"            → 修的什么 bug？
  2. "update"             → 更新了什么？
  3. "WIP"                → 进行中的什么工作？
  4. "11111"              → 无意义
  5. "提交代码"           → 中文，但缺少 type 标识
```

### 本功能的解决方案

| 问题 | 解决方式 |
|------|---------|
| 格式不统一 | 强制 Conventional Commits 规范 |
| 无自动化检查 | GitHub Actions + commitlint 自动校验 |
| 无法阻断不合规 | 不合规 commit → CI 失败 → PR 无法合并 |

---

<!-- 幻灯片 4: 需求概述 -->

## 需求概述

### F-D-009 包含 5 个核心子功能

| 编号 | 功能 | 说明 |
|------|------|------|
| F-D-009-01 | **配置向导** | 选择 Conventional Commits / 自定义规则集，编辑 type/header/subject |
| F-D-009-02 | **配置文件生成** | 一键生成 `.commitlintrc.json` + `commitlint.yml` |
| F-D-009-03 | **推送到仓库** | 通过 GitHub Contents API 写入指定分支 |
| F-D-009-04 | **CI 联动** | 启用=error（阻断），停用=0（跳过） |
| F-D-009-05 | **状态展示** | 显示启用状态、规则版本、最近 5 次失败记录 |

---

<!-- 幻灯片 5: 系统架构 -->

## 系统架构

```
┌─────────────────────────────────────────────┐
│         教师前端 (teacher.html)               │
│  [状态展示] [配置编辑] [分支选择] [失败记录]   │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│          FastAPI 后端 (commitlint 路由)       │
│  10 个接口：config / toggle / generate /      │
│  push / save-and-push / status / failures /  │
│  branches / repo-status                      │
└──────┬──────────────┬──────────────┬─────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼──────┐
│ commitlint  │ │ GitHub API │ │  MySQL    │
│ 引擎 (核心) │ │ Contents   │ │ 配置存储  │
│ 生成配置    │ │ 文件推送   │ │ commitlint│
└─────────────┘ └────────────┘ │ _configs  │
                               └───────────┘
```

---

<!-- 幻灯片 6: 数据库设计 -->

## 数据库设计

### commitlint_configs 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| course_id | BIGINT UNIQUE | 所属课程 |
| rule_set | ENUM | `conventional` / `custom` |
| header_max_len | INT | 默认 100 |
| subject_min_len | INT | 默认 5 |
| type_enum_json | JSON | type 枚举列表 |
| enabled | TINYINT | 启用/停用 |
| config_version | INT | 自增版本号 |

### 字段映射机制

```
rule_type  ←──→ rule_set        (命名风格转换)
type_enum  ←──→ type_enum_json  (JSON 序列化)
rule_version ←──→ config_version (版本号)
```

---

<!-- 幻灯片 7: 功能演示 — 配置向导 -->

## 功能演示① — 配置向导

```
┌──────────────────────────────────────────────┐
│  ✅ Commit 消息格式自动校验（F-D-009）        │
│                            🟢 已启用          │
├──────────────────────────────────────────────┤
│  启用状态  规则版本  规则类型   Type 数量       │
│  已启用    v2       Custom    6 个             │
├──────────────────────────────────────────────┤
│  规则集: [Conventional Commits 标准      ▼]   │
│  版本: v2 (只读)                              │
│                                              │
│  Type: feat fix refactor style test chore    │
│  [__________] [+ 添加]                        │
│                                              │
│  Header 最大长度: [100]   Subject 最小长度: [5]│
│                                              │
│  [💾保存] [📤保存并提交] [⚡预览]  [⬆提交]   │
└──────────────────────────────────────────────┘
```

---

<!-- 幻灯片 8: 功能演示 — 生成配置与推送 -->

## 功能演示② — 生成配置与推送

### 生成的 commitlintrc.json

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [2, "always", ["feat", "fix", "refactor"]],
    "subject-min-length": [2, "always", 5],
    "header-max-length": [2, "always", 100]
  }
}
```

### 生成的 commitlint.yml

```yaml
name: Commit Message 检查
on: [pull_request]
jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: wagoid/commitlint-github-action@v5
```

### 推送后仓库状态

```
📡 仓库同步状态
✅ commitlint.yml     ✅ .commitlintrc.json
📎 查看 commit  |  📜 查看 Git 历史
```

---

<!-- 幻灯片 9: 技术亮点 -->

## 技术亮点

### 亮点 1：Contents API 替代 Git Data API

| 方案 | 步骤 | 状态 |
|------|------|------|
| ❌ Git Data API | POST /git/blobs → POST /git/trees → POST /git/commits → PATCH /git/refs | 403 权限不足 |
| **✅ Contents API** | **PUT /repos/{owner}/{repo}/contents/{path}** | **1 步完成** |

### 亮点 2：CI 联动策略

```
启用 (enabled=1)          停用 (enabled=0)
    │                          │
    ▼                          ▼
规则 level = 2 (error)    规则 level = 0 (关闭)
    │                          │
    ▼                          ▼
不合规 commit → CI ❌    CI 跳过校验 → CI ✅
PR 无法合并                PR 可正常合并
```

### 亮点 3：MySQL 列名映射

前端字段 `rule_type` → MySQL 列 `rule_set`，通过 `_FRONTEND_TO_MYSQL` 字典双向转换，避免前后端命名冲突。

---

<!-- 幻灯片 10: TDD 测试结果 -->

## TDD 测试结果

### 5/5 全部通过 ✅

```bash
test_F_D_009_TC01_state_attrs_exist      ✅ PASSED
test_F_D_009_TC02_save_config_method     ✅ PASSED
test_F_D_009_TC03_type_enum_validation   ✅ PASSED
test_F_D_009_TC04_header_max_length      ✅ PASSED
test_F_D_009_TC05_recent_failures        ✅ PASSED
```

### F-D-009 模块覆盖率

| 模块 | 覆盖率 |
|------|--------|
| commitlint_engine.py | **100%** |
| devops_commitlint.py | **100%** |
| failures_store.py | 87% |
| commitlint.py (路由) | 83% |

---

<!-- 幻灯片 11: 核心代码文件 -->

## 核心代码文件

| 文件 | 代码量 | 职责 |
|------|--------|------|
| `routers/commitlint.py` | 480 行 | 10 个 API 路由 |
| `github_client.py` | 185 行 | GitHub API 封装 |
| `failures_store.py` | 47 行 | 失败记录存储 |
| `commitlint_engine.py` | 46 行 | 配置生成引擎 |
| `devops_commitlint.py` | 36 行 | Reflex State |
| `test_F_D_009_commitlint.py` | 68 行 | 5 个 TDD 测试 |
| `teacher.html` (commitlint 部分) | ~200 行 | 前端界面 |

---

<!-- 幻灯片 12: 项目总结 -->

## 项目总结

### 已完成 ✅

- 配置向导（规则集 + 参数在线编辑）
- 配置文件生成（commitlintrc + workflow）
- GitHub Contents API 推送
- CI 联动（启用→阻断，停用→跳过）
- 状态展示 + 分支选择器
- TDD 测试 5/5 通过

### 未完成 ⏳

- GitHub 推送需要仓库 Write 权限（等待管理员授权）
- 失败记录从本地 JSON 迁移到 MySQL 表

### 收获

- 深入理解 Conventional Commits 规范和 commitlint 工具
- 掌握 GitHub REST API（Contents API）的集成方法
- 理解前后端字段名映射机制的设计模式
- 实践 TDD 开发流程（RED → GREEN → REFACTOR）

---

<!-- 幻灯片 13: Q&A -->

## Q&A

### 感谢聆听，欢迎提问！

**项目仓库**：https://github.com/uwislab/robotics-systems-course

**代码路径**：
- `backend/app/routers/commitlint.py`
- `backend/app/github_client.py`
- `oaepp/states/commitlint_engine.py`

---

<!-- 幻灯片 14: 留白 -->

>

```
   ___ ___   __  _   ___  _    ___
  / __|_ _| / _|| | | _ \| |  |_  )
 | (__ | | | (_ | |_|  _/| |__ / /
  \___|___| \__|____|_|  |____/___|
  __  __    _    ___  ___  ___
 / _|/ _|  /_\  | _ \/ __|| _ \
|  _|  _| / _ \ |  _/\__ \|  _/
|_| |_|  /_/ \_\|_|  |___/|_|

 邹圣杰 · 工程实践4 · F-D-009
```
