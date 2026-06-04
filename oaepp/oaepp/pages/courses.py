import reflex as rx
from ..mock_data import MockData
from ..components.layout import protected_page


def _course_card(course: dict) -> rx.Component:
    is_current = course.get("is_current", False)
    border_color = "border-blue-300" if is_current else "border-gray-100"
    box_shadow = "0 4px 6px -1px rgba(0,0,0,0.1)" if is_current else "0 1px 3px rgba(0,0,0,0.08)"
    progress_pct = course["completed"] / course["tasks"] * 100

    status_colors = {
        "completed": ("green", "#16a34a", "#dcfce7"),
        "active": ("blue", "#2563eb", "#dbeafe"),
    }
    _, score_color, _ = status_colors.get(course["status"], ("gray", "#6b7280", "#f3f4f6"))

    return rx.box(
        rx.cond(
            is_current,
            rx.box(
                rx.text("当前学期", font_size="0.75rem", color="white",
                        bg="#2563eb", padding_x="0.75rem", padding_y="0.125rem",
                        border_radius="9999px", box_shadow="0 1px 3px rgba(0,0,0,0.2)",
                        position="absolute", top="-0.625rem", right="1rem"),
            ),
        ),
        rx.hstack(
            rx.vstack(
                rx.box(
                    rx.text(course["status_label"], font_size="0.75rem",
                            font_weight="500",
                            color={"completed": "#16a34a", "active": "#2563eb"}
                            .get(course["status"], "#6b7280"),
                            bg={"completed": "#dcfce7", "active": "#dbeafe"}
                            .get(course["status"], "#f3f4f6"),
                            padding_x="0.5rem", padding_y="0.125rem",
                            border_radius="9999px",
                    ),
                    rx.text(course["name"], font_size="1rem",
                            font_weight="600", color="#1f2937",
                            margin_top="0.25rem"),
                    rx.text(f"{course['semester']} · 共 {course['chapters']} 章节 · "
                            f"{course['tasks']} 任务",
                            font_size="0.75rem", color="#9ca3af",
                            margin_top="0.125rem"),
                    align="start",
                ),
                flex="1",
                align="start",
            ),
            rx.vstack(
                rx.text(str(course["total_score"]), font_size="1.5rem",
                        font_weight="bold", color=score_color),
                rx.text("总评", font_size="0.75rem", color="#9ca3af"),
                align="center",
                spacing="0",
            ),
            justify="between",
            align="start",
            margin_bottom="0.75rem",
        ),
        rx.box(
            rx.box(
                rx.box(
                    height="100%",
                    bg=score_color,
                    border_radius="9999px",
                    width=f"{progress_pct}%",
                ),
                width="100%", bg="#f3f4f6",
                height="0.375rem", border_radius="9999px",
            ),
            margin_bottom="0.75rem",
        ),
        rx.hstack(
            rx.text(f"完成进度 {course['completed']}/{course['tasks']} 任务",
                    font_size="0.75rem", color="#9ca3af"),
            rx.cond(
                is_current,
                rx.text("· 2 项即将截止",
                        font_size="0.75rem", color="#ef4444"),
            ),
            flex="1",
            margin_bottom="0.5rem",
        ),
        rx.link("查看课程详情 →",
                href="#" if not is_current else "/courses",
                font_size="0.75rem", color="#2563eb",
                _hover={"text_decoration": "underline"},
                underline="none"),
        position="relative",
        bg="white", border_radius="0.75rem",
        border=f"2px solid {border_color}" if is_current else "1px solid #f3f4f6",
        box_shadow=box_shadow,
        padding="1.5rem",
    )


