# F-S-051 异常提示 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建全局统一的错误提示基础设施（ErrorState + Toast 组件 + 统一异常映射），覆盖上传失败、网络中断、权限不足等场景。

**架构：** 新增 `ErrorState(rx.State)` 管理错误队列与展示状态，通过 `handle_error()` 将异常映射为错误码+文案+重试建议，新增 `toast_bar` 组件从页面顶部渲染 5 色状态提示条，所有页面通过 `page_layout` 共享此基础设施。

**技术栈：** Reflex 0.9.4, pytest (asyncio_mode=auto), Python 3.11+

---

## 文件职责清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `tests/reflex/test_F_S_051_error.py` | 重写 | 测试 ErrorState API、handle_error 映射、Toast 渲染条件 |
| `oaepp/constants.py` | 修改 | 新增 ErrorSeverity（4 级）和 ErrorCode（10 个错误码）枚举 |
| `oaepp/states/__init__.py` | 修改 | 移除死掉的 toast_message/toast_type 字段，保留 GlobalState |
| `oaepp/states/error.py` | 新建 | ErrorState — show/dismiss/retry，错误队列管理 |
| `oaepp/utils/error_handler.py` | 新建 | handle_error() + 文案映射表 + 严重程度策略表 |
| `oaepp/components/__init__.py` | 新建 | 导出 toast_bar, layout |
| `oaepp/components/toast_bar.py` | 新建 | Toast 条渲染组件（5 色，顶部 fixed，自动消失） |
| `oaepp/components/layout.py` | 新建 | page_layout() 页面壳，挂载 Toast + 导航栏占位 |
| `oaepp/app.py` | 修改 | 页面用 page_layout() 包裹，注册 ErrorState |

---

### 任务 1：重写 TDD 测试（RED → 对齐设计）

**文件：**
- 重写：`tests/reflex/test_F_S_051_error.py`
- 新建：`tests/reflex/utils/test_error_handler.py`（如果需要独立测试 handle_error）

- [ ] **步骤 1：重写 ErrorState 测试以匹配新设计**

