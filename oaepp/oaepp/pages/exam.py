import reflex as rx
from ..mock_data import MockData


def _question_nav() -> rx.Component:
    answered = MockData.EXAM_ANSWERED
    current = MockData.CURRENT_EXAM["current_question_index"]
    numbers = []
    for i in range(1, MockData.CURRENT_EXAM["total_questions"] + 1):
        is_current = i == current
        is_answered = answered.get(i, False)
        if is_current:
            bg = "#f97316"
            extra = "ring-2 ring-orange-300"
        elif is_answered:
            bg = "#22c55e"
            extra = ""
        else:
            bg = "#e5e7eb"
            extra = ""
        numbers.append(
            rx.box(
                rx.text(str(i), font_size="0.75rem", font_weight="bold",
                        color="white" if (is_current or is_answered) else "#6b7280"),
                width="2rem", height="2rem",
                bg=bg, border_radius="0.25rem",
                display="flex", align_items="center", justify_content="center",
                class_name=extra,
            )
        )
    return rx.hstack(
        *numbers,
        rx.text("绿=已答 · 橙=当前 · 灰=未答",
                font_size="0.75rem", color="#9ca3af",
                margin_left="0.75rem", align_self="center"),
        gap="0.5rem",
        flex_wrap="wrap",
        margin_bottom="1rem",
    )


def _question_options(q: dict) -> rx.Component:
    opts = []
    for opt in q["options"]:
        selected = opt.get("selected", False)
        border = "border-blue-400 bg-blue-50" if selected else "border-gray-200 hover:bg-blue-50 hover:border-blue-300"
        opts.append(
            rx.box(
                rx.hstack(
                    rx.el.input(type_="radio", name=f"q{q['id']}",
                                default_checked=selected,
                                class_name="mt-0.5 text-blue-600"),
                    rx.text(
                        f"{opt['key']}. {opt['text']}",
                        font_size="0.875rem", color="#374151",
                    ),
                    gap="0.75rem",
                    align="start",
                ),
                class_name=f"flex items-start gap-3 p-3 border rounded-lg cursor-pointer {border}",
            )
        )
    return rx.vstack(*opts, gap="0.75rem", align="stretch")


def _exam_history_row(r: dict) -> rx.Component:
    score_text = str(r["score"]) if r["score"] is not None else "—"
    score_color = {"green": "#16a34a", "yellow": "#ca8a04", "gray": "#9ca3af"}
    return rx.table.row(
        rx.table.cell(rx.text(r["name"], font_size="0.875rem",
                               font_weight="500", color="#374151")),
        rx.table.cell(rx.text(r["date"], font_size="0.875rem", color="#6b7280")),
        rx.table.cell(rx.text(str(r["total"]), font_size="0.875rem", color="#4b5563")),
        rx.table.cell(
            rx.text(score_text, font_weight="bold",
                    color=score_color.get(r["score_color"], "#6b7280"),
                    font_size="0.875rem")),
        rx.table.cell(
            _status_badge(r["status"], r["status_color"])),
        rx.table.cell(
            rx.text("查看详情", font_size="0.75rem", color="#3b82f6",
                    _hover={"text_decoration": "underline"})),
        border_bottom="1px solid #f9fafb",
    )


def _status_badge(text: str, color: str) -> rx.Component:
    return rx.text(text,
                   class_name=f"px-2 py-0.5 bg-{color}-100 text-{color}-600 rounded text-xs font-medium")