def _chapter_row(ch: dict) -> rx.Component:
    status_badge = rx.box(
        rx.text(ch["status_label"], font_size="0.75rem"),
        padding_x="0.5rem", padding_y="0.125rem",
        border_radius="9999px",
        bg={"green": "#dcfce7", "yellow": "#fef9c3", "red": "#fef2f2", "gray": "#f3f4f6"}
        .get(ch["status_color"], "#f3f4f6"),
        color={"green": "#16a34a", "yellow": "#ca8a04", "red": "#dc2626", "gray": "#6b7280"}
        .get(ch["status_color"], "#6b7280"),
        display="inline-block",
    )
    score_el = (
        rx.text(ch["score"], font_size="0.875rem", font_weight="600", color="#16a34a")
        if ch["score"]
        else rx.text("—", color="#9ca3af")
    )
    action_link = rx.link(
        {"graded": "查看", "pending": "查看", "todo": "提交", "upcoming": "查看"}
        .get(ch["status"], "查看"),
        href={
            "graded": "/grades",
            "pending": "/grades",
            "todo": "/assignments",
            "upcoming": "/courses",
        }.get(ch["status"], "/courses"),
        font_size="0.75rem", color="#2563eb",
        _hover={"text_decoration": "underline"},
        underline="none",
        text_align="right",
    )

    return rx.table.row(
        rx.table.cell(rx.text(ch["ch"], font_size="0.75rem", color="#9ca3af")),
        rx.table.cell(rx.text(ch["title"], font_size="0.875rem", font_weight="500",
                               color="#1f2937")),
        rx.table.cell(
            rx.text(ch["deadline"], font_size="0.75rem",
                    color="#dc2626" if "⚠️" in ch["deadline"] else "#9ca3af",
                    font_weight="500" if "⚠️" in ch["deadline"] else "normal"),
        ),
        rx.table.cell(status_badge),
        rx.table.cell(score_el),
        rx.table.cell(action_link),
        border_bottom="1px solid #f9fafb",
    )


def courses_page() -> rx.Component:
    course_cards = rx.grid(
        *[_course_card(c) for c in MockData.COURSES],
        grid_template_columns="repeat(2, 1fr)",
        gap="1.5rem",
        margin_bottom="2rem",
    )

    current_course = next(c for c in MockData.COURSES if c.get("is_current"))
    chapter_rows = [_chapter_row(ch) for ch in MockData.CHAPTERS]

    chapters_table = rx.box(
        rx.hstack(
            rx.text(f"{current_course['name']} · 章节列表",
                    font_size="0.875rem", font_weight="600", color="#374151"),
            rx.select(
                ["全部状态", "已完成", "进行中", "待开始"],
                default_value="全部状态",
                font_size="0.75rem",
                width="auto",
            ),
            justify="between",
            align="center",
            margin_bottom="1.25rem",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(
                        rx.text("章节", font_size="0.75rem", font_weight="500", color="#6b7280")),
                    rx.table.column_header_cell(
                        rx.text("标题", font_size="0.75rem", font_weight="500", color="#6b7280")),
                    rx.table.column_header_cell(
                        rx.text("截止时间", font_size="0.75rem", font_weight="500", color="#6b7280")),
                    rx.table.column_header_cell(
                        rx.text("状态", font_size="0.75rem", font_weight="500", color="#6b7280")),
                    rx.table.column_header_cell(
                        rx.text("得分", font_size="0.75rem", font_weight="500", color="#6b7280")),
                    rx.table.column_header_cell(rx.text("", font_size="0.75rem")),
                ),
            ),
            rx.table.body(*chapter_rows),
            width="100%",
        ),
        bg="white", border_radius="0.75rem",
        border="1px solid #f3f4f6",
        box_shadow="0 1px 3px rgba(0,0,0,0.08)",
        padding="1.5rem",
    )

    content = rx.vstack(
        rx.vstack(
            rx.text("课程列表", font_size="1.25rem", font_weight="bold",
                    color="#1f2937"),
            rx.text("已选课程 · 工程实践 1–4",
                    font_size="0.875rem", color="#9ca3af", margin_top="0.125rem"),
            align="start",
            spacing="0",
        ),
        course_cards,
        chapters_table,
        align="start",
        spacing="0",
        width="100%",
    )

    return protected_page(content, current_route="/courses")
