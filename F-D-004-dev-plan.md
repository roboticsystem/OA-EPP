# F-D-004 CI自动化 开发计划

## 需求概述

每次 PR 自动触发 GitHub Actions 运行代码 lint（Ruff）和单元测试（pytest），CI 通过为合并前置条件，CI 失败时不可合并，确保代码质量门槛。

## 更新背景

本分支创建计划后，已将 `origin/main` 合入当前分支。最新 `main` 新增了 `tests/reflex/` TDD 验收体系，其中 F-D-004 已有专门验收测试：

- [tests/reflex/test_F_D_004_ci.py](tests/reflex/test_F_D_004_ci.py)
- [tests/reflex/F-D-004_ci.sh](tests/reflex/F-D-004_ci.sh)

该测试要求存在：

- `oaepp.states.devops_ci.CIState`
- `CIState.ci_enabled`
- `CIState.last_run_status`
- `CIState.workflow_url`
- `CIState.trigger_ci()`
- `CIState.CI_STEPS`、`lint_enabled`、`test_enabled` 或 `workflow_template` 中至少一种 CI 步骤配置表达

因此，本计划需要从“仅后端 CI 工作流”调整为：

1. 满足原始需求：GitHub Actions 在 PR 上运行 Ruff 和 pytest
2. 满足新增 TDD 验收：实现 F-D-004 对应的 `CIState`
3. 仍保持 CI 主要覆盖后端代码，但把 F-D-004 的验收测试纳入本次验证范围

## 验收标准

- PR 触发时自动运行 Ruff lint 和 pytest
- CI 失败时 PR 无法合并
- CI 结果在 PR 页面清晰展示
- lint 和测试分步骤展示完整日志
- `tests/reflex/test_F_D_004_ci.py` 通过
- `bash tests/reflex/F-D-004_ci.sh` 通过

## 当前项目状态

| 项目                | 状态                                                                                         |
| ------------------- | -------------------------------------------------------------------------------------------- |
| 后端框架            | FastAPI，位于 `backend/`                                                                   |
| Python 版本         | 3.12（Docker 基础镜像）                                                                      |
| 数据库              | SQLite（无 ORM，原生 sqlite3）                                                               |
| Ruff 配置           | 无                                                                                           |
| 后端测试代码        | 无                                                                                           |
| Reflex TDD 测试     | 已由最新 `main` 新增，位于 `tests/reflex/`                                               |
| F-D-004 验收测试    | 已存在，当前因 `oaepp.states.devops_ci` 不存在而处于 RED                                   |
| CI 构建流水线       | 无（仅有 PR-Agent 审查和 Issue 关闭校验两个工作流）                                          |
| 已有 GitHub Actions | `.github/workflows/pr-agent-review.yml`、`.github/workflows/require-commit-on-close.yml` |

## 覆盖范围

本次 CI 覆盖：

- `backend/` 后端 Python 代码
- `oaepp/states/devops_ci.py` 作为 F-D-004 的状态实现
- `tests/reflex/test_F_D_004_ci.py` 作为 F-D-004 的验收测试
- `.github/workflows/ci.yml` CI 工作流本身

暂不覆盖：

- 根目录 MkDocs 文档构建
- `scripts/` 下的工具脚本
- `prototype/` 静态原型页面
- Docker 镜像构建
- `tests/reflex/` 中其他尚未实现功能的 RED 测试

## 技术方案

### 1. 后端配置集中到 `backend/pyproject.toml`

新增 `backend/pyproject.toml`，承载：

- Ruff 配置
- pytest 配置
- Python 版本目标

建议配置：

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

本次使用 Ruff 默认 lint 规则，先建立稳定的 CI 质量门禁；不在该 issue 中强制 `ruff format --check`，避免把历史格式化债务混入 CI 自动化任务。

### 2. 创建 F-D-004 State 实现

新增最小 `oaepp` 包结构，使最新 TDD 验收测试进入 GREEN。

