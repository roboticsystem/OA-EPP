import reflex as rx
from ..mock_data import MockData
from ..components.layout import protected_page


def _score_card(label: str, value: float, total: int, color: str, sub: str | None) -> rx.Component:
    color_map = {
        "blue": ("#2563eb", "#dbeafe"),
        "green": ("#16a34a", "#dcfce7"),
        "purple": ("#9333ea", "#f3e8ff"),
        "orange": ("#f97316", "#fff7ed"),
    }
    main_color, bg_color = color_map.get(color, color_map["blue"])
    return rx.box(
        rx.text(label, font_size="0.75rem", color="#9ca3af",
                font_weight="500", text_transform="uppercase"),
        rx.text(str(value), font_size="1.875rem", font_weight="bold",
                color=main_color, margin_top="0.25rem"),
        rx.text(f"满分 {total} 分", font_size="0.75rem", color="#9ca3af",
                margin_top="0.25rem"),
        bg="white",
        border_radius="0.75rem",
        border="1px solid #f3f4f6",
        box_shadow="0 1px 3px rgba(0,0,0,0.08)",
        padding="1.25rem",
    )


def _pending_task_card(task: dict) -> rx.Component:
    urgency_colors = {
        "urgent": {"bg": "#fef2f2", "border": "#fecaca", "dot": "#ef4444", "text": "#dc2626"},
        "warning": {"bg": "#fefce8", "border": "#fef08a", "dot": "#eab308", "text": "#ca8a04"},
        "done": {"bg": "#f9fafb", "border": "#f3f4f6", "dot": "#22c55e", "text": "#16a34a"},
    }
    c = urgency_colors.get(task["urgency"], urgency_colors["done"])
    return rx.hstack(
        rx.box(width="0.5rem", height="0.5rem", border_radius="9999px",
               bg=c["dot"], flex_shrink="0"),
        rx.vstack(
            rx.text(task["title"], font_size="0.875rem", font_weight="500",
                    color="#1f2937", truncate=True),
            rx.text(
                f"截止：{task['deadline']} · 剩余 {task['remaining']}"
                if task["deadline"]
                else task["status"],
                font_size="0.75rem", color=c["text"],
            ),
            spacing="0",
            align="start",
            flex="1",
            min_width="0",
        ),
        rx.link("提交", href="/assignments",
                font_size="0.75rem", color="#2563eb",
                _hover={"text_decoration": "underline"},
                flex_shrink="0", underline="none"),
        gap="0.75rem",
        padding="0.75rem",
        bg=c["bg"],
        border=f"1px solid {c['border']}",
        border_radius="0.5rem",
        align="center",
    )


def _announcement_item(ann: dict) -> rx.Component:
    dot_color = "#ef4444" if ann["unread"] else "#d1d5db"
    title_color = "#1f2937" if ann["unread"] else "#6b7280"
    return rx.hstack(
        rx.box(width="0.5rem", height="0.5rem", border_radius="9999px",
               bg=dot_color, margin_top="0.375rem", flex_shrink="0"),
        rx.vstack(
            rx.text(ann["title"], font_size="0.875rem", color=title_color),
            rx.text(f"{ann['date']} · {ann['author']}",
                    font_size="0.75rem", color="#9ca3af", margin_top="0.125rem"),
            spacing="0",
            align="start",
            gap="0",
        ),
        gap="0.75rem",
    )


def _radar_chart_placeholder() -> rx.Component:
    return rx.box(
        rx.html(
            '<svg viewBox="0 0 160 140" class="w-40 h-36">'
            '<polygon points="80,10 140,50 120,120 40,120 20,50" fill="none" '
            'stroke="#e5e7eb" stroke-width="1.5"/>'
            '<polygon points="80,30 120,58 108,104 52,104 40,58" fill="none" '
            'stroke="#e5e7eb" stroke-width="1"/>'
            '<polygon points="80,50 100,66 94,90 66,90 60,66" fill="none" '
            'stroke="#e5e7eb" stroke-width="1"/>'
            '<polygon points="80,22 128,56 111,112 49,112 32,54" fill="#3b82f6" '
            'fill-opacity="0.25" stroke="#3b82f6" stroke-width="2"/>'
            '<text x="75" y="8" font-size="9" fill="#6b7280">出勤</text>'
            '<text x="136" y="54" font-size="9" fill="#6b7280">考试</text>'
            '<text x="112" y="130" font-size="9" fill="#6b7280">代码</text>'
            '<text x="28" y="130" font-size="9" fill="#6b7280">PR</text>'
            '<text x="2" y="54" font-size="9" fill="#6b7280">其他</text>'
            '</svg>'
        ),
    )


def _bar_chart_placeholder() -> rx.Component:
    s = MockData.EXAM_HISTORY
    bars = []
    for item in s:
        bars.append(
            rx.vstack(
                rx.text(str(item["score"]), font_size="0.75rem", color="#6b7280"),
                rx.box(
                    width="100%", bg="#2563eb",
                    border_radius="0.25rem 0.25rem 0 0",
                    height=f"{item['height_pct']}%",
                ),
                rx.text(item["name"], font_size="0.75rem", color="#9ca3af"),
                align="center",
                gap="0.25rem",
                flex="1",
            )
        )
    return rx.hstack(
        *bars,
        align="end",
        gap="0.75rem",
        height="10rem",
        padding_x="0.5rem",
    )


