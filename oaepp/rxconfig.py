import reflex as rx

config = rx.Config(
    app_name="oaepp",
    app_module_import="oaepp",
    title="OA-EPP",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)