建议文件：

- `oaepp/__init__.py`
- `oaepp/states/__init__.py`
- `oaepp/states/devops_ci.py`

`CIState` 最小职责：

- 表达 CI 已启用状态
- 记录最近一次运行状态
- 暴露工作流入口 URL
- 暴露 lint 和 pytest 步骤配置
- 提供 `trigger_ci()` 事件处理器

建议实现形态：

```python
class CIState:
    ci_enabled = True
    last_run_status = "not_started"
    workflow_url = ".github/workflows/ci.yml"
    CI_STEPS = ("ruff", "pytest")
    lint_enabled = True
    test_enabled = True

    async def trigger_ci(self):
        self.last_run_status = "queued"
```

当前验收测试只要求属性和方法存在，不要求真实调用 GitHub API。不要在 `trigger_ci()` 中发起网络请求。

### 3. 创建基础 pytest 测试体系

新增 `backend/tests/`，使用 FastAPI `TestClient` 进行基础冒烟测试。

初始测试目标：

- FastAPI app 可以被导入并创建
- 关键页面路由存在：`/teacher`、`/score`
- Swagger 文档路由存在：`/api/docs`
- 主要 API 路由注册成功
- 教师登录、学生查询、认证失败等基础接口行为可测试

测试不连接生产数据库，不依赖外部服务。

### 4. 创建 GitHub Actions CI 工作流

新增 `.github/workflows/ci.yml`。

触发条件：

```yaml
on:
  pull_request:
    types: [opened, reopened, synchronize]
    paths:
      - "backend/**"
      - "oaepp/**"
      - "tests/reflex/test_F_D_004_ci.py"
      - "tests/reflex/F-D-004_ci.sh"
      - ".github/workflows/ci.yml"
```

Jobs：

1. `ruff-check`

   - checkout
   - setup Python 3.12
   - install Ruff
   - run `ruff check backend oaepp tests/reflex/test_F_D_004_ci.py --config backend/pyproject.toml`
2. `pytest`

   - checkout
   - setup Python 3.12
   - install backend requirements
   - install pytest/httpx/pytest-asyncio/sqlmodel
   - run backend tests
   - run `tests/reflex/test_F_D_004_ci.py`

两个 job 并行执行，任一失败则 CI 失败。

### 5. 分支保护规则

“CI 失败时 PR 无法合并”需要在 GitHub 仓库设置中完成，代码无法直接强制启用。

建议手动配置：

- Settings → Branches → Branch protection rules → `main`
- 勾选 `Require status checks to pass before merging`
- 选择：
  - `ruff-check`
  - `pytest`

## 文件清单

| 操作     | 文件路径                       | 说明                               |
| -------- | ------------------------------ | ---------------------------------- |
| 新建     | `backend/pyproject.toml`     | Ruff + pytest 配置                 |
| 新建     | `.github/workflows/ci.yml`   | GitHub Actions CI 工作流           |
| 新建     | `oaepp/__init__.py`          | Reflex/TDD 功能包入口              |
| 新建     | `oaepp/states/__init__.py`   | State 包入口                       |
| 新建     | `oaepp/states/devops_ci.py`  | F-D-004 CIState 实现               |
| 新建     | `backend/tests/__init__.py`  | 测试包标记                         |
| 新建     | `backend/tests/conftest.py`  | 测试 fixtures                      |
| 新建     | `backend/tests/test_main.py` | 应用启动和路由测试                 |
| 新建     | `backend/tests/test_api.py`  | API 冒烟测试                       |
| 可能修改 | `backend/app/**/*.py`        | 仅当 Ruff 发现现有 lint 问题时修复 |
| 修改     | `F-D-004-dev-plan.md`        | 记录更新后的计划和验收方式         |

## 10 次 Commit 拆分计划

> 每个 commit 都应保持可运行、可回滚、目标单一。下面 commit message 使用当前仓库已有中文 conventional commit 风格。

