# F-S-051 异常提示 — 设计规格

> 状态：已确认 | 日期：2026-06-11 | 优先级：中

---

## 1. 目标

构建全局统一的错误提示基础设施（`ErrorState` + `Toast` 组件 + 统一异常映射），覆盖上传失败、网络中断、权限不足等所有异常场景，提供可理解的错误文案和重试入口。

---

## 2. 架构

### 2.1 文件结构

```
oaepp/oaepp/
├── constants.py                  # 【扩充】ErrorSeverity + ErrorCode 枚举
├── states/
│   ├── __init__.py               # GlobalState（移除死掉的 toast 字段）
│   ├── error_state.py            # 【新增】ErrorState — 全局错误管理
│   └── auth_state.py             # 【改造】双写 ErrorState.show()
├── components/
│   ├── toast_bar.py              # 【新增】Toast 条组件
│   └── layout.py                 # 【新增】共享页面壳，挂载 Toast
└── utils/
    ├── helpers.py                # 现有验证函数
    └── error_handler.py          # 【新增】handle_error() + 文案映射表
```

### 2.2 State 层次

```
rx.State
├── ErrorState              — 全局错误队列 + show/dismiss/retry
├── GlobalState             — 移除遗留 toast_message/toast_type
└── AuthState               — 通过 get_state(ErrorState).show() 逐步迁移
```

各 State 通过 Reflex 的 `self.get_state(ErrorState)` 访问全局错误系统，**不改变继承关系**。

### 2.3 Toast 挂载

`components/layout.py` → `page_layout()` 作为所有页面外层容器，Toast 从顶部 fixed 定位渲染。

---

## 3. ErrorState — 数据模型

### 3.1 错误码枚举 (`constants.py`)

```python
class ErrorSeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class ErrorCode(str, Enum):
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    EXAM_ALREADY_SUBMITTED = "EXAM_ALREADY_SUBMITTED"
    DEADLINE_PASSED = "DEADLINE_PASSED"
    AUTH_FAILED = "AUTH_FAILED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    UNKNOWN = "UNKNOWN"
```

### 3.2 ErrorState (`states/error_state.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_code` | `ErrorCode` | 当前错误码 |
| `current_message` | `str` | 展示给用户的文案 |
| `current_severity` | `ErrorSeverity` | 驱动颜色和图标 |
| `current_visible` | `bool` | 控制 Toast 显隐 |
| `retry_label` | `str` | 重试按钮文字，空=不显示 |
| `auto_dismiss_sec` | `int` | 自动消失倒计时，0=手动关闭 |
| `_queue` | `list[dict]` | 待展示错误队列（Reflex 不序列化） |

| 方法 | 说明 |
|------|------|
| `show(code, message, severity, retry="", retry_event="", auto_dismiss=0)` | 入队并展示，`retry_event` 为回调事件名 |
| `dismiss()` | 关闭当前，展示队列下一个 |
| `retry()` | 关闭 Toast → `yield` 调用方 State 的 `retry_event` |

---

## 4. handle_error() — 统一异常映射

### 4.1 位置

`utils/error_handler.py`

### 4.2 文案映射表

| ErrorCode | 默认文案 | 严重程度 | 重试 |
|-----------|---------|---------|------|
| FILE_TOO_LARGE | 文件过大，请选择小于 10MB 的文件 | ERROR | — |
| UNSUPPORTED_FORMAT | 不支持的文件格式，支持：pdf、docx、zip、py、c、cpp | ERROR | — |
| NETWORK_TIMEOUT | 网络超时，请检查网络连接 | ERROR | 重试 |
| NETWORK_ERROR | 网络异常，请稍后重试 | ERROR | 重试 |
| PERMISSION_DENIED | 权限不足，请联系教师开通 | WARNING | — |
| EXAM_ALREADY_SUBMITTED | 该考试已提交，每人仅可提交一次 | WARNING | — |
| DEADLINE_PASSED | 已过截止时间，无法提交 | WARNING | — |
| AUTH_FAILED | 学号或密码错误，请重试 | ERROR | — |
| ACCOUNT_LOCKED | 账号已锁定，请稍后重试 | WARNING | — |
| UNKNOWN | 操作失败，请重试 | ERROR | 重试 |

### 4.3 异常 → ErrorCode 映射规则（按优先级）