```python
"""F-S-051 异常提示 TDD 测试

被测模块 : oaepp.states.error.ErrorState
          oaepp.utils.error_handler.handle_error
TDD RED   : 模块不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.error import ErrorState
    _ERR_STATE_IMPORT_ERROR = None
except ImportError as _e:
    ErrorState = None
    _ERR_STATE_IMPORT_ERROR = str(_e)

try:
    from oaepp.utils.error_handler import handle_error, ErrorCode, ErrorSeverity, ERROR_MESSAGES, ERROR_POLICY
    _HANDLER_IMPORT_ERROR = None
except ImportError as _e:
    handle_error = None
    ErrorCode = None
    ErrorSeverity = None
    ERROR_MESSAGES = None
    ERROR_POLICY = None
    _HANDLER_IMPORT_ERROR = str(_e)


def _guard_err():
    if _ERR_STATE_IMPORT_ERROR:
        pytest.fail(f"TDD RED (ErrorState): {_ERR_STATE_IMPORT_ERROR}")

def _guard_handler():
    if _HANDLER_IMPORT_ERROR:
        pytest.fail(f"TDD RED (error_handler): {_HANDLER_IMPORT_ERROR}")


# ══════════════════════════════════════════════════════════
#  ErrorState 测试
# ══════════════════════════════════════════════════════════

def test_TC01_state_attrs_exist():
    """ErrorState 必须声明 current_code, current_message, current_severity, current_visible, retry_label"""
    _guard_err()
    for attr in ("current_code", "current_message", "current_severity",
                 "current_visible", "retry_label", "auto_dismiss_sec"):
        assert hasattr(ErrorState, attr), f"缺少 {attr} 状态变量"


async def test_TC02_show_sets_state(mem_db):
    """show() 设置错误信息并显示 Toast"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.UNKNOWN, "测试错误", ErrorSeverity.ERROR)
    assert state.current_visible is True
    assert state.current_message == "测试错误"
    assert state.current_code == ErrorCode.UNKNOWN


async def test_TC03_dismiss_hides_toast(mem_db):
    """dismiss() 隐藏 Toast 并展示队列中下一个错误"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.UNKNOWN, "第一个错误", ErrorSeverity.ERROR)
    await state.show(ErrorCode.NETWORK_TIMEOUT, "第二个错误", ErrorSeverity.ERROR)
    await state.dismiss()
    assert state.current_visible is True
    assert state.current_message == "第二个错误"
    await state.dismiss()
    assert state.current_visible is False


async def test_TC04_show_stores_retry_info(mem_db):
    """show() 存储重试标签和回调事件名"""
    _guard_err()
    state = ErrorState()
    await state.show(ErrorCode.NETWORK_ERROR, "网络异常", ErrorSeverity.ERROR,
                     retry="重试", retry_event="submit_assignment")
    assert state.retry_label == "重试"


async def test_TC05_clear_error_resets_state(mem_db):
    """手动重置所有状态变量"""
    _guard_err()
    state = ErrorState()
    state.current_message = "some error"
    state.current_visible = True
    state.retry_label = "重试"
    await state.dismiss()
    await state.dismiss()  # 清空队列
    assert state.current_visible is False
    assert state.current_message == ""


# ══════════════════════════════════════════════════════════
#  handle_error() 测试
# ══════════════════════════════════════════════════════════

def test_TC06_error_messages_complete():
    """ERROR_MESSAGES 覆盖所有 ErrorCode"""
    _guard_handler()
    for code in ErrorCode:
        assert code in ERROR_MESSAGES, f"缺少 {code} 的文案映射"


def test_TC07_error_policy_complete():
    """ERROR_POLICY 覆盖所有 ErrorCode"""
    _guard_handler()
    for code in ErrorCode:
        assert code in ERROR_POLICY, f"缺少 {code} 的策略映射"


def test_TC08_handle_unknown_error():
    """未知异常映射为 UNKNOWN"""
    _guard_handler()
    code, msg, severity, retry = handle_error(Exception("未知错误"))
    assert code == ErrorCode.UNKNOWN
    assert msg == ERROR_MESSAGES[ErrorCode.UNKNOWN]
    assert severity == ErrorSeverity.ERROR


def test_TC09_handle_timeout_error():
    """TimeoutError 映射为 NETWORK_TIMEOUT"""
    _guard_handler()
    code, msg, severity, retry = handle_error(TimeoutError("连接超时"))
    assert code == ErrorCode.NETWORK_TIMEOUT


def test_TC10_handle_connection_error():
    """ConnectionError 映射为 NETWORK_ERROR"""
    _guard_handler()
    code, msg, severity, retry = handle_error(ConnectionError("连接被拒绝"))
    assert code == ErrorCode.NETWORK_ERROR


def test_TC11_handle_permission_error():
    """PermissionError 映射为 PERMISSION_DENIED"""
    _guard_handler()
    code, msg, severity, retry = handle_error(PermissionError("权限不足"))
    assert code == ErrorCode.PERMISSION_DENIED


def test_TC12_retry_label_for_retryable_errors():
    """网络类错误应返回重试标签"""
    _guard_handler()
    _, _, _, retry = handle_error(TimeoutError())
    assert retry != "", "可重试错误应有 retry_label"


def test_TC13_no_retry_for_permission_errors():
    """权限错误不应返回重试标签"""
    _guard_handler()
    _, _, _, retry = handle_error(PermissionError())
    assert retry == "", "权限错误不应可重试"
```

- [ ] **步骤 2：运行测试验证 RED 状态**

```bash
python -m pytest tests/reflex/test_F_S_051_error.py -v --rootdir=tests/reflex
```

预期：ALL FAIL — `ModuleNotFoundError: No module named 'oaepp.states.error'`

- [ ] **步骤 3：Commit**

```bash
git add tests/reflex/test_F_S_051_error.py
git commit -m "test(异常提示): 重写 F-S-051 TDD 测试匹配 ErrorState 新设计"
```

---

### 任务 2：扩充 constants.py — ErrorSeverity + ErrorCode

**文件：**
- 修改：`oaepp/constants.py`

- [ ] **步骤 1：添加枚举定义**

在 `oaepp/constants.py` 末尾追加：