### Commit 1：新增后端 pytest 配置骨架

**目标：** 先建立后端测试配置入口，不引入测试逻辑。

**改动文件：**

- `backend/pyproject.toml`

**具体内容：**

- 新增 `[tool.pytest.ini_options]`
- 配置 `testpaths = ["tests"]`
- 配置 `pythonpath = ["."]`

**验证命令：**

```bash
python -m pytest --version
```

**建议 commit message：**

```text
test(后端): 新增 pytest 配置骨架
```

---

### Commit 2：新增后端 Ruff 配置

**目标：** 建立后端 lint 配置，但暂不修改业务代码。

**改动文件：**

- `backend/pyproject.toml`

**具体内容：**

- 新增 `[tool.ruff]`
- 设置 `target-version = "py312"`
- 设置 `line-length = 120`
- 使用 Ruff 默认 lint 规则

**验证命令：**

```bash
python -m ruff check backend --config backend/pyproject.toml
```

**建议 commit message：**

```text
chore(后端): 新增 Ruff 检查配置
```

---

### Commit 3：实现 F-D-004 CIState 验收状态

**目标：** 让最新 `tests/reflex/test_F_D_004_ci.py` 从 RED 进入 GREEN。

**改动文件：**

- `oaepp/__init__.py`
- `oaepp/states/__init__.py`
- `oaepp/states/devops_ci.py`

**具体内容：**

- 创建 `oaepp` 包
- 创建 `oaepp.states` 包
- 实现 `CIState`
- 声明 `ci_enabled`、`last_run_status`、`workflow_url`
- 声明 `CI_STEPS` 或 `lint_enabled` / `test_enabled`
- 实现 `trigger_ci()`，只更新本地状态，不访问外部网络

**验证命令：**

```bash
python -m pytest tests/reflex/test_F_D_004_ci.py -v --override-ini="asyncio_mode=auto"
bash tests/reflex/F-D-004_ci.sh
```

**建议 commit message：**

```text
feat(DevOps): 实现 CI 自动化状态模型
```

---

### Commit 4：创建后端测试目录和基础 fixtures

**目标：** 建立 pytest 测试目录结构和可复用 TestClient fixture。

**改动文件：**

- `backend/tests/__init__.py`
- `backend/tests/conftest.py`

**具体内容：**

- 创建 `tests` 包
- 在 `conftest.py` 中提供 `client` fixture
- 使用 FastAPI `TestClient(app)`
- 通过临时环境变量隔离测试数据库路径

**验证命令：**

```bash
cd backend && python -m pytest --collect-only
```

**建议 commit message：**

```text
test(后端): 新增测试目录和客户端fixture
```

---

### Commit 5：新增应用启动和文档路由测试

**目标：** 验证 FastAPI app 可导入，Swagger 文档路由可访问。

**改动文件：**

- `backend/tests/test_main.py`

**具体测试：**

- `test_app_can_be_imported`
- `test_docs_route_available`
- 可选：验证 `app.title` 等基本元信息

**验证命令：**

```bash
cd backend && python -m pytest tests/test_main.py -v
```

**建议 commit message：**

```text
test(后端): 覆盖应用启动和文档路由
```

---

### Commit 6：新增静态页面路由测试

**目标：** 验证 `/teacher` 和 `/score` 页面路由在后端中注册并可访问。

**改动文件：**

- `backend/tests/test_main.py`

**具体测试：**

- `test_teacher_page_available`
- `test_score_page_available`

**注意事项：**

- 测试只验证状态码和 HTML 响应，不校验完整页面内容
- 如果运行环境缺少静态文件，需要明确失败原因，而不是跳过核心路由

**验证命令：**

```bash
cd backend && python -m pytest tests/test_main.py -v
```

**建议 commit message：**

```text
test(后端): 覆盖教师和成绩页面路由
```

---

### Commit 7：新增学生查询和认证 API 冒烟测试