def exam_page() -> rx.Component:
    from ..components.layout import protected_page
    cur = MockData.CURRENT_EXAM
    q = MockData.EXAM_QUESTIONS[0]
    body = rx.vstack(
        rx.text("在线考试", font_size="1.25rem",
                font_weight="bold", color="#1f2937",
                margin_bottom="1.5rem"),
        # Active exam card
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.box(width="0.625rem", height="0.625rem",
                               border_radius="9999px", bg="#f97316",
                               class_name="animate-pulse"),
                        rx.text("考试进行中", font_size="0.875rem",
                                font_weight="600", color="#c2410c"),
                        gap="0.5rem",
                        align="center",
                        margin_bottom="0.25rem",
                    ),
                    rx.text(cur["name"], font_size="1.125rem",
                            font_weight="bold", color="#1f2937"),
                    rx.text(
                        f"共 {cur['total_questions']} 题 | 总分 {cur['total_score']} 分 | "
                        f"限时 {cur['time_limit_min']} 分钟",
                        font_size="0.875rem", color="#6b7280",
                        margin_top="0.25rem",
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("14:23", font_size="1.875rem",
                            font_weight="bold", color="#f97316",
                            font_family="'Courier New', monospace",
                            class_name="tabular-nums"),
                    rx.text("剩余时间", font_size="0.75rem",
                            color="#6b7280", margin_top="0.25rem"),
                    align="end",
                ),
                justify="between",
                align="start",
                width="100%",
            ),
            # Progress
            rx.box(
                rx.hstack(
                    rx.text("答题进度", font_size="0.75rem", color="#6b7280"),
                    rx.text(f"{cur['answered_count']} / {cur['total_questions']} 题已作答",
                            font_size="0.75rem", color="#6b7280"),
                    justify="between",
                    width="100%",
                    margin_bottom="0.25rem",
                ),
                rx.box(
                    rx.box(
                        width=f"{cur['answered_count'] / cur['total_questions'] * 100}%",
                        height="100%", bg="#f97316", border_radius="9999px",
                    ),
                    width="100%", bg="#e5e7eb",
                    height="0.5rem", border_radius="9999px",
                ),
                margin_bottom="1rem",
            ),
            _question_nav(),
            class_name="bg-orange-50 border-2 border-orange-400 rounded-xl p-6 mb-6",
            width="100%",
        ),
        # Current question
        rx.box(
            rx.hstack(
                rx.text(f"第 {q['id']} 题 · {q['type']} · {q['score']} 分",
                        font_size="0.875rem", font_weight="500", color="#4b5563"),
                rx.text("草稿已自动保存 08:14:22",
                        font_size="0.75rem", color="#9ca3af"),
                justify="between",
                align="center",
                class_name="px-6 py-4 border-b border-gray-100",
            ),
            rx.box(
                rx.text(q["text"], font_size="0.875rem",
                        font_weight="500", color="#1f2937",
                        margin_bottom="1.25rem"),
                _question_options(q),
                class_name="px-6 py-5",
            ),
            rx.hstack(
                rx.el.button("← 上一题",
                    class_name="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50"),
                rx.el.button("下一题 →",
                    class_name="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"),
                justify="between",
                align="center",
                class_name="px-6 py-4 border-t border-gray-100",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm mb-4",
            width="100%",
        ),
        # Submit warning
        rx.box(
            rx.hstack(
                rx.text(
                    rx.text.span("注意：", font_weight="500", color="#ef4444"),
                    "提交后不可修改。截止时间到将自动提交当前已作答内容。",
                    font_size="0.875rem", color="#6b7280",
                ),
                rx.el.button("提交试卷",
                    class_name="px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white font-bold rounded-lg text-sm shadow"),
                justify="between",
                align="center",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-5",
            width="100%",
        ),
        # Exam history
        rx.box(
            rx.text("历史考试成绩", font_size="0.875rem",
                    font_weight="600", color="#1f2937",
                    class_name="px-5 py-4 border-b border-gray-100"),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                rx.text("考试名称", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("考试时间", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("总分", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("得分", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("状态", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("操作", font_size="0.75rem", color="#9ca3af")),
                        ),
                    ),
                    rx.table.body(
                        *[_exam_history_row(r) for r in MockData.EXAM_HISTORY_RECORDS],
                    ),
                    width="100%",
                ),
                class_name="px-5 py-4",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm mt-6",
            width="100%",
        ),
        spacing="0",
        width="100%",
    )
    return protected_page(body, current_route="/exam")
