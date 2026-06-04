"""
Minimal Reflex profile page.
Provides `profile_page` when Reflex is available.
"""
try:
    import reflex as rx
except Exception:
    rx = None

profile_page = None
if rx is not None:
    def profile_page():
        """A minimal profile page."""
        return rx.center(
            rx.box(
                rx.vstack(
                    rx.avatar(name="用户", size="9"),
                    rx.heading("个人资料", size="6"),
                    rx.text("这里将展示用户信息", color="gray"),
                    rx.divider(),
                    rx.hstack(
                        rx.text("姓名：", weight="medium"),
                        rx.text("示例用户"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.text("学号：", weight="medium"),
                        rx.text("2024001"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.text("邮箱：", weight="medium"),
                        rx.text("user@example.com"),
                        spacing="2",
                    ),
                    rx.button("返回首页", on_click=rx.redirect("/")),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                max_width="460px",
                width="100%",
                padding="28px",
                border_radius="12px",
                box_shadow="0 10px 30px rgba(0,0,0,0.08)",
                background="white",
            ),
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
            padding="20px",
        )
