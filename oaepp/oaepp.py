import reflex as rx

from oaepp.pages.login import login
from oaepp.pages.dashboard import dashboard


app = rx.App()

app.add_page(
    login,
    route="/",
    title="OA-EPP 登录",
)

app.add_page(
    dashboard,
    route="/dashboard",
    title="OA-EPP 仪表盘",
)