**目标：** 验证学生查询与学生认证接口的基础响应行为。

**改动文件：**

- `backend/tests/test_api.py`
- 如有必要，补充 `backend/tests/conftest.py`

**具体测试：**

- 未提供查询条件时返回合理响应
- 查询不存在学生时返回空结果或预期错误
- 不存在的学生或考试返回认证失败
- 存在学生和考试时返回 token 或预期认证结果

**测试数据：**

- 使用临时 SQLite 数据库
- 必要时在测试前插入少量学生和考试数据

**验证命令：**

```bash
cd backend && python -m pytest tests/test_api.py -v
```

**建议 commit message：**

```text
test(后端): 新增学生接口冒烟测试
```

---

### Commit 8：新增教师登录 API 冒烟测试

**目标：** 验证教师登录接口和环境变量密码逻辑。

**改动文件：**

- `backend/tests/test_api.py`
- 如有必要，补充 `backend/tests/conftest.py`

**具体测试：**

- 密码错误时登录失败
- 密码正确时返回教师 token
- token 响应结构符合预期

**测试环境：**

- 在测试 fixture 中设置 `TEACHER_PASSWORD`
- 避免依赖默认生产值

**验证命令：**

```bash
cd backend && python -m pytest tests/test_api.py -v
```

**建议 commit message：**

```text
test(后端): 新增教师登录接口冒烟测试
```

---

### Commit 9：新增 GitHub Actions CI 工作流

**目标：** 创建 PR 自动触发的 Ruff + pytest CI。

**改动文件：**

- `.github/workflows/ci.yml`

**具体内容：**

- `on.pull_request.types = [opened, reopened, synchronize]`
- 路径过滤：`backend/**`、`oaepp/**`、F-D-004 验收测试、CI 工作流自身
- `ruff-check` job：
  - Python 3.12
  - 安装 Ruff
  - 运行 Ruff lint
- `pytest` job：
  - Python 3.12
  - 安装 `backend/requirements.txt`
  - 安装 `pytest`、`httpx`、`pytest-asyncio`、`sqlmodel`
  - 执行后端测试
  - 执行 F-D-004 Reflex/TDD 验收测试

**验证命令：**

```bash
python -m ruff check backend oaepp tests/reflex/test_F_D_004_ci.py --config backend/pyproject.toml
cd backend && python -m pytest -v
cd .. && python -m pytest tests/reflex/test_F_D_004_ci.py -v --override-ini="asyncio_mode=auto"
```

**建议 commit message：**

```text
ci(DevOps): 新增 PR lint 和测试流水线
```

---

### Commit 10：修复 lint/test 问题并补充验收说明

**目标：** 让本地 lint、后端 pytest、F-D-004 验收测试全部通过，并在计划文档中补齐最终验收记录。

**改动文件：**

- `backend/app/**/*.py`（仅当 Ruff 发现问题时修改）
- `backend/tests/**/*.py`（仅当测试需要修正时修改）
- `oaepp/**/*.py`（仅当 Ruff 或 F-D-004 测试发现问题时修改）
- `F-D-004-dev-plan.md`

**具体内容：**

- 修复 Ruff 报告的 import 顺序、未使用变量、Python 3.12 可升级写法等问题
- 修正测试中发现的 fixture、数据库隔离或接口断言问题
- 记录本地验证结果
- 明确 GitHub 分支保护规则需人工配置

**最终验证命令：**

```bash
python -m ruff check backend oaepp tests/reflex/test_F_D_004_ci.py --config backend/pyproject.toml
cd backend && python -m pytest -v
cd .. && python -m pytest tests/reflex/test_F_D_004_ci.py -v --override-ini="asyncio_mode=auto"
bash tests/reflex/F-D-004_ci.sh
```

**建议 commit message：**

```text
fix(DevOps): 修复 CI 校验发现的问题
```

如无 lint/test 问题，该 commit 可改为：

