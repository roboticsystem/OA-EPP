"""oaepp.states.error — 全局错误状态管理。

ErrorState 提供统一的 show/dismiss/retry 接口，
各功能 State 通过 get_state(ErrorState) 调用。
"""

from typing import Optional
import reflex as rx
from pydantic import BaseModel

# 导入枚举的尝试路径（兼容两种项目结构）
try:
    from constants import ErrorCode, ErrorSeverity
except ImportError:
    try:
        from oaepp.constants import ErrorCode, ErrorSeverity
    except ImportError:
        ErrorCode = None
        ErrorSeverity = None


class ErrorItem(BaseModel):
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
    retry_event: str = ""               # retry() 时 yield 的事件名（预留）
    auto_dismiss_sec: int = 0

    # 错误队列（不序列化，仅后端使用）
    _queue: list[ErrorItem] = []

    async def show(
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

    async def dismiss(self):
        """关闭当前错误，展示队列中下一个。"""
        if self._queue:
            item = self._queue.pop(0)
            self._apply_item(item)
        else:
            self.current_visible = False
            self.current_message = ""
            self.retry_label = ""
            self.retry_event = ""

    async def retry(self):
        """触发重试。关闭 Toast。

        调用方 State 通过监听 current_visible == False && current_code
        来自行处理重试逻辑。retry_event 字段为预留扩展。
        """
        await self.dismiss()

    def _apply_item(self, item: ErrorItem):
        """将 ErrorItem 应用到当前展示字段。"""
        self.current_code = item.code
        self.current_message = item.message
        self.current_severity = item.severity
        self.current_visible = True
        self.retry_label = item.retry_label
        self.retry_event = item.retry_event
