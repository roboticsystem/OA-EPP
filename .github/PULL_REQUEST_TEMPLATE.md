## 功能描述

**关联 Issue**：F-D-009

**功能概述**：
<!-- 简要描述本次 PR 实现的功能 -->

---

## 变更文件清单

<!-- 列出本次修改/新增的文件，并说明每处变更的目的 -->

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `oaepp/states/commitlint.py` | 新增/修改 | Commitlint 配置状态管理 |
| `oaepp/pages/commitlint.py` | 新增/修改 | 配置向导页面组件 |
| `tests/reflex/test_F_D_009_commitlint.py` | 新增 | TDD 测试用例 |
| `prototype/commitlint.html` | 新增 | 功能原型文件 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 修改 | 替换为功能 PR 模板 |

---

## 自检清单

- [ ] 仅修改了允许的文件（`oaepp/pages/`、`oaepp/states/`、`tests/reflex/`、`prototype/`）
- [ ] 未修改禁止文件（`oaepp/models/`、`oaepp/components/`、`oaepp/app.py`、`backend/` 等）
- [ ] 函数命名遵循 `{模块名}_page()` / `{模块名}State` 约定
- [ ] 原型文件与页面文件命名一致
- [ ] 本地 `reflex run` 测试通过
- [ ] 测试用例全部通过

---

## 测试说明

<!-- 描述测试覆盖范围和测试方法 -->

---

## 截图（可选）

<!-- 如有界面截图，请粘贴在此 -->
