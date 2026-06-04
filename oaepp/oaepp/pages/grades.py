import reflex as rx
from ..mock_data import MockData


def _grade_card(card: dict) -> rx.Component:
    color_map = {
        "green": ("#16a34a", "#22c55e"),
        "purple": ("#9333ea", "#a855f7"),
        "orange": ("#ea580c", "#fb923c"),
        "blue": ("#2563eb", "#3b82f6"),
    }
    fill, bg = color_map.get(card["color"], ("#6b7280", "#9ca3af"))
    pct = min(card["value"] / card["total"] * 100, 100)
    badge_color = card.get("badge_color", "green")
    show_badge = card.get("badge_text")
    return rx.box(
        rx.hstack(
            rx.text(card["label"], font_size="0.75rem",
                    color="#9ca3af", font_weight="500"),
            rx.text(
                card.get("badge_text", "已更新"),
                class_name=f"text-xs bg-{badge_color}-100 text-{badge_color}-700 px-2 py-0.5 rounded-full",
            ) if show_badge else rx.text("已更新",
                class_name="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"),
            justify="between",
            align="center",
            margin_bottom="0.5rem",
        ),
        rx.hstack(
            rx.text(str(card["value"]),
                    font_size="1.5rem", font_weight="bold", color=fill),
            rx.text(f"/ {card['total']}",
                    font_size="0.875rem", color="#9ca3af"),
            gap="0.25rem",
            align="end",
        ),
        rx.box(
            rx.box(
                width=f"{pct}%", height="100%",
                bg=fill, border_radius="9999px",
            ),
            width="100%", bg="#f3f4f6",
            height="0.375rem", border_radius="9999px",
            margin_top="0.5rem",
        ),
        rx.text(card["detail"], font_size="0.75rem",
                color="#9ca3af", margin_top="0.375rem"),
        class_name="bg-white rounded-xl border border-gray-100 shadow-sm p-5",
    )


def _grade_detail_row(g: dict) -> rx.Component:
    score_font_color = {"green": "#16a34a", "orange": "#ea580c", "gray": "#9ca3af"}
    sc = g["score_color"]
    return rx.table.row(
        rx.table.cell(rx.text(g["task"], font_size="0.875rem",
                               font_weight="500", color="#1f2937")),
        rx.table.cell(rx.text(g["score"], font_weight="bold",
                               color=score_font_color.get(sc, "#6b7280"))),
        rx.table.cell(rx.text(g["reviewer"], font_size="0.75rem", color="#6b7280")),
        rx.table.cell(rx.text(g["review_time"], font_size="0.75rem", color="#9ca3af")),
        rx.table.cell(
            rx.text(g["status_label"],
                    class_name=f"text-xs bg-{g['status_color']}-100 text-{g['status_color']}-700 px-2 py-0.5 rounded-full"),
        ),
        rx.table.cell(
            rx.text("查看评语", font_size="0.75rem",
                    color="#3b82f6", _hover={"text_decoration": "underline"}),
            text_align="right",
        ),
        border_bottom="1px solid #f9fafb",
    )