```text
docs(CI): 补充自动化验收说明
```

## 本地验证清单

实施完成后至少运行：

```bash
python -m ruff check backend oaepp tests/reflex/test_F_D_004_ci.py --config backend/pyproject.toml
cd backend && python -m pytest -v
cd .. && python -m pytest tests/reflex/test_F_D_004_ci.py -v --override-ini="asyncio_mode=auto"
bash tests/reflex/F-D-004_ci.sh
```

如需模拟 CI 安装环境，可运行：

```bash
python -m pip install -r backend/requirements.txt
python -m pip install ruff pytest httpx pytest-asyncio sqlmodel
```

## 最终执行记录

- 已完成 10 次 commit 拆分中的前 9 次功能性提交。
- 第 10 次提交用于收敛 CI 配置和计划文档。
- Ruff 配置最终采用默认 lint 规则，仅建立基础质量门禁。
- CI 工作流保留 `ruff-check` 与 `pytest` 两个 status check。
- CI 中 pytest job 分别运行后端测试与 F-D-004 验收测试。
- 本地环境中 `python` 命令返回退出码 49，无法实际执行 Ruff/pytest；最终验证以 GitHub Actions 为准。
- `CI 失败时 PR 无法合并` 仍需仓库管理员在 GitHub 分支保护规则中勾选 `ruff-check` 和 `pytest`。

## PR 验收清单

创建 PR 后确认：

- PR 页面出现 `ruff-check` status check
- PR 页面出现 `pytest` status check
- Ruff job 日志中可见 lint 步骤完整输出
- pytest job 日志中可见后端测试和 F-D-004 验收测试
- 修改 `backend/`、`oaepp/`、`.github/workflows/ci.yml` 后 CI 自动重新运行
- CI 失败时 PR merge 按钮被分支保护规则阻止

## 手动配置项

以下事项不能仅靠代码完成，需要仓库管理员在 GitHub 设置中操作：

1. 打开仓库 Settings
2. 进入 Branches
3. 新建或编辑 `main` 分支保护规则
4. 开启 `Require status checks to pass before merging`
5. 勾选 `ruff-check` 和 `pytest`
6. 如需要，可开启 `Require branches to be up to date before merging`

## 风险与处理

| 风险                                       | 影响                      | 处理                                                       |
| ------------------------------------------ | ------------------------- | ---------------------------------------------------------- |
| 新增 `tests/reflex/` 让原计划过时        | F-D-004 验收测试不会通过  | 增加 `oaepp.states.devops_ci.CIState` 实现和对应验证     |
| 全量 `tests/reflex/` 仍有大量 RED 测试   | CI 若运行全量会失败       | 本次 CI 仅运行 F-D-004 对应测试，其他功能由对应 issue 实现 |
| 现有代码 Ruff 不通过                       | CI 初始化后立即失败       | 在 Commit 10 集中修复，避免与 CI 配置混杂                  |
| FastAPI 启动时自动同步 docs 导致测试不稳定 | pytest 失败或依赖文档目录 | 使用临时环境变量和 fixture 隔离测试环境                    |
| SQLite 默认路径指向 `/app/data/exam.db`  | 本地测试可能写入错误位置  | 测试中设置临时 `DB_PATH`                                 |
| 分支保护无法代码化                         | CI 失败仍可手动合并       | 在 PR 描述和计划文档中明确需管理员配置                     |
| CI 只覆盖 F-D-004 验收测试                 | 其他功能 RED 测试不被发现 | 符合当前 issue 范围；后续按功能逐步纳入                    |

## 不做事项

本次不做：

- 不引入 coverage 门槛
- 不引入 mypy 类型检查
- 不构建 Docker 镜像
- 不运行 MkDocs 文档构建
- 不运行全量 `tests/reflex/` RED 测试
- 不将 Ruff/pytest 加入生产 `backend/requirements.txt`
- 不对 `scripts/` 和根目录其他 Python 文件做 lint
