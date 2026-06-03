import reflex as rx
from oaepp.theme import c, FONT

COLOR_MAP = {
    "blue": c("blue.600"),
    "green": c("green.600"),
    "purple": c("purple.600"),
    "orange": c("orange.500"),
}


def stat_card(title: str, value: str, subtitle: str, color: str = "blue") -> rx.Component:
    return rx.box(
        rx.el.p(
            title,
            style={
                "font_size": "12px",
                "color": c("gray.400"),
                "font_weight": "500",
                "text_transform": "uppercase",
                "letter_spacing": "0.05em",
                "margin": "0",
                "font_family": FONT,
            },
        ),
        rx.el.p(
            value,
            style={
                "font_size": "30px",
                "font_weight": "700",
                "color": COLOR_MAP.get(color, c("blue.600")),
                "margin": "4px 0 0 0",
                "font_family": FONT,
                "line_height": "1.2",
            },
        ),
        rx.el.p(
            subtitle,
            style={
                "font_size": "12px",
                "color": c("gray.400"),
                "margin": "4px 0 0 0",
                "font_family": FONT,
            },
        ),
        style={
            "background": "white",
            "border_radius": "12px",
            "border": f"1px solid {c('gray.100')}",
            "box_shadow": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
            "padding": "20px",
        },
    )
