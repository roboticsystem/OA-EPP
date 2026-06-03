import reflex as rx

config = rx.Config(
    app_name="oaepp",
    app_module_import="oaepp",
    title="OA-EPP · 仪表盘",
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