1. `HTTPError(status=413)` → `FILE_TOO_LARGE`
2. `HTTPError(status=415)` → `UNSUPPORTED_FORMAT`
3. `HTTPError(status=401/403)` → `PERMISSION_DENIED`
4. `HTTPError(status=409)` → `EXAM_ALREADY_SUBMITTED`（或按端点细分）
5. `TimeoutError` / `ConnectionError` → `NETWORK_TIMEOUT` / `NETWORK_ERROR`
6. `PermissionError` → `PERMISSION_DENIED`
7. 自定义 `OaeppError(RuntimeError)` — 扩展预留
8. 其他 → `UNKNOWN`

### 4.4 调用示例

```python
# auth_state.py — 无重试场景
err_state = await self.get_state(ErrorState)
try:
    ...
except Exception as e:
    code, msg, severity, retry = handle_error(e)
    err_state.show(code, msg, severity, retry)

# assignment_state.py — 带重试场景
err_state = await self.get_state(ErrorState)
try:
    await self.upload_file(file)
except Exception as e:
    code, msg, severity, retry_label = handle_error(e)
    err_state.show(code, msg, severity,
                   retry=retry_label,
                   retry_event="submit_assignment")  # retry() 时 yield 此事件
```

---

## 5. Toast 组件 — UI 渲染

### 5.1 颜色映射（原型约定）

| severity | 容器 | 文字 | 图标 |
|----------|------|------|------|
| error | `bg-red-50 border-red-200` | `text-red-700` | ✕ |
| warning | `bg-yellow-50 border-yellow-100` | `text-yellow-700` | ⚠ |
| success | `bg-green-50 border-green-200` | `text-green-700` | ✓ |
| info | `bg-blue-50 border-blue-100` | `text-blue-600` | ℹ |

### 5.2 行为

- 定位：`position: fixed, top: 16px, z-index: 50`，水平居中
- 有 `auto_dismiss_sec > 0` 时自动消失（`info`/`success` 默认 3s，`warning` 默认 5s，`error` 默认 8s）
- 有 `retry_label` 时显示次要样式按钮（`text-gray-600 border-gray-300`）
- 布局：图标 + 文字 + 关闭按钮 + (可选)重试按钮

### 5.3 挂载

```python
# components/layout.py
def page_layout(*children):
    return rx.box(
        toast_bar(),
        # ... navbar, sidebar, content ...
    )
```

---

## 6. 迁移路径

### 阶段 1 — 基础设施（与现有代码零冲突）

1. `constants.py` 扩充 `ErrorSeverity` + `ErrorCode`
2. 新建 `states/error_state.py`
3. 新建 `utils/error_handler.py`
4. 新建 `components/toast_bar.py` + `components/layout.py`

### 阶段 2 — 激活 Toast

1. `app.py` 中所有页面用 `page_layout()` 包裹
2. 此时无调用方，Toast 静默 — 零破坏

### 阶段 3 — 渐进迁移

| 模块 | 迁移方式 | 优先级 |
|------|---------|--------|
| `AuthState.handle_login()` | 双写：保留旧 error_message + 新增 ErrorState.show() | 低 |
| `DeadlineState.submit_assignment()` | 同上双写 | 低 |
| Login 页面渲染 | 保留旧 rx.cond，Toast 作为第二通道 | 低 |

新功能（上传、考试提交等）直接使用 ErrorState，存量模块不强行替换。

---

## 7. 不做什么（YAGNI 排除）

- ~~全局 403/404 错误页面~~ — 原型无此需求
- ~~离线检测/Service Worker~~ — 超出 F-S-051 范围
- ~~错误日志收集上报~~ — 超出 F-S-051 范围
- ~~Loading 骨架屏~~ — 属于独立功能，非本轮范围
- ~~ErrorState 继承 GlobalState~~ — 保持兄弟关系，避免耦合

---

## 8. 验收清单

- [ ] 上传文件过大时提示"文件过大，请选择小于 10MB 的文件"
- [ ] 上传格式不支持时提示支持格式列表
- [ ] 网络超时/中断时提示"网络异常，请稍后重试" + "重试"按钮
- [ ] 权限不足时提示"权限不足，请联系教师开通"（无重试按钮）
- [ ] 考试重复提交时提示"该考试已提交，每人仅可提交一次"
- [ ] 截止时间过后提示"已过截止时间，无法提交"
- [ ] 所有错误场景的 Toast 从页面顶部滑入
- [ ] success/info 类型 Toast 自动消失，error 类型可手动关闭
- [ ] 错误文案为中文，符合同学习惯
