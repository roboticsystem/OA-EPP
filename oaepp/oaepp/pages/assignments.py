import reflex as rx
from ..mock_data import MockData


STATUS_STYLES = {
    "todo": ("bg-red-100 text-red-600", "紧急"),
    "pending": ("bg-yellow-100 text-yellow-700", "等待"),
    "graded": ("bg-green-100 text-green-700", "完成"),
    "late": ("bg-orange-100 text-orange-600", "警告"),
}


def _filter_buttons() -> rx.Component:
    filters = ["全部", "待提交", "已提交", "已批改"]
    buttons = []
    for i, label in enumerate(filters):
        active = i == 0
        buttons.append(
            rx.el.button(
                label,
                class_name=(
                    "text-xs px-3 py-1 rounded-full "
                    + ("bg-blue-600 text-white" if active else "bg-gray-100 text-gray-600 hover:bg-gray-200")
                ),
            )
        )
    return rx.hstack(
        rx.text("筛选：", font_size="0.75rem", font_weight="500", color="#4b5563"),
        *buttons,
        gap="0.75rem",
        align="center",
    )


def _icon_warning() -> rx.Component:
    return rx.html(
        '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        'd="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333'
        '-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>'
    )


def _icon_clock() -> rx.Component:
    return rx.html(
        '<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        'd="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    )


def _icon_check() -> rx.Component:
    return rx.html(
        '<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
        'd="M5 13l4 4L19 7"/></svg>'
    )


def _assign_icon(icon_type: str) -> rx.Component:
    m = {"warning": _icon_warning, "clock": _icon_clock, "check": _icon_check}
    fn = m.get(icon_type, _icon_warning)
    return fn()


def _assignment_item(a: dict) -> rx.Component:
    status_color_map = {
        "todo": "red", "pending": "yellow", "graded": "green", "late": "orange",
    }
    icon_bg = {
        "red": "bg-red-100", "yellow": "bg-yellow-100",
        "green": "bg-green-100", "orange": "bg-orange-100",
    }
    sc = status_color_map.get(a["status"], "gray")
    body = []

    title_row = rx.hstack(
        rx.text(a["title"], font_size="0.875rem",
                font_weight="semibold" if a["status"] == "todo" else "medium",
                color="#1f2937" if a["status"] == "todo" else "#374151"),
        rx.text(a["status_label"],
                class_name=f"text-xs bg-{sc}-100 text-{sc}-600 px-1.5 py-0.5 rounded"),
        gap="0.5rem",
        align="center",
        margin_bottom="0.125rem",
    )
    body.append(title_row)

    if a["status"] == "todo":
        body.append(rx.text(f"截止：{a['deadline']} · 剩余 {a['remaining']}",
                            font_size="0.75rem", color="#ef4444"))
        body.append(rx.text(a.get("notes", ""),
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.125rem"))
    elif a["status"] == "pending":
        body.append(rx.text(f"提交时间：{a['submitted_at']} · {a['version']} · {a['file_size']}",
                            font_size="0.75rem", color="#9ca3af"))
        body.append(rx.text(f"文件：{a['file_name']}",
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.125rem"))
    elif a["status"] == "graded":
        body.append(rx.text(f"得分：{a['score']} · 批改时间：{a['graded_at']}",
                            font_size="0.75rem", color="#9ca3af"))
        body.append(rx.text(f"{a['version']} · {a.get('notes', '')}",
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.125rem"))
    elif a["status"] == "late":
        body.append(rx.text(f"提交时间：{a['submitted_at']}（截止：{a['deadline_original']}）",
                            font_size="0.75rem", color="#9ca3af"))
        body.append(rx.text(a.get("notes", ""),
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.125rem"))

    contents = rx.hstack(
        rx.box(_assign_icon(a["icon_type"]),
               class_name=f"w-10 h-10 rounded-lg {icon_bg[sc]} flex items-center justify-center flex-shrink-0"),
        rx.vstack(*body, flex="1", min_width="0"),
        rx.html(
            '<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>'
        ),
        gap="1rem",
        align="center",
    )

    return rx.box(
        contents,
        class_name="px-5 py-4 flex items-center gap-4",
        border_bottom="1px solid #f9fafb",
        _hover={"bg": "#eff6ff"},
    )


def _submit_panel() -> rx.Component:
    a = MockData.ACTIVE_ASSIGNMENT
    return rx.box(
        rx.box(
            rx.hstack(
                rx.box(width="0.5rem", height="0.5rem",
                       border_radius="9999px", bg="#ef4444"),
                rx.text("提交作业", font_size="0.875rem",
                        font_weight="600", color="#1f2938"),
                gap="0.5rem",
                align="center",
                margin_bottom="0.25rem",
            ),
            rx.text(
                f"{a['title']} · 截止 {a['deadline']}",
                font_size="0.75rem", color="#6b7280",
                margin_bottom="1rem",
            ),
            # Text area
            rx.vstack(
                rx.text("说明（可选）", font_size="0.75rem",
                        font_weight="500", color="#4b5563",
                        margin_bottom="0.25rem"),
                rx.text_area(
                    placeholder="填写提交说明或备注...",
                    rows="3",
                    width="100%",
                    border="1px solid #e5e7eb",
                    border_radius="0.5rem",
                    padding="0.75rem",
                    font_size="0.875rem",
                    resize="none",
                    _focus={"outline": "none", "ring": "2px", "border_color": "#60a5fa"},
                ),
                gap="0.25rem",
                align="stretch",
                margin_bottom="1rem",
            ),
            # Drop zone
            rx.box(
                rx.html(
                    '<svg class="w-8 h-8 text-gray-300 mx-auto mb-2" fill="none" '
                    'stroke="currentColor" viewBox="0 0 24 24">'
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
                    'd="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9'
                    'M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>'
                ),
                rx.text("拖拽文件到此处，或", font_size="0.75rem", color="#9ca3af"),
                rx.text("选择文件", font_size="0.75rem",
                        color="#3b82f6", _hover={"text_decoration": "underline"},
                        margin_top="0.25rem"),
                rx.text(f"支持 {a['file_types']} · 最大 {a['max_size']}",
                        font_size="0.75rem", color="#d1d5db", margin_top="0.25rem"),
                text_align="center",
                padding="1.25rem",
                border="2px dashed #e5e7eb",
                border_radius="0.5rem",
                margin_bottom="1rem",
                _hover={"border_color": "#93c5fd"},
            ),
            # Version info
            rx.box(
                rx.text(
                    rx.text.span("当前版本：", font_weight="500", color="#374151"),
                    a["current_version"],
                    font_size="0.75rem", color="#6b7280",
                ),
                rx.text("教师允许多次重新提交",
                        font_size="0.75rem", color="#6b7280"),
                class_name="bg-gray-50 rounded-lg px-3 py-2 mb-4",
            ),
            # Submit button
            rx.el.button(
                "确认提交",
                class_name=(
                    "w-full bg-blue-600 hover:bg-blue-700 text-white "
                    "text-sm font-semibold py-2.5 rounded-lg transition"
                ),
            ),
            rx.text("提交后可在截止前重新上传",
                    font_size="0.75rem", color="#9ca3af",
                    text_align="center", margin_top="0.5rem"),
            class_name="bg-white rounded-xl border-2 border-blue-200 shadow-sm p-5",
        ),
        # Version history
        rx.box(
            rx.text("第6章提交版本记录", font_size="0.75rem",
                    font_weight="600", color="#4b5563",
                    margin_bottom="0.75rem"),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.text(v["version"], font_size="0.75rem", color="#9ca3af"),
                        rx.text(v["file_name"], font_size="0.75rem",
                                color="#4b5563", flex="1"),
                        rx.text(v["date"], font_size="0.75rem", color="#9ca3af"),
                        gap="0.75rem",
                        align="center",
                    )
                    for v in MockData.VERSION_HISTORY
                ],
                gap="0.5rem",
            ),
            class_name="bg-white rounded-xl border border-gray-100 shadow-sm p-5 mt-4",
        ),
        width="20rem",
        flex_shrink="0",
    )


def assignments_page() -> rx.Component:
    from ..components.layout import protected_page
    body = rx.vstack(
        rx.box(
            rx.text("作业提交", font_size="1.25rem",
                    font_weight="bold", color="#1f2937"),
            rx.text("工程实践 4 · 2025 春", font_size="0.875rem",
                    color="#9ca3af", margin_top="0.125rem"),
            margin_bottom="1.5rem",
        ),
        rx.hstack(
            rx.box(
                rx.box(
                    _filter_buttons(),
                    class_name="flex items-center gap-3 px-5 py-3 border-b border-gray-100",
                ),
                rx.vstack(
                    *[_assignment_item(a) for a in MockData.ASSIGNMENTS],
                    gap="0",
                ),
                class_name="bg-white rounded-xl border border-gray-100 shadow-sm",
                flex="1",
                min_width="0",
            ),
            _submit_panel(),
            gap="1.5rem",
        ),
        spacing="0",
        width="100%",
    )
    return protected_page(body, current_route="/assignments")