```python
from enum import Enum

class ErrorSeverity(str, Enum):
    """错误严重程度，驱动 Toast 颜色和自动消失策略。"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class ErrorCode(str, Enum):
    """全局错误码，handle_error() 按异常类型映射。"""
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

- [ ] **步骤 2：验证枚举可用**

```bash
python -c "from oaepp.constants import ErrorSeverity, ErrorCode; print(list(ErrorCode)); print('OK')"
```

预期输出：枚举列表 + `OK`

- [ ] **步骤 3：Commit**

```bash
git add oaepp/constants.py
git commit -m "feat(异常提示): 新增 ErrorSeverity 和 ErrorCode 枚举"
```

---

### 任务 3：创建 ErrorState (`states/error.py`)

**文件：**
- 新建：`oaepp/states/error.py`

- [ ] **步骤 1：编写最小实现**

```python
"""oaepp.states.error — 全局错误状态管理。

ErrorState 提供统一的 show/dismiss/retry 接口，
各功能 State 通过 get_state(ErrorState) 调用。
"""

from typing import Optional
import reflex as rx

# 导入枚举的尝试路径（兼容两种项目结构）
try:
    from constants import ErrorCode, ErrorSeverity
except ImportError:
    try:
        from oaepp.constants import ErrorCode, ErrorSeverity
    except ImportError:
        ErrorCode = None
        ErrorSeverity = None


class ErrorItem(rx.Base):
    """单个错误条目（用于队列）。"""
    code: str = "UNKNOWN"
    message: str = ""
    severity: str = "error"
    retry_label: str = ""
    retry_event: str = ""


class ErrorState(rx.State):
    """全局错误提示状态。

    用法：
        err = await self.get_state(ErrorState)
        err.show(ErrorCode.NETWORK_TIMEOUT, "网络超时", ErrorSeverity.ERROR, retry="重试")
    """

    # 当前展示的错误
    current_code: str = "UNKNOWN"
    current_message: str = ""
    current_severity: str = "info"     # info | success | warning | error
    current_visible: bool = False
    retry_label: str = ""
    retry_event: str = ""               # retry() 时 yield 的事件名
    auto_dismiss_sec: int = 0

    # 错误队列（不序列化，仅后端使用）
    _queue: list[ErrorItem] = []

    def show(
        self,
        code: str,
        message: str,
        severity: str,
        retry: str = "",
        retry_event: str = "",
        auto_dismiss: int = 0,
    ):
        """入队一个错误并在空闲时展示。

        Args:
            code: ErrorCode 值或任意错误码字符串
            message: 用户可见文案
            severity: ErrorSeverity 值
            retry: 重试按钮文字，空字符串 = 不显示
            retry_event: 回调事件名，retry() 时通过 yield 触发
            auto_dismiss: 自动消失秒数，0 = 手动关闭
        """
        item = ErrorItem(
            code=code,
            message=message,
            severity=severity,
            retry_label=retry,
            retry_event=retry_event,
        )
        if not self.current_visible:
            self._apply_item(item)
        else:
            self._queue.append(item)

    def dismiss(self):
        """关闭当前错误，展示队列中下一个。"""
        if self._queue:
            item = self._queue.pop(0)
            self._apply_item(item)
        else:
            self.current_visible = False
            self.current_message = ""
            self.retry_label = ""
            self.retry_event = ""

    def retry(self):
        """触发重试。关闭 Toast。

        调用方 State 通过监听 current_visible == False && current_code
        来自行处理重试逻辑。retry_event 字段为预留扩展。
        """
        self.dismiss()

    def _apply_item(self, item: ErrorItem):
        """将 ErrorItem 应用到当前展示字段。"""
        self.current_code = item.code
        self.current_message = item.message
        self.current_severity = item.severity
        self.current_visible = True
        self.retry_label = item.retry_label
        self.retry_event = item.retry_event
```

- [ ] **步骤 2：运行 ErrorState 测试**

```bash
python -m pytest tests/reflex/test_F_S_051_error.py::test_TC01_state_attrs_exist tests/reflex/test_F_S_051_error.py::test_TC02_show_sets_state tests/reflex/test_F_S_051_error.py::test_TC03_dismiss_hides_toast tests/reflex/test_F_S_051_error.py::test_TC04_show_stores_retry_info tests/reflex/test_F_S_051_error.py::test_TC05_clear_error_resets_state -v --rootdir=tests/reflex
```

预期：TC01-TC05 ALL PASS

- [ ] **步骤 3：Commit**

```bash
git add oaepp/states/error.py
git commit -m "feat(异常提示): 新增 ErrorState 全局错误状态管理"
```

---

### 任务 4：创建 handle_error() (`utils/error_handler.py`)

**文件：**
- 新建：`oaepp/utils/error_handler.py`

- [ ] **步骤 1：编写完整实现**

```python
"""oaepp.utils.error_handler — 统一异常→错误码映射。

提供 handle_error() 将异常转换为 ErrorCode + 文案 + 严重程度 + 重试建议。
各 State 在 try/except 中调用。
"""

