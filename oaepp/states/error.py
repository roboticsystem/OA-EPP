"""F-S-051 异常提示/网络韧性状态 — ErrorState

提供错误捕获、重试计数、网络在线状态管理。

用法:
    from oaepp.states.error import ErrorState

    await ErrorState.set_error("网络请求失败")
    # UI 层通过 ErrorState.has_error / ErrorState.error_message 显示错误横幅
    await ErrorState.clear_error()
"""
try:
    import reflex as rx
except Exception:
    rx = None

ErrorState = None

if rx is not None:
    class ErrorState(rx.State):
        """全局错误和网络状态管理

        属性:
            error_message: 当前错误消息（空字符串表示无错误）
            has_error: 是否有未清除的错误
            retry_count: 累计重试次数（不清零，用于监控统计）
            network_online: 网络是否在线（乐观默认 True）
        """

        # ── 错误状态 ──
        error_message: str = ""
        has_error: bool = False
        retry_count: int = 0

        # ── 网络在线状态 ──
        network_online: bool = True

        async def set_error(self, message: str):
            """记录错误，递增重试计数。

            Args:
                message: 用户可读的错误描述
            """
            self.error_message = message
            self.has_error = True
            self.retry_count += 1

        async def clear_error(self):
            """清除当前错误状态。

            注意：retry_count 不会重置，保留用于监控统计。
            """
            self.has_error = False
            self.error_message = ""
