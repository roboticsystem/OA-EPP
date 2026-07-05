---
applyTo: '**'
---

# Commit Message 规范

所有 commit message 必须使用**中文**撰写。

## 格式

```
<类型>(<范围>): <简要描述>

<详细说明>

BREAKING CHANGE: 说明
Close #Issue编号: 7位commit哈希
```

## 类型

| 类型     | 含义                         |
|----------|------------------------------|
| feat     | 新增功能或内容               |
| fix      | 修复错误                     |
| docs     | 文档变更（教材内容修订等）   |
| style    | 格式调整（不影响功能）       |
| refactor | 代码重构                     |
| perf     | 性能优化                     |
| test     | 测试相关                     |
| build    | 构建系统或外部依赖变更       |
| ci       | CI/CD 配置变更               |
| chore    | 杂务                         |
| revert   | 回滚提交                     |

## 范围（scope）

用中文描述改动模块，常见范围：

- 教材内容（docs/ 章节修改）
- 后端API（backend/）
- 部署配置（Docker、Nginx）
- 构建脚本（scripts/、mkdocs.yml）
- CI/CD（.github/workflows/）
- 示例代码（code_examples/）

## 示例

```
feat(教材内容): 新增第15章运动规划算法节

补充了 A* 和 RRT 算法的原理说明、伪代码和对比表格。
```

```
fix(构建脚本): 修复图表自动编号跨章节重复问题

apply_numbering 中全局偏移量导致低行号操作时索引偏移，
改为降序处理消除依赖。
```

```
docs(教材内容): 修订第3章传感器分类表述
```

```
ci(CI/CD): 新增关闭Issue必填commit的workflow校验
```

## 规则

1. 简要描述不超过 50 个字符
2. 类型关键词使用英文小写（与 Conventional Commits 兼容）
3. 范围和描述使用中文
4. 如有详细说明，空一行后书写，每行不超过 72 个字符
5. 如果修改涉及多个范围，选最主要的一个
6. 必须添加 `BREAKING CHANGE:` 说明
7. 必须附加 `Close #Issue编号: 7位commit哈希`