import builtins
from typing import Tuple

# 兼容路径导入
try:
    from constants import ErrorCode, ErrorSeverity
except ImportError:
    try:
        from oaepp.constants import ErrorCode, ErrorSeverity
    except ImportError:
        ErrorCode = None
        ErrorSeverity = None


# ══════════════════════════════════════════════════════════
#  文案映射表
# ══════════════════════════════════════════════════════════

ERROR_MESSAGES: dict = {
    ErrorCode.FILE_TOO_LARGE:         "文件过大，请选择小于 10MB 的文件",
    ErrorCode.UNSUPPORTED_FORMAT:     "不支持的文件格式，支持：pdf、docx、zip、py、c、cpp",
    ErrorCode.NETWORK_TIMEOUT:        "网络超时，请检查网络连接",
    ErrorCode.NETWORK_ERROR:          "网络异常，请稍后重试",
    ErrorCode.PERMISSION_DENIED:      "权限不足，请联系教师开通",
    ErrorCode.EXAM_ALREADY_SUBMITTED: "该考试已提交，每人仅可提交一次",
    ErrorCode.DEADLINE_PASSED:        "已过截止时间，无法提交",
    ErrorCode.AUTH_FAILED:            "学号或密码错误，请重试",
    ErrorCode.ACCOUNT_LOCKED:         "账号已锁定，请稍后重试",
    ErrorCode.UNKNOWN:                "操作失败，请重试",
}


# ══════════════════════════════════════════════════════════
#  策略映射表 — 每个错误码的默认严重程度和重试策略
# ══════════════════════════════════════════════════════════

ERROR_POLICY: dict = {
    ErrorCode.FILE_TOO_LARGE:         {"severity": ErrorSeverity.ERROR,   "retry": ""},
    ErrorCode.UNSUPPORTED_FORMAT:     {"severity": ErrorSeverity.ERROR,   "retry": ""},
    ErrorCode.NETWORK_TIMEOUT:        {"severity": ErrorSeverity.ERROR,   "retry": "重试"},
    ErrorCode.NETWORK_ERROR:          {"severity": ErrorSeverity.ERROR,   "retry": "重试"},
    ErrorCode.PERMISSION_DENIED:      {"severity": ErrorSeverity.WARNING, "retry": ""},
    ErrorCode.EXAM_ALREADY_SUBMITTED: {"severity": ErrorSeverity.WARNING, "retry": ""},
    ErrorCode.DEADLINE_PASSED:        {"severity": ErrorSeverity.WARNING, "retry": ""},
    ErrorCode.AUTH_FAILED:            {"severity": ErrorSeverity.ERROR,   "retry": ""},
    ErrorCode.ACCOUNT_LOCKED:         {"severity": ErrorSeverity.WARNING, "retry": ""},
    ErrorCode.UNKNOWN:                {"severity": ErrorSeverity.ERROR,   "retry": "重试"},
}


# ══════════════════════════════════════════════════════════
#  异常 → ErrorCode 映射规则
# ══════════════════════════════════════════════════════════

