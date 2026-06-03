import reflex as rx


def stat_card(title: str, value: str, desc: str, color: str):
    return rx.box(
        rx.text(
            title,
            color="#9ca3af",
            font_size="0.75rem",
            font_weight="600",
            text_transform="uppercase",
            letter_spacing="0.04em",
        ),
        rx.text(
            value,
            color=color,
            font_size="2rem",
            font_weight="800",
            margin_top="0.25rem",
        ),
        rx.text(
            desc,
            color="#9ca3af",
            font_size="0.75rem",
            margin_top="0.25rem",
        ),
        background="white",
        border="1px solid #f3f4f6",
        border_radius="0.75rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        padding="1.25rem",
        width="100%",
    )
