try:
    import reflex as rx
except Exception:
    rx = None

if rx is not None:
    from states.devops_state import DevOpsState


    def render_log(log: dict) -> rx.Component:
        return rx.text(
            log["text"],
            class_name=rx.cond(
                log["is_error"],
                "text-red-400",
                "text-green-400"
            ) + " font-mono text-sm whitespace-pre-wrap"
        )

    def admin_devops_page() -> rx.Component:
        return rx.vstack(
            rx.heading("自动化脚本执行向导", size="lg", margin_bottom="2rem"),

            rx.hstack(
                rx.text("执行进度：", font_weight="bold"),
                rx.text(f"{DevOpsState.current_step} / {DevOpsState.total_steps}"),
                rx.progress(
                    value=rx.cond(
                        DevOpsState.total_steps > 0,
                        (DevOpsState.current_step / DevOpsState.total_steps) * 100,
                        0
                    ),
                    width="100%",
                ),
                width="100%",
                spacing="4",
                align_items="center",
            ),

            rx.box(
                rx.foreach(DevOpsState.logs, render_log),
                class_name="bg-gray-900 p-4 rounded-md w-full font-mono overflow-y-auto",
                min_h="400px",
                max_h="500px",
            ),

            rx.hstack(
                rx.cond(
                    DevOpsState.status == "success",
                    rx.text("✅ 执行成功", class_name="text-green-500 font-bold text-lg"),
                    rx.cond(
                        DevOpsState.status == "failed",
                        rx.text("❌ 执行失败", class_name="text-red-500 font-bold text-lg"),
                        rx.cond(
                            DevOpsState.status == "running",
                            rx.spinner(color="blue", size="md"),
                            rx.text("⏳ 等待执行", class_name="text-gray-500")
                        )
                    )
                ),
                rx.spacer(),
                rx.cond(
                    DevOpsState.error_log != "",
                    rx.button(
                        "复制错误日志",
                        on_click=rx.set_clipboard(DevOpsState.error_log),
                        variant="outline",
                        color_scheme="red",
                    ),
                ),
                rx.cond(
                    DevOpsState.status == "failed",
                    rx.button(
                        "重试失败步骤",
                        on_click=DevOpsState.retry_failed,
                        color_scheme="orange",
                        variant="solid",
                    ),
                ),
                rx.button(
                    "一键执行",
                    on_click=DevOpsState.execute_scripts,
                    color_scheme="blue",
                    is_disabled=DevOpsState.status == "running",
                ),
                width="100%",
                padding_top="1rem",
                align_items="center",
            ),

            padding="2rem",
            max_width="900px",
            margin="0 auto",
        )
