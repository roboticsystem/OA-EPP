"""
F-S-051 调试页面 — 手动触发所有 Toast 变体用于人工测试。
访问路由：/debug_toast（测试完后可删除此文件）
"""
try:
    import reflex as rx
except Exception:
    rx = None

debug_toast_page = None

if rx is not None:
    from oaepp.components.layout import page_layout
    from oaepp.states.error import ErrorState
    from oaepp.constants import ErrorCode, ErrorSeverity

    class DebugToastState(rx.State):
        """调试状态：提供按钮事件来触发各种 Toast。"""
        _queue_count: int = 0

        def _show(self, code, msg, severity, retry="", retry_event=""):
            """辅助方法：通过 get_state 调用 ErrorState.show()。"""
            return ErrorState.show(
                code, msg, severity, retry=retry, retry_event=retry_event
            )

        # ── 按严重程度 ──
        async def trigger_info(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.UNKNOWN, "这是一条信息提示", ErrorSeverity.INFO)

        async def trigger_success(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.UNKNOWN, "操作成功！", ErrorSeverity.SUCCESS)

        async def trigger_warning(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.DEADLINE_PASSED, "提交截止时间已过", ErrorSeverity.WARNING)

        async def trigger_error(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.NETWORK_ERROR, "网络连接异常，请稍后重试",
                     ErrorSeverity.ERROR, retry="重试", retry_event="debug_retry")

        # ── 按错误码 ──
        async def trigger_file_too_large(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.FILE_TOO_LARGE, "文件大小超出限制（最大 10MB）",
                     ErrorSeverity.WARNING)

        async def trigger_unsupported_format(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.UNSUPPORTED_FORMAT,
                     "不支持的文件格式，支持：pdf、docx、zip、py、c、cpp",
                     ErrorSeverity.WARNING)

        async def trigger_network_timeout(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.NETWORK_TIMEOUT, "网络请求超时，请检查网络连接",
                     ErrorSeverity.ERROR, retry="重试", retry_event="debug_retry")

        async def trigger_permission_denied(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.PERMISSION_DENIED, "权限不足，请联系教师开通",
                     ErrorSeverity.ERROR)

        async def trigger_auth_failed(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.AUTH_FAILED, "身份验证失败，请重新登录",
                     ErrorSeverity.ERROR)

        async def trigger_account_locked(self):
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.ACCOUNT_LOCKED, "账户已被锁定，请 300 秒后重试",
                     ErrorSeverity.ERROR)

        # ── 队列测试 ──
        async def trigger_queue_three(self):
            """连续触发 3 个错误，验证队列机制。"""
            err = await self.get_state(ErrorState)
            err.show(ErrorCode.NETWORK_ERROR, "第 1 个错误：网络异常", ErrorSeverity.ERROR,
                     retry="重试", retry_event="debug_retry")
            err.show(ErrorCode.FILE_TOO_LARGE, "第 2 个错误：文件过大", ErrorSeverity.WARNING)
            err.show(ErrorCode.PERMISSION_DENIED, "第 3 个错误：权限不足", ErrorSeverity.ERROR)

        async def dismiss_current(self):
            err = await self.get_state(ErrorState)
            err.dismiss()

    def _button(label, on_click, color="gray"):
        return rx.button(label, on_click=on_click, size="2", color_scheme=color,
                         width="100%")

    def debug_toast_page():
        return page_layout(
            rx.container(
                rx.vstack(
                    rx.heading("F-S-051 Toast 调试面板", size="5"),
                    rx.text("点击下方按钮触发对应 Toast，验证颜色/文字/重试/队列。",
                            color="gray", size="2"),
                    rx.divider(),

                    # ── 按严重程度 ──
                    rx.text("按严重程度", weight="bold"),
                    rx.hstack(
                        _button("ℹ 信息 (info)", DebugToastState.trigger_info, "blue"),
                        _button("✅ 成功 (success)", DebugToastState.trigger_success, "green"),
                        _button("⚠ 警告 (warning)", DebugToastState.trigger_warning, "yellow"),
                        _button("❌ 错误 (error)", DebugToastState.trigger_error, "red"),
                        gap="8px",
                    ),

                    # ── 按错误码 ──
                    rx.text("按错误码", weight="bold"),
                    rx.hstack(
                        _button("文件过大", DebugToastState.trigger_file_too_large, "yellow"),
                        _button("格式不支持", DebugToastState.trigger_unsupported_format, "yellow"),
                        _button("网络超时", DebugToastState.trigger_network_timeout, "red"),
                        gap="8px",
                    ),
                    rx.hstack(
                        _button("权限不足", DebugToastState.trigger_permission_denied, "red"),
                        _button("认证失败", DebugToastState.trigger_auth_failed, "red"),
                        _button("账号锁定", DebugToastState.trigger_account_locked, "red"),
                        gap="8px",
                    ),

                    # ── 队列测试 ──
                    rx.text("队列 / 交互测试", weight="bold"),
                    rx.hstack(
                        _button("连续触发 3 个错误", DebugToastState.trigger_queue_three, "purple"),
                        _button("关闭当前 Toast", DebugToastState.dismiss_current, "gray"),
                        gap="8px",
                    ),

                    rx.divider(),
                    # ── 状态监视 ──
                    rx.text("当前状态", weight="bold", size="2"),
                    rx.code(
                        rx.text(
                            rx.foreach(
                                rx.Var.create(
                                    [(ErrorState.current_code, "current_code"),
                                     (ErrorState.current_message, "current_message"),
                                     (ErrorState.current_severity, "current_severity"),
                                     (ErrorState.current_visible, "current_visible"),
                                     (ErrorState.retry_label, "retry_label"),
                                     (ErrorState.retry_event, "retry_event"),
                                     (ErrorState.retry_counter, "retry_counter"),
                                    ]
                                ),
                                lambda item: rx.text(
                                    item[0],
                                    size="1",
                                    white_space="pre",
                                ),
                            ),
                        ),
                        width="100%",
                    ),

                    spacing="3",
                    width="100%",
                ),
                max_width="700px",
                padding="24px",
            ),
        )
