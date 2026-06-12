"""oaepp.states.error — 全局错误状态管理。

ErrorState 提供统一的 show/dismiss/retry 接口，
各功能 State 通过 get_state(ErrorState) 调用。

重试机制：
    - 用户点击 Toast 重试按钮 → ErrorState.retry_counter += 1
    - 调用方 State 监听 retry_counter 变化 → 重新执行操作
    - 调用方 State 执行完后通过 clear_retry() 重置计数器

示例（调用方 State）：
    class SubmitState(rx.State):
        _last_retry: int = 0

        async def check_retry(self):
            err = await self.get_state(ErrorState)
            if err.retry_counter > self._last_retry:
                self._last_retry = err.retry_counter
                await err.clear_retry()
                yield self.do_submit()
"""

from typing import Optional
import reflex as rx
from pydantic import BaseModel

from oaepp.constants import ErrorCode, ErrorSeverity


class ErrorItem(BaseModel):
    """单个错误条目（用于队列）。"""
    code: ErrorCode = ErrorCode.UNKNOWN
    message: str = ""
    severity: ErrorSeverity = ErrorSeverity.ERROR
    retry_label: str = ""
    retry_event: str = ""


class ErrorState(rx.State):
    """全局错误提示状态。

    用法：
        err = await self.get_state(ErrorState)
        err.show(ErrorCode.NETWORK_TIMEOUT, "网络超时", ErrorSeverity.ERROR,
                 retry="重试", retry_event="submit")
    """

    # 当前展示的错误（Reflex 序列化时 str-enum 自动转为字符串）
    current_code: str = ErrorCode.UNKNOWN
    current_message: str = ""
    current_severity: str = ErrorSeverity.INFO
    current_visible: bool = False
    retry_label: str = ""
    retry_event: str = ""
    retry_counter: int = 0              # 每次点击重试 +1，调用方监听此值
    auto_dismiss_sec: int = 0

    # 错误队列（不序列化，仅后端使用）
    _queue: list[ErrorItem] = []

    async def show(
        self,
        code: ErrorCode,
        message: str,
        severity: ErrorSeverity,
        retry: str = "",
        retry_event: str = "",
        auto_dismiss: int = 0,
    ):
        """入队一个错误并在空闲时展示。

        Args:
            code: ErrorCode 枚举值
            message: 用户可见文案
            severity: ErrorSeverity 枚举值
            retry: 重试按钮文字，空字符串 = 不显示
            retry_event: 调用方事件标识，retry() 后供调用方识别
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
        """触发重试。retry_counter += 1，关闭 Toast。

        调用方 State 应监听 retry_counter 变化来重新执行操作。
        执行完后调用 clear_retry() 重置。
        """
        self.retry_counter += 1
        await self.dismiss()

    async def clear_retry(self):
        """重置 retry_counter（调用方处理完重试后调用）。"""
        self.retry_counter = 0

    def _apply_item(self, item: ErrorItem):
        """将 ErrorItem 应用到当前展示字段。"""
        self.current_code = item.code
        self.current_message = item.message
        self.current_severity = item.severity
        self.current_visible = True
        self.retry_label = item.retry_label
        self.retry_event = item.retry_event