def _map_exception_to_code(exc: Exception) -> str:
    """按优先级将异常映射为 ErrorCode。"""
    ex_type = type(exc)
    ex_msg = str(exc).lower()

    # 1. 自定义 HTTPError（如果项目后续引入 requests/aiohttp）
    if hasattr(exc, "status_code") or hasattr(exc, "status"):
        status = getattr(exc, "status_code", None) or getattr(exc, "status", 0)
        mapping = {
            413: ErrorCode.FILE_TOO_LARGE,
            415: ErrorCode.UNSUPPORTED_FORMAT,
            401: ErrorCode.PERMISSION_DENIED,
            403: ErrorCode.PERMISSION_DENIED,
            409: ErrorCode.EXAM_ALREADY_SUBMITTED,
        }
        if status in mapping:
            return mapping[status]

    # 2. 网络类异常
    if issubclass(ex_type, TimeoutError):
        return ErrorCode.NETWORK_TIMEOUT
    if issubclass(ex_type, (ConnectionError, ConnectionRefusedError, ConnectionAbortedError,
                              ConnectionResetError, OSError)):
        return ErrorCode.NETWORK_ERROR

    # 3. 权限异常
    if issubclass(ex_type, PermissionError):
        return ErrorCode.PERMISSION_DENIED

    # 4. 业务异常关键字匹配
    if "too large" in ex_msg or "file size" in ex_msg:
        return ErrorCode.FILE_TOO_LARGE
    if "format" in ex_msg or "unsupported" in ex_msg:
        return ErrorCode.UNSUPPORTED_FORMAT
    if "deadline" in ex_msg or "due date" in ex_msg:
        return ErrorCode.DEADLINE_PASSED
    if "already submitted" in ex_msg or "duplicate" in ex_msg:
        return ErrorCode.EXAM_ALREADY_SUBMITTED

    # 5. 兜底
    return ErrorCode.UNKNOWN


def handle_error(exc: Exception) -> Tuple[str, str, str, str]:
    """将任意异常映射为 (code, message, severity, retry_label)。

    用法：
        code, msg, severity, retry = handle_error(e)
        err_state.show(code, msg, severity, retry=retry)

    Returns:
        tuple of (ErrorCode value, 中文文案, severity value, retry_label)
    """
    code = _map_exception_to_code(exc)
    msg = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.UNKNOWN])
    policy = ERROR_POLICY.get(code, ERROR_POLICY[ErrorCode.UNKNOWN])
    severity = policy["severity"]
    retry = policy["retry"]
    return code, msg, severity, retry
```

- [ ] **步骤 2：运行 error_handler 测试**

```bash
python -m pytest tests/reflex/test_F_S_051_error.py::test_TC06_error_messages_complete tests/reflex/test_F_S_051_error.py::test_TC07_error_policy_complete tests/reflex/test_F_S_051_error.py::test_TC08_handle_unknown_error tests/reflex/test_F_S_051_error.py::test_TC09_handle_timeout_error tests/reflex/test_F_S_051_error.py::test_TC10_handle_connection_error tests/reflex/test_F_S_051_error.py::test_TC11_handle_permission_error tests/reflex/test_F_S_051_error.py::test_TC12_retry_label_for_retryable_errors tests/reflex/test_F_S_051_error.py::test_TC13_no_retry_for_permission_errors -v --rootdir=tests/reflex
```

预期：TC06-TC13 ALL PASS

- [ ] **步骤 3：Commit**

```bash
git add oaepp/utils/error_handler.py
git commit -m "feat(异常提示): 新增 handle_error() 统一异常映射"
```

---

### 任务 5：创建 Toast 组件 (`components/toast_bar.py`)

**文件：**
- 新建：`oaepp/components/__init__.py`
- 新建：`oaepp/components/toast_bar.py`

- [ ] **步骤 1：创建 `components/__init__.py`**

```python
"""oaepp.components — 可复用 UI 组件。"""
from oaepp.components.toast_bar import toast_bar
from oaepp.components.layout import page_layout

__all__ = ["toast_bar", "page_layout"]
```

- [ ] **步骤 2：编写 Toast 组件**

Reflex 中 `rx.box()` 的 `background`/`color` 支持 `rx.cond()` 动态切换。使用三元嵌套实现 4 色切换：

```python
"""oaepp.components.toast_bar — 全局错误提示条。

从页面顶部 fixed 定位，5 色状态变体，支持自动消失和重试按钮。
"""

import reflex as rx

try:
    from oaepp.states.error import ErrorState
except ImportError:
    ErrorState = rx.State