def _expanded_comment() -> rx.Component:
    c = MockData.EXPANDED_COMMENT
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text("李", font_weight="bold", font_size="0.875rem", color="#1d4ed8"),
                width="2rem", height="2rem",
                border_radius="9999px", bg="#bfdbfe",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.vstack(
                rx.text(f"{c['chapter']}评语 · {c['reviewer']}",
                        font_size="0.875rem", font_weight="600", color="#1f2937"),
                rx.text(f"{c['date']} 批改",
                        font_size="0.75rem", color="#9ca3af"),
                gap="0",
                align="start",
            ),
            rx.text(c["score"], font_size="1.125rem",
                    font_weight="bold", color="#16a34a",
                    margin_left="auto"),
            gap="0.75rem",
            align="center",
            margin_bottom="0.75rem",
        ),
        rx.text(c["text"], font_size="0.875rem", color="#374151",
                line_height="1.625", margin_bottom="0.75rem"),
        rx.hstack(
            *[
                rx.text(t["text"],
                        class_name=f"text-xs bg-{t['color']}-100 text-{t['color']}-600 px-2 py-0.5 rounded")
                for t in c["tags"]
            ],
            gap="0.5rem",
            flex_wrap="wrap",
            margin_bottom="0.75rem",
        ),
        rx.box(
            rx.text("此任务允许二次提交，可基于以上反馈修改后重新提交",
                    font_size="0.75rem", color="#6b7280",
                    margin_bottom="0.5rem"),
            rx.link("前往重新提交 →", font_size="0.75rem",
                    color="#3b82f6", _hover={"text_decoration": "underline"},
                    href="/assignments"),
            border_top="1px solid #bfdbfe",
            padding_top="0.75rem",
        ),
        border="1px solid #bfdbfe",
        bg="#eff6ff",
        border_radius="0.75rem",
        padding="1.25rem",
        margin_top="1.5rem",
    )


def grades_page() -> rx.Component:
    from ..components.layout import protected_page
    body = rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("成绩与反馈", font_size="1.25rem",
                        font_weight="bold", color="#1f2937"),
                rx.text("工程实践 4 · 综合总分 87.5 / 100",
                        font_size="0.875rem", color="#9ca3af",
                        margin_top="0.125rem"),
                gap="0",
                align="start",
            ),
            rx.el.button(
                rx.hstack(
                    rx.html(
                        '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
                        'd="M12 10v6m0 0l-3-3m3 3l3-2m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586'
                        'a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>'
                    ),
                    rx.text("下载成绩单 Excel", font_size="0.875rem"),
                    gap="0.5rem",
                    align="center",
                ),
                class_name="bg-green-600 hover:bg-green-700 text-white text-sm px-4 py-2 rounded-lg transition",
            ),
            justify="between",
            align="center",
            margin_bottom="1.5rem",
            width="100%",
        ),
        rx.grid(
            *[_grade_card(c) for c in MockData.GRADE_CARDS],
            grid_template_columns="repeat(4, 1fr)",
            gap="1.25rem",
            margin_bottom="2rem",
            width="100%",
        ),
        rx.box(
            rx.hstack(
                rx.text("代码评阅详情", font_size="0.875rem",
                        font_weight="500", color="#2563eb",
                        border_bottom="2px solid #2563eb",
                        padding_y="0.75rem", padding_x="1rem"),
                rx.text("考试成绩", font_size="0.875rem",
                        color="#6b7280", _hover={"color": "#374151"},
                        padding_y="0.75rem", padding_x="1rem"),
                rx.text("出勤记录", font_size="0.875rem",
                        color="#6b7280", _hover={"color": "#374151"},
                        padding_y="0.75rem", padding_x="1rem"),
                rx.text("时间线", font_size="0.875rem",
                        color="#6b7280", _hover={"color": "#374151"},
                        padding_y="0.75rem", padding_x="1rem"),
                border_bottom="1px solid #f3f4f6",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                rx.text("任务", font_size="0.75rem", font_weight="500", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("得分", font_size="0.75rem", font_weight="500", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("批改人", font_size="0.75rem", font_weight="500", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("批改时间", font_size="0.75rem", font_weight="500", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("状态", font_size="0.75rem", font_weight="500", color="#9ca3af")),
                            rx.table.column_header_cell(""),
                        ),
                    ),
                    rx.table.body(
                        *[_grade_detail_row(g) for g in MockData.GRADE_DETAILS],
                    ),
                    width="100%",
                ),
                _expanded_comment(),
                padding="1.25rem",
            ),
            class_name="bg-white rounded-xl border border-gray-100 shadow-sm",
            width="100%",
        ),
        spacing="0",
        width="100%",
    )
    return protected_page(body, current_route="/grades")
