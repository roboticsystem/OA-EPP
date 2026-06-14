# F-T-002 VS Code扩展与Copilot提示词配置 — 设计文档

> 日期 2026-06-01 | 优先级 中 | 模块 教师功能 / 开发运维

## 功能概述

教师可管理课程的 VS Code 扩展清单（必装/建议/禁止），自动生成 `.vscode/extensions.json`，并编辑 Copilot 全局/模块指令文件。所有变更可一键提交到 Git 仓库并触发 CI 格式检查。

## 验收标准

1. 扩展按必装/建议/禁止分组管理，生成标准的 `extensions.json`
2. 提供 3 组预置模板（Python 开发套件、Copilot 全家桶、Reflex 开发）
3. Copilot 指令文件支持在线编辑和保存
4. 一键提交后自动触发 CI 格式检查

## 技术决策

| 决策 | 选项 | 理由 |
|------|------|------|
| 实现框架 | FastAPI + 原生 HTML | 与现有生产代码一致 |
| 数据存储 | 文件系统 + Git | 配置本质是仓库文件，天然适合版本管理 |
| 前端 | 新页面 `/vscode-config` | teacher.html 已 477 行，独立页面更好维护 |

## 架构

```
backend/app/
  routers/
    vscode_config.py      ← 新增 API 路由（~150 行）
  data/
    vscode_config.json    ← 扩展配置状态持久化
  static/
    vscode_config.html    ← 新增教师配置页（~350 行）
项目根/
  .vscode/extensions.json ← generate 写出
  .github/copilot-instructions.md  ← 直接编辑
```

## API 端点

所有端点需要教师 JWT（Bearer token），格式 `/api/teacher/*`。鉴权复用 `teacher.py` 的 `_require_teacher()`。

### 扩展管理

| 方法 | 路由 | 请求体 | 响应 |
|------|------|--------|------|
| GET | `/api/teacher/vscode/extensions` | — | `{recommendations: [...], unwantedRecommendations: [...]}` |
| POST | `/api/teacher/vscode/extensions` | `{action: "add"|"remove", group: "recommendations"|"unwanted", ext_id: str, ext_name: str, ext_desc: str}` | `{ok: true}` |
| GET | `/api/teacher/vscode/extensions/presets` | — | `{presets: [{id, name, config}]}` |
| POST | `/api/teacher/vscode/extensions/generate` | — | `{ok: true, path: ".vscode/extensions.json"}` |

### Copilot 指令

| 方法 | 路由 | 请求体 | 响应 |
|------|------|--------|------|
| GET | `/api/teacher/copilot/instructions` | — | `{files: [{path, name, size}]}` |
| GET | `/api/teacher/copilot/instructions/{path:path}` | — | `{path, content, size}` |
| POST | `/api/teacher/copilot/instructions/{path:path}` | `{content: str}` | `{ok: true}` |

### Git 操作

| 方法 | 路由 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/api/teacher/config/commit` | — | `{ok: true, sha, message}` |
| GET | `/api/teacher/config/git-status` | — | `{dirty: bool, changed_files: [...], branch: str}` |

## 数据结构

### vscode_config.json

```json
{
  "recommendations": [
    {"id": "GitHub.copilot", "name": "GitHub Copilot", "description": "AI 代码补全"}
  ],
  "unwantedRecommendations": [
    {"id": "ms-python.pylint", "name": "Pylint", "description": "与 Ruff 冲突"}
  ]
}
```

### Presets

内置于代码中，不存文件：

```python
PRESETS = {
    "python-dev": {
        "name": "Python开发套件",
        "config": {
            "recommendations": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "charliermarsh.ruff",
                "ms-python.debugpy"
            ],
            "unwantedRecommendations": ["ms-python.pylint"]
        }
    },
    "copilot-suite": {
        "name": "Copilot全家桶",
        "config": {
            "recommendations": ["GitHub.copilot", "GitHub.copilot-chat"],
            "unwantedRecommendations": []
        }
    },
    "reflex-dev": {
        "name": "Reflex开发",
        "config": {
            "recommendations": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "GitHub.copilot",
                "charliermarsh.ruff"
            ],
            "unwantedRecommendations": []
        }
    }
}
```

## 前端页面 `/vscode-config`

### 布局

```
┌─────────────────────────────────────────────┐
│  顶部栏 — 页面标题 + 导航返回教师管理          │
├───────────────────────┬─────────────────────┤
│  卡片1: 扩展管理        │  卡片2: JSON 预览     │
│  ┌─必装/建议─────────┐  │  {                  │
│  │  GitHub.copilot  ×│  │    "recommendations" │
│  │  ms-python.python ×│  │    [...]            │
│  │  ...              │  │  }                  │
│  └───────────────────┘  │  [复制JSON] [生成]   │
│  ┌─禁装──────────────┐  └─────────────────────┘
│  │  ms-python.pylint ×│
│  └───────────────────┘
│  ┌─预置模板──────────┐
│  │ Python套件 Copilot Reflex │
│  └───────────────────┘
├─────────────────────────────────────────────┤
│  卡片3: Copilot 指令编辑器                    │
│  ┌─文件选择─────────────────────────┐          │
│  │ global | per-module tabs         │          │
│  └──────────────────────────────────┘          │
│  [                          ]                 │
│  [      编辑区 (textarea)    ]                 │
│  [                          ]                 │
│  [加载] [保存] [预览渲染]                      │
├─────────────────────────────────────────────┤
│  操作栏: [提交到仓库]  [检查CI状态]              │
└─────────────────────────────────────────────┘
```

### 安全

- 页面级 JWT 校验：页面加载时从 `sessionStorage` 读取 token，向 `/api/teacher/exams` 发请求验证有效性
- 所有 API 请求携带 `Authorization: Bearer <token>`
- 写操作（POST/PUT）由后端 `_require_teacher()` 校验

## 文件读写安全

**写入路径限制：**
- `.vscode/extensions.json` — 项目根目录下
- `.github/copilot-instructions.md` — 项目根目录下
- `vscode_config.json` — `backend/app/data/` 目录下

后端禁止写入以上路径之外的文件。构建基于项目根目录（`REPO_ROOT`）的路径白名单。

## Git 操作

```python
def git_commit_push(message: str) -> dict:
    """git add .vscode/ .github/ → commit → push"""
    # 使用 subprocess.run 执行 git 命令
```

Commit message 固定格式：`chore: update VSCode & Copilot config`

## 测试策略

TDD 测试位于 `tests/reflex/test_F_T_002_vscode_config.py`，原有测试面向 Reflex State。本次改为面向 API 端点：

- TC01 — GET `/api/teacher/vscode/extensions` 返回正确结构
- TC02 — 扩展类型枚举存在（`recommendations`, `unwantedRecommendations`）
- TC03 — POST `/api/teacher/vscode/extensions/generate` 生成文件
- TC04 — POST `/api/teacher/copilot/instructions/...` 保存文件内容
- TC05 — POST `/api/teacher/config/commit` 执行 git 提交
- TC06 — 未授权请求返回 401

## 实现范围

| 包含 | 不包含 |
|------|--------|
| 扩展增删、分组管理 | 按学生分组下发不同扩展 |
| extensions.json 生成 | VS Code Settings 管理 |
| Copilot 指令文件编辑保存 | 指令模板自动生成 |
| Git commit + push | 分支管理 / PR 创建 |
| 3 组预设模板 | 自定义模板保存 |
| CI 状态查询 | CI 配置编辑 |
