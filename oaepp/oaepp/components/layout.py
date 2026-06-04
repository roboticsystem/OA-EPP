import reflex as rx
from .sidebar import sidebar


def protected_page(content: rx.Component, current_route: str = "/") -> rx.Component:
    """Wrap a page with sidebar layout for authenticated pages."""
    return rx.hstack(
        sidebar(current_route=current_route),
        rx.box(
            content,
            margin_left="14rem",
            flex="1",
            padding="2rem",
            bg="#f9fafb",
            min_height="100vh",
        ),
        spacing="0",
        width="100%",
        min_height="100vh",
    )
