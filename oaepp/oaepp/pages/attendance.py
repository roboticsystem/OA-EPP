import reflex as rx
from ..mock_data import MockData


def _attendance_record_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(r["week"], font_size="0.75rem", color="#6b7280")),
        rx.table.cell(rx.text(r["date"], font_size="0.875rem")),
        rx.table.cell(rx.text(r["course"], font_size="0.875rem", color="#4b5563")),
        rx.table.cell(rx.text(r["time"], font_size="0.875rem", color="#6b7280")),
        rx.table.cell(
            rx.text(r["status_label"],
                    class_name=f"px-2 py-0.5 bg-{r['status_color']}-100 text-{r['status_color']}-600 rounded text-xs font-medium"),
        ),
        border_bottom="1px solid #f9fafb",
    )


def _status_badge(text: str, color: str) -> rx.Component:
    return rx.text(text,
                   class_name=f"px-2 py-0.5 bg-{color}-100 text-{color}-600 rounded text-xs font-medium")


def attendance_page() -> rx.Component:
    from ..components.layout import protected_page
    s = MockData.ATTENDANCE_STATS
    cur = MockData.CURRENT_CHECKIN
    body = rx.vstack(
        rx.text("课堂签到", font_size="1.25rem",
                font_weight="bold", color="#1f2937",
                margin_bottom="1.5rem"),
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.box(width="0.625rem", height="0.625rem",
                               border_radius="9999px", bg="#22c55e",
                               class_name="animate-pulse"),
                        rx.text("正在进行中", font_size="0.875rem",
                                font_weight="600", color="#15803d"),
                        gap="0.5rem",
                        align="center",
                        margin_bottom="0.25rem",
                    ),
                    rx.text(cur["course"], font_size="1.125rem",
                            font_weight="bold", color="#1f2937",
                            margin_bottom="0.25rem"),
                    rx.text(
                        f"教师：{cur['teacher']} | 地点：{cur['location']} | "
                        f"课程：{cur['date']}",
                        font_size="0.875rem", color="#6b7280",
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("00:42", font_size="1.875rem",
                            font_weight="bold", color="#ef4444",
                            font_family="'Courier New', monospace",
                            class_name="tabular-nums"),
                    rx.text("剩余秒数", font_size="0.75rem",
                            color="#6b7280", margin_top="0.25rem"),
                    align="end",
                ),
                justify="between",
                align="start",
                width="100%",
            ),
            # Progress bar
            rx.box(
                rx.box(
                    rx.box(width=f"{cur['progress_pct']}%", height="100%",
                           bg="#22c55e", border_radius="9999px"),
                    width="100%", bg="#e5e7eb",
                    height="0.5rem", border_radius="9999px",
                ),
                rx.hstack(
                    rx.text("签到开始", font_size="0.75rem", color="#9ca3af"),
                    rx.text(f"{cur['window_seconds']} 秒窗口期",
                            font_size="0.75rem", color="#9ca3af"),
                    justify="between",
                    width="100%",
                    margin_top="0.25rem",
                ),
                margin_top="1rem",
                margin_bottom="1rem",
            ),
            # Check-in button
            rx.hstack(
                rx.el.button(
                    "确认签到",
                    class_name=(
                        "px-8 py-3 bg-green-600 hover:bg-green-700 "
                        "text-white font-bold rounded-lg text-base shadow"
                    ),
                ),
                rx.text("签到前请确认已在教室内",
                        font_size="0.875rem", color="#6b7280"),
                gap="0.75rem",
                align="center",
                margin_bottom="0.75rem",
            ),
            # Geo fence hint
            rx.box(
                rx.hstack(
                    rx.html(
                        '<svg class="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" '
                        'fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
                        'd="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243'
                        'a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" '
                        'stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>'
                    ),
                    rx.text(
                        f"地理围栏验证已启用：{cur['geo_hint']}",
                        font_size="0.75rem", color="#a16207",
                    ),
                    gap="0.5rem",
                    align="start",
                ),
                class_name="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg",
            ),
            class_name="bg-green-50 border-2 border-green-400 rounded-xl p-6 mb-6",
            width="100%",
        ),
        # Attendance records
        rx.box(
            rx.hstack(
                rx.text("本学期出勤记录", font_size="0.875rem",
                        font_weight="600", color="#1f2937"),
                rx.hstack(
                    rx.text(f"总计 {s['total']} 次", font_size="0.875rem", color="#6b7280"),
                    rx.text(f"出勤 {s['present']}", font_size="0.875rem", color="#16a34a"),
                    rx.text(f"迟到 {s['late']}", font_size="0.875rem", color="#eab308"),
                    rx.text(f"缺勤 {s['absent']}", font_size="0.875rem", color="#ef4444"),
                    gap="1rem",
                ),
                justify="between",
                align="center",
                class_name="px-5 py-4 border-b border-gray-100",
            ),
            # Rate bar
            rx.box(
                rx.hstack(
                    rx.text("出勤率", font_size="0.875rem", color="#6b7280", width="4rem"),
                    rx.box(
                        rx.box(width=f"{s['rate_pct']}%", height="100%",
                               bg="#3b82f6", border_radius="9999px"),
                        flex="1", bg="#f3f4f6",
                        height="0.75rem", border_radius="9999px",
                    ),
                    rx.text(f"{s['rate_pct']}%", font_size="0.875rem",
                            font_weight="bold", color="#2563eb",
                            width="3rem", text_align="right"),
                    gap="0.75rem",
                    align="center",
                ),
                class_name="px-5 pt-4 pb-2",
            ),
            # Table
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                rx.text("周次", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("日期", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("课程", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("签到时间", font_size="0.75rem", color="#9ca3af")),
                            rx.table.column_header_cell(
                                rx.text("状态", font_size="0.75rem", color="#9ca3af")),
                        ),
                    ),
                    rx.table.body(
                        *[_attendance_record_row(r) for r in MockData.ATTENDANCE_RECORDS],
                    ),
                    width="100%",
                ),
                class_name="px-5 py-4",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm mb-6",
            width="100%",
        ),
        # Scoring rules
        rx.box(
            rx.text("出勤得分计算规则", font_size="0.875rem",
                    font_weight="600", color="#1f2937",
                    class_name="px-5 py-4 border-b border-gray-100"),
            rx.box(
                rx.grid(
                    rx.box(
                        rx.text(str(s['max_score']), font_size="1.5rem",
                                font_weight="bold", color="#2563eb"),
                        rx.text("总分", font_size="0.75rem", color="#6b7280",
                                margin_top="0.25rem"),
                        class_name="bg-blue-50 rounded-lg p-4 text-center",
                    ),
                    rx.box(
                        rx.text(str(s['estimated_score']), font_size="1.5rem",
                                font_weight="bold", color="#16a34a"),
                        rx.text("当前得分（估算）", font_size="0.75rem",
                                color="#6b7280", margin_top="0.25rem"),
                        class_name="bg-green-50 rounded-lg p-4 text-center",
                    ),
                    rx.box(
                        rx.text(f"{s['rate_pct']}%", font_size="1.5rem",
                                font_weight="bold", color="#ca8a04"),
                        rx.text("出勤率", font_size="0.75rem",
                                color="#6b7280", margin_top="0.25rem"),
                        class_name="bg-yellow-50 rounded-lg p-4 text-center",
                    ),
                    grid_template_columns="repeat(3, 1fr)",
                    gap="1rem",
                    margin_bottom="1rem",
                ),
                rx.vstack(
                    *[
                        rx.hstack(
                            rx.box(width="1rem", height="1rem",
                                   class_name=f"bg-{rule['color']}-100 rounded flex-shrink-0 mt-0.5"),
                            rx.text(rule["text"], font_size="0.875rem", color="#4b5563"),
                            gap="0.5rem",
                            align="start",
                        )
                        for rule in MockData.ATTENDANCE_RULES
                    ],
                    gap="0.25rem",
                    align="stretch",
                ),
                rx.text("出勤得分 = 出勤率 × 本项满分（15 分），最终成绩发布后以教师确认为准。",
                        font_size="0.75rem", color="#9ca3af",
                        margin_top="0.5rem"),
                class_name="px-5 py-4",
            ),
            class_name="bg-white rounded-xl border border-gray-200 shadow-sm",
            width="100%",
        ),
        spacing="0",
        width="100%",
    )
    return protected_page(body, current_route="/attendance")
