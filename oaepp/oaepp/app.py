import reflex as rx
from oaepp.pages.dashboard import dashboard_page


def index() -> rx.Component:
    return rx.box(
        rx.text("OA-EPP - 欢迎使用工程实践平台"),
        rx.link("进入仪表盘", href="/dashboard", color="blue.500"),
        display="flex",
        flex_direction="column",
        align_items="center",
        justify_content="center",
        min_height="100vh",
    )


app = rx.App()
app.add_page(index, route="/")
app.add_page(dashboard_page, route="/dashboard")