def toast_bar() -> rx.Component:
    """全局 Toast 条。绑定 ErrorState.current_visible。"""

    # 按 severity 动态选择背景色 / 文字色
    bg_color = rx.cond(
        ErrorState.current_severity == "error", "#fef2f2",
        rx.cond(
            ErrorState.current_severity == "warning", "#fefce8",
            rx.cond(
                ErrorState.current_severity == "success", "#f0fdf4",
                "#eff6ff",  # info / default
            ),
        ),
    )
    text_color = rx.cond(
        ErrorState.current_severity == "error", "#b91c1c",
        rx.cond(
            ErrorState.current_severity == "warning", "#a16207",
            rx.cond(
                ErrorState.current_severity == "success", "#15803d",
                "#1d4ed8",
            ),
        ),
    )

    return rx.cond(
        ErrorState.current_visible,
        rx.box(
            rx.hstack(
                rx.text(ErrorState.current_message, font_size="14px", flex="1"),
                rx.cond(
                    ErrorState.retry_label != "",
                    rx.button(
                        ErrorState.retry_label,
                        on_click=ErrorState.retry,
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                    ),
                ),
                rx.button(
                    "✕",
                    on_click=ErrorState.dismiss,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                width="100%",
                align="center",
                gap="8px",
            ),
            position="fixed",
            top="16px",
            left="50%",
            transform="translateX(-50%)",
            z_index="50",
            max_width="480px",
            width="calc(100% - 32px)",
            padding="12px 16px",
            background=bg_color,
            color=text_color,
            border_radius="8px",
            box_shadow="0 4px 12px rgba(0, 0, 0, 0.1)",
        ),
    )
```

```python
"""oaepp.components.toast_bar — 全局错误提示条。"""

import reflex as rx

try:
    from oaepp.states.error import ErrorState
except ImportError:
    ErrorState = rx.State


def toast_bar() -> rx.Component:
    """全局 Toast 条。

    绑定 ErrorState.current_visible。
    从页面顶部 fixed 定位，居中显示。
    """

    # 按 severity 选择颜色
    def _color_for(severity_var):
        return rx.cond(
            severity_var == "error",
            "#fef2f2",
            rx.cond(
                severity_var == "warning",
                "#fefce8",
                rx.cond(
                    severity_var == "success",
                    "#f0fdf4",
                    "#eff6ff",  # info / default
                ),
            ),
        )

    def _text_color_for(severity_var):
        return rx.cond(
            severity_var == "error",
            "#b91c1c",
            rx.cond(
                severity_var == "warning",
                "#a16207",
                rx.cond(
                    severity_var == "success",
                    "#15803d",
                    "#1d4ed8",
                ),
            ),
        )

    return rx.cond(
        ErrorState.current_visible,
        rx.box(
            rx.hstack(
                rx.text(ErrorState.current_message, font_size="14px", flex="1"),
                rx.cond(
                    ErrorState.retry_label != "",
                    rx.button(
                        ErrorState.retry_label,
                        on_click=ErrorState.retry,
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                    ),
                ),
                rx.button(
                    "✕",
                    on_click=ErrorState.dismiss,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                width="100%",
                align="center",
                gap="8px",
            ),
            position="fixed",
            top="16px",
            left="50%",
            transform="translateX(-50%)",
            z_index="50",
            max_width="480px",
            width="calc(100% - 32px)",
            padding="12px 16px",
            background=_color_for(ErrorState.current_severity),
            color=_text_color_for(ErrorState.current_severity),
            border_radius="8px",
            box_shadow="0 4px 12px rgba(0, 0, 0, 0.1)",
        ),
    )
```

- [ ] **步骤 3：验证组件可导入**

```bash
python -c "from oaepp.components.toast_bar import toast_bar; print('OK')"
```

预期：`OK`（若 ErrorState 未实现则 fallback 到 rx.State）

- [ ] **步骤 4：Commit**

```bash
git add oaepp/components/__init__.py oaepp/components/toast_bar.py
git commit -m "feat(异常提示): 新增 Toast 条组件（5 色状态、重试按钮）"
```

---

### 任务 6：创建页面布局 (`components/layout.py`)

**文件：**
- 新建：`oaepp/components/layout.py`

- [ ] **步骤 1：编写 page_layout**

```python
"""oaepp.components.layout — 共享页面壳。

所有页面通过 page_layout() 包裹，自动获得：
- 顶部 Toast 错误提示条
- 未来可扩展：导航栏、侧边栏插槽
"""

import reflex as rx
from oaepp.components.toast_bar import toast_bar


def page_layout(*children, **kwargs) -> rx.Component:
    """页面通用布局。

    自动挂载全局 Toast 条，子元素填充内容区。
    未来可在此添加 navbar/sidebar 插槽。

    用法:
        @rx.page("/", title="首页")
        def index():
            return page_layout(
                rx.heading("欢迎"),
                ...
            )
    """
    return rx.box(
        # 全局 Toast（最顶层）
        toast_bar(),
        # 页面内容
        rx.box(
            *children,
            width="100%",
        ),
        width="100%",
        position="relative",
    )
```

- [ ] **步骤 2：验证导入**

```bash
python -c "from oaepp.components.layout import page_layout; print('OK')"
```

预期：`OK`

- [ ] **步骤 3：Commit**

```bash
git add oaepp/components/layout.py
git commit -m "feat(异常提示): 新增 page_layout 共享页面壳（挂载 Toast）"
```

---

### 任务 7：集成 — 更新 app.py 和 states/__init__.py

**文件：**
- 修改：`oaepp/states/__init__.py`
- 修改：`oaepp/app.py`

- [ ] **步骤 1：清理 GlobalState 死代码**

在 `oaepp/states/__init__.py` 中移除 `toast_message` 和 `toast_type` 相关代码。修改前先读取确认当前内容，然后：

```python
# oaepp/states/__init__.py — 修改后
"""OA-EPP 全局状态层。"""

import reflex as rx


class GlobalState(rx.State):
    """跨功能共享的全局状态基类。

    所有学生功能 State 应继承 GlobalState。
    """

    # 当前用户信息
    current_user: dict = {}

    # 全局加载态
    is_loading: bool = False

    # 通知未读数
    unread_notifications: int = 0

    # ── 用户操作 ────────────────────────────────────────

    def set_user(self, user: dict):
        """设置当前登录用户。"""
        self.current_user = user

    def clear_user(self):
        """清除当前用户信息。"""
        self.current_user = {}

    # ── 通知操作 ────────────────────────────────────────

    def show_toast(self, message: str, type_: str = "info"):
        """显示全局 Toast 提示。
        
        已迁移至 ErrorState.show()。
        此方法保留兼容，内部委托给 ErrorState。
        """
        pass
```

**精确操作**：删除 `toast_message: str = ""`、`toast_type: str = "info"`、`clear_toast()` 方法。保留其他字段和方法不变。

- [ ] **步骤 2：更新 app.py — 页面用 page_layout 包裹**

修改 `oaepp/app.py`，在每个页面函数中包裹 `page_layout()`。读取当前 app.py 确认所有页面注册点，对每个页面函数添加包裹：

```python
# oaepp/app.py — 修改示意（在现有代码基础上增量修改）

from oaepp.components.layout import page_layout

# 原有 login_page 或其他页面函数中，将 return 内容包裹：
def login_page():
    return page_layout(
        # ... 原有 login 页面内容 ...
    )

def profile_page():
    return page_layout(
        # ... 原有 profile 页面内容 ...
    )
```

- [ ] **步骤 3：验证 app.py 能启动**

```bash
cd oaepp && python -c "from app import app; print('App loaded OK')"
```

预期：`App loaded OK`

- [ ] **步骤 4：运行全量 F-S-051 测试**

```bash
python -m pytest tests/reflex/test_F_S_051_error.py -v --rootdir=tests/reflex
```

预期：ALL 13 TESTS PASS

- [ ] **步骤 5：Commit**

```bash
git add oaepp/states/__init__.py oaepp/app.py
git commit -m "feat(异常提示): 集成 ErrorState + Toast 到 app.py，清理 GlobalState 死代码"
```

---

### 任务 8：全量测试验证

- [ ] **步骤 1：运行 F-S-051 专项测试**

```bash
bash tests/reflex/F-S-051_error.sh
```

预期：🟢 GREEN

- [ ] **步骤 2：运行全量回归测试**

```bash
bash tests/reflex/run_all.sh
```

预期：F-S-051 GREEN，其他现有测试无新增失败。

- [ ] **步骤 3：LSP 诊断检查**

对新增/修改的文件运行 LSP diagnostics，确保无类型错误。

- [ ] **步骤 4：Final commit**

```bash
git add -A
git commit -m "test(异常提示): F-S-051 全量测试通过"
```
