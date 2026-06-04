import reflex as rx
from ..mock_data import MockData


NAV_ICONS = {
    "home": (
        "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10"
        "a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 01"
        "1 1v4a1 1 0 001 1m-6 0h6"
    ),
    "book": (
        "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 "
        "6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0"
        "-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253"
        "v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
    ),
    "clipboard": (
        "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00"
        "-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 "
        "012 2"
    ),
    "chart": (
        "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002"
        "-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 "
        "002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 "
        "01-2-2z"
    ),
    "check": (
        "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00"
        "-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 "
        "012 2m-6 9l2 2 4-4"
    ),
    "edit": (
        "M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L"
        "6.5 21.036H3v-3.572L16.732 3.732z"
    ),
    "user": (
        "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
    ),
}


def _nav_icon(icon_name: str) -> rx.Component:
    path = NAV_ICONS.get(icon_name, NAV_ICONS["home"])
    return rx.html(
        f'<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        f'd="{path}"/></svg>'
    )


def sidebar(current_route: str = "/") -> rx.Component:
    s = MockData.STUDENT
    nav_links = []
    for item in MockData.NAV_ITEMS:
        is_active = item["route"] == current_route
        link_class = (
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm "
            + (
                "bg-blue-50 text-blue-700 font-medium"
                if is_active
                else "text-gray-600 hover:bg-gray-50"
            )
        )
        link = rx.link(
            rx.hstack(
                _nav_icon(item["icon"]),
                rx.text(item["name"], font_size="0.875rem"),
                class_name=link_class[link_class.index("flex"):],
                gap="0.75rem",
                align="center",
            ),
            href=item["route"],
            underline="none",
        )
        nav_links.append(link)

    return rx.box(
        # Brand
        rx.hstack(
            rx.box(
                rx.html(
                    '<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" '
                    'viewBox="0 0 24 24">'
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
                    'd="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 '
                    '014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 '
                    '3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 '
                    '3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 '
                    '01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 '
                    '3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 '
                    '00.806-1.946 3.42 3.42 0 013.138-3.138z"/>'
                    '</svg>'
                ),
                width="2rem",
                height="2rem",
                bg="#2563eb",
                border_radius="0.5rem",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text("OA-EPP", font_weight="bold", color="#1f2937", font_size="0.875rem"),
            gap="0.625rem",
            align="center",
            padding_x="1.25rem",
            padding_y="1.25rem",
            border_bottom="1px solid #f3f4f6",
        ),
        # Nav
        rx.vstack(
            *nav_links,
            gap="1",
            padding_x="0.75rem",
            padding_y="1rem",
            flex="1",
        ),
        # User Info
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text(s["avatar_char"],
                            font_weight="bold", font_size="0.875rem", color="#1d4ed8"),
                    width="2rem", height="2rem",
                    border_radius="9999px",
                    bg="#dbeafe",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text(s["name"], font_size="0.875rem",
                            font_weight="500", color="#1f2937", truncate=True),
                    rx.text(s["student_id"], font_size="0.75rem",
                            color="#9ca3af", truncate=True),
                    gap="0",
                    align="start",
                    spacing="0",
                ),
                gap="0.75rem",
                align="center",
            ),
            rx.link(
                rx.text("退出登录", font_size="0.75rem", color="#9ca3af",
                        _hover={"color": "#ef4444"}),
                href="/login",
                margin_top="0.75rem",
                display="block",
                text_align="center",
                underline="none",
            ),
            padding_x="1rem",
            padding_y="1rem",
            border_top="1px solid #f3f4f6",
        ),
        width="14rem",
        bg="white",
        border_right="1px solid #e5e7eb",
        display="flex",
        flex_direction="column",
        height="100vh",
        position="fixed",
        left="0",
        top="0",
    )
