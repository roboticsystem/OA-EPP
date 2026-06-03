import reflex as rx


def navbar():
    return rx.hstack(
        rx.link("OA-EPP", href="/"),
        rx.spacer(),
        padding="1rem",
        width="100%",
        border_bottom="1px solid #e5e7eb",
    )