def _line_chart_placeholder() -> rx.Component:
    points = MockData.TOTAL_SCORE_TREND
    n = len(points)
    if n < 2:
        return rx.box()
    w, h = 200, 120
    x_step = w / (n - 1)
    y_min, y_max = min(points), max(points)
    y_range = y_max - y_min or 1
    coords = []
    for i, p in enumerate(points):
        x = 10 + i * x_step
        y = h - ((p - y_min) / y_range) * (h - 20) - 10
        coords.append(f"{x:.0f},{y:.0f}")
    polyline_pts = " ".join(coords)
    last_val = points[-1]
    return rx.box(
        rx.html(
            f'<svg viewBox="0 0 {w+20} {h+10}" class="w-full h-full">'
            f'<polyline points="{polyline_pts}" fill="none" stroke="#3b82f6" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<text x="{w-60}" y="35" font-size="9" fill="#3b82f6">{last_val}</text>'
            '</svg>'
        ),
        height="10rem",
        bg="#eff6ff",
        border_radius="0.5rem",
        position="relative",
        overflow="hidden",
        display="flex",
        align_items="center",
        justify_content="center",
    )


def dashboard_page() -> rx.Component:
    s = MockData.STUDENT
    score_cards = rx.grid(
        *[_score_card(**card) for card in MockData.SCORE_CARDS],
        grid_template_columns="repeat(4, 1fr)",
        gap="1.25rem",
        margin_bottom="2rem",
    )

    charts = rx.grid(
        # Radar chart
        rx.box(
            rx.text("四维雷达图", font_size="0.875rem", font_weight="600",
                    color="#374151", margin_bottom="1rem"),
            rx.box(_radar_chart_placeholder(),
                   display="flex", justify_content="center"),
            rx.grid(
                *[
                    rx.hstack(
                        rx.box(width="0.625rem", height="0.625rem",
                               border_radius="9999px",
                               bg={"出勤": "#4ade80", "考试": "#c084fc",
                                   "代码": "#fb923c", "PR": "#60a5fa"}
                               .get(label.split()[0], "#60a5fa"),
                               display="inline-block"),
                        rx.text(label, font_size="0.75rem", color="#6b7280"),
                        align="center",
                        gap="0.375rem",
                    )
                    for label in ["出勤 18/20", "考试 24/30", "代码 32/40", "PR 13.5/10"]
                ],
                grid_template_columns="repeat(2, 1fr)",
                gap="0.5rem",
                margin_top="0.75rem",
            ),
            bg="white", border_radius="0.75rem",
            border="1px solid #f3f4f6",
            box_shadow="0 1px 3px rgba(0,0,0,0.08)",
            padding="1.25rem",
        ),
        # Bar chart
        rx.box(
            rx.text("历次考试得分", font_size="0.875rem", font_weight="600",
                    color="#374151", margin_bottom="1rem"),
            _bar_chart_placeholder(),
            bg="white", border_radius="0.75rem",
            border="1px solid #f3f4f6",
            box_shadow="0 1px 3px rgba(0,0,0,0.08)",
            padding="1.25rem",
        ),
        # Line chart
        rx.box(
            rx.text("总分变化曲线", font_size="0.875rem", font_weight="600",
                    color="#374151", margin_bottom="1rem"),
            _line_chart_placeholder(),
            rx.text("最近更新：2025-05-24", font_size="0.75rem", color="#9ca3af",
                    margin_top="0.5rem", text_align="right"),
            bg="white", border_radius="0.75rem",
            border="1px solid #f3f4f6",
            box_shadow="0 1px 3px rgba(0,0,0,0.08)",
            padding="1.25rem",
        ),
        grid_template_columns="repeat(3, 1fr)",
        gap="1.25rem",
        margin_bottom="2rem",
    )

    # Bottom row: pending tasks + announcements
    pending_items = [_pending_task_card(t) for t in MockData.PENDING_TASKS]
    announcement_items = [_announcement_item(a) for a in MockData.ANNOUNCEMENTS]

    bottom = rx.grid(
        rx.box(
            rx.hstack(
                rx.text("即将到期任务", font_size="0.875rem", font_weight="600",
                        color="#374151"),
                rx.link("查看全部", href="/assignments",
                        font_size="0.75rem", color="#2563eb",
                        _hover={"text_decoration": "underline"},
                        underline="none"),
                justify="between",
                align="center",
                margin_bottom="1rem",
            ),
            rx.vstack(*pending_items, gap="0.75rem"),
            bg="white", border_radius="0.75rem",
            border="1px solid #f3f4f6",
            box_shadow="0 1px 3px rgba(0,0,0,0.08)",
            padding="1.25rem",
        ),
        rx.box(
            rx.hstack(
                rx.text("课程公告", font_size="0.875rem", font_weight="600",
                        color="#374151"),
                rx.box(
                    rx.text("2 未读", font_size="0.75rem", color="#dc2626"),
                    bg="#fee2e2",
                    padding_x="0.5rem", padding_y="0.125rem",
                    border_radius="9999px",
                ),
                justify="between",
                align="center",
                margin_bottom="1rem",
            ),
            rx.vstack(*announcement_items, gap="0.75rem"),
            bg="white", border_radius="0.75rem",
            border="1px solid #f3f4f6",
            box_shadow="0 1px 3px rgba(0,0,0,0.08)",
            padding="1.25rem",
        ),
        grid_template_columns="repeat(2, 1fr)",
        gap="1.25rem",
    )

    content = rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("仪表盘", font_size="1.25rem", font_weight="bold",
                        color="#1f2937"),
                rx.text(f"欢迎回来，{s['name']} · 工程实践4 · 2025春",
                        font_size="0.875rem", color="#9ca3af",
                        margin_top="0.125rem"),
                align="start",
                spacing="0",
            ),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="2rem",
        ),
        score_cards,
        charts,
        bottom,
        spacing="0",
        width="100%",
    )

    return protected_page(content, current_route="/")
