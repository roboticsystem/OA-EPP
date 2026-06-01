# TDD 测试说明

## 概述

本项目采用 **TDD（测试驱动开发）** 模式，针对 Reflex 重实现的 43 个功能需求点编写测试。

- **🔴 RED**：`oaepp` 包未实现，测试全部失败（预期）
- **🟢 GREEN**：对应 `oaepp/states/*.py` 实现后，测试通过

---

## 环境准备

```bash
pip install pytest pytest-asyncio sqlmodel
```

---

## 运行测试

### 单个功能

```bash
# 方式一：直接运行 .py 文件
python3 -m pytest tests/reflex/test_F_S_004_avatar.py -v --override-ini="asyncio_mode=auto"

# 方式二：运行对应 .sh 脚本
bash tests/reflex/F-S-004_avatar.sh
```

### 全量测试

```bash
bash tests/reflex/run_all.sh
```

### 按系列运行

```bash
# 学生功能 (F-S)
python3 -m pytest tests/reflex/ -k "F_S" -v --override-ini="asyncio_mode=auto"

# DevOps 功能 (F-D)
python3 -m pytest tests/reflex/ -k "F_D" -v --override-ini="asyncio_mode=auto"

# 教师功能 (F-T)
python3 -m pytest tests/reflex/ -k "F_T" -v --override-ini="asyncio_mode=auto"
```

---

## 测试文件结构

```
tests/reflex/
├── pytest.ini              # asyncio_mode=auto
├── conftest.py             # mem_db fixture（SQLite 内存库）
├── lib/common.sh           # 公共 Shell 函数
├── run_all.sh              # 全量运行器
├── test_F_S_001_login.py   # 测试文件（Python）
├── F-S-001_login.sh        # 运行器（Shell）
└── ...                     # 共 43 对，覆盖所有功能
```

---

## 功能 → 实现路径对照

| 测试文件 | 需实现的 State 文件 |
|----------|-------------------|
| `test_F_S_001_login.py` | `oaepp/states/auth.py` → `AuthState` |
| `test_F_S_004_avatar.py` | `oaepp/states/avatar.py` → `AvatarState` |
| `test_F_D_001_repo_init.py` | `oaepp/states/devops_repo.py` → `RepoInitState` |
| `test_F_T_001_github_map.py` | `oaepp/states/teacher_github_map.py` → `StudentGitHubState` |
| *(其余同理，一功能一文件)* | |

---

## 读懂测试输出

```
FAILED test_F_S_004_TC01... — Failed: TDD RED: No module named 'oaepp'
```
→ 正常，`oaepp/states/avatar.py` 尚未创建。

```
PASSED test_F_S_004_TC01_state_attrs_exist
```
→ `AvatarState` 已实现且包含必要属性。

---

## TDD 开发流程

```
1. 运行测试 → 🔴 RED（预期失败）
2. 创建 oaepp/states/<feature>.py，实现对应 State
3. 再次运行测试 → 🟢 GREEN
4. 重构优化（保持 GREEN）
```
