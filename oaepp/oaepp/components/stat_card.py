import reflex as rx


def stat_card(title: str, value: str, subtitle: str, color: str = "blue") -> rx.Component:
    color_map = {
        "blue": "blue.600",
        "green": "green.600",
        "purple": "purple.600",
        "orange": "orange.500",
    }
    return rx.box(
        rx.text(
            title,
            font_size="xs",
            color="gray.400",
            font_weight="medium",
            text_transform="uppercase",
            letter_spacing="wide",
        ),
        rx.text(
            value,
            font_size="3xl",
            font_weight="bold",
            color=color_map.get(color, "blue.600"),
            margin_top="4px",
        ),
        rx.text(subtitle, font_size="xs", color="gray.400", margin_top="4px"),
        bg="white",
        border_radius="xl",
        border="1px solid",
        border_color="gray.100",
        shadow="sm",
        padding="20px",
    )