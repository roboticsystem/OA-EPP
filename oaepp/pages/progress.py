"""F-T-013 进度看板 — 教师端页面

路由: /progress（由 app.py 自动发现注册）
页面函数: progress_page()

需求对齐：
  - 热力图展示「学生（行）× 任务（列）」完成状态矩阵
  - 柱状图展示各任务完成率趋势
  - 完成率最低前 N 名置顶高亮
  - 点击单元格查看提交详情
  - 数据每 10 秒自动刷新
  - 按课程、学期筛选视图范围
"""

from __future__ import annotations

import reflex as rx

from oaepp.components.layout import page_layout
from oaepp.states.progress import ProgressState, STATUS_COLORS, STATUS_LABELS


# ═══════════════════════════════════════════════════════════════
#  颜色图例
# ═══════════════════════════════════════════════════════════════

def _legend() -> rx.Component:
    items = [
        ("submitted", "已提交"),
        ("late", "迟交"),
        ("not_submitted", "未提交"),
        ("not_published", "未发布"),
    ]
    return rx.hstack(
        *[
            rx.hstack(
                rx.box(
                    width="12px",
                    height="12px",
                    bg=STATUS_COLORS[code],
                    border_radius="3px",
                ),
                rx.text(label, font_size="xs", color="gray.500"),
                spacing="1",
            )
            for code, label in items
        ],
        spacing="3",
        wrap="nowrap",
    )


# ═══════════════════════════════════════════════════════════════
#  统计概览卡片
# ═══════════════════════════════════════════════════════════════

def _summary_cards() -> rx.Component:
    """4 张概览卡片。"""
    return rx.hstack(
        rx.card(
            rx.vstack(
                rx.text("学生人数", font_size="xs", color="gray.500"),
                rx.heading(ProgressState.summary_total_students, size="5"),
                spacing="1",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.text("任务数量", font_size="xs", color="gray.500"),
                rx.heading(ProgressState.summary_total_assignments, size="5"),
                spacing="1",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.text("提交总数", font_size="xs", color="gray.500"),
                rx.heading(ProgressState.summary_total_submissions, size="5"),
                spacing="1",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.text("整体完成率", font_size="xs", color="gray.500"),
                rx.heading(
                    rx.text.span(ProgressState.summary_overall_rate),
                    rx.text.span("%"),
                    size="5",
                ),
                spacing="1",
                align="center",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
        wrap="wrap",
    )


# ═══════════════════════════════════════════════════════════════
#  筛选栏
# ═══════════════════════════════════════════════════════════════

def _filter_bar() -> rx.Component:
    """顶部筛选栏：课程选择 + 学期筛选 + 前 N 名配置 + 刷新。"""
    return rx.card(
        rx.hstack(
            # 课程下拉
            rx.vstack(
                rx.text("课程", font_size="xs", color="gray.500"),
                rx.select(
                    ProgressState.course_labels,
                    placeholder="选择课程...",
                    value=ProgressState.selected_course_label,
                    on_change=ProgressState.select_course_by_label,
                    size="2",
                    min_width="200px",
                ),
                spacing="1",
                align="start",
            ),
            # 学期筛选
            rx.vstack(
                rx.text("学期", font_size="xs", color="gray.500"),
                rx.select(
                    ["全部", "2026-春", "2025-秋", "2025-春", "2024-秋"],
                    value=ProgressState.selected_term,
                    on_change=ProgressState.set_term,
                    size="2",
                    min_width="120px",
                ),
                spacing="1",
                align="start",
            ),
            rx.divider(orientation="vertical", height="48px"),
            # 置底 N 配置
            rx.vstack(
                rx.text("末位置顶数", font_size="xs", color="gray.500"),
                rx.hstack(
                    rx.input(
                        value=ProgressState.bottom_n.to(str),
                        on_change=ProgressState.set_bottom_n_str,
                        type="number",
                        min=1,
                        max=20,
                        size="2",
                        width="60px",
                        text_align="center",
                    ),
                    rx.text("名", font_size="sm", color="gray.500"),
                    spacing="1",
                    align="center",
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # 刷新按钮
            rx.vstack(
                rx.text("", font_size="xs"),
                rx.hstack(
                    rx.button(
                        rx.icon("refresh-cw", size=14),
                        "刷新",
                        size="2",
                        color_scheme="blue",
                        variant="outline",
                        on_click=ProgressState.manual_refresh,
                    ),
                    rx.cond(
                        ProgressState.last_refresh != "",
                        rx.text(
                            f"更新于 {ProgressState.last_refresh}",
                            font_size="xs",
                            color="gray.400",
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                align="end",
            ),
            width="100%",
            spacing="4",
            align="end",
            wrap="wrap",
        ),
        width="100%",
        padding="16px 20px",
    )


# ═══════════════════════════════════════════════════════════════
#  热力图
# ═══════════════════════════════════════════════════════════════

def _heatmap_column_headers() -> rx.Component:
    """热力图上方竖排任务标题 + 图例。"""
    return rx.hstack(
        rx.box(width="130px", flex_shrink="0"),
        rx.box(width="70px", flex_shrink="0"),
        rx.text("│", color="gray.300", font_size="12px"),
        rx.foreach(
            ProgressState.assignments,
            lambda a: rx.tooltip(
                rx.box(
                    rx.text(
                        a["title"][:8],
                        font_size="10px",
                        color="#6b7280",
                        text_align="center",
                    ),
                    width="42px",
                    min_width="42px",
                    height="50px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border_bottom="1px solid #e5e7eb",
                    flex_shrink="0",
                ),
                content=a["title"],
            ),
        ),
        rx.spacer(),
        _legend(),
        spacing="0",
        align="center",
        width="100%",
        padding_bottom="4px",
        border_bottom="2px solid var(--gray-5)",
    )


def _heatmap_cell(cell: dict) -> rx.Component:
    """单个任务状态格 — 顶层函数。"""
    c_sid = cell.get("student_id", 0)
    c_aid = cell.get("assignment_id", 0)
    return rx.tooltip(
        rx.box(
            rx.text(
                cell.get("emoji", "·"),
                font_size="14px",
                text_align="center",
                width="100%",
                line_height="34px",
                color="#ffffff",
            ),
            width="42px",
            min_width="42px",
            height="34px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
            bg=cell.get("color", "#d1d5db"),
            border_right="1px solid rgba(255,255,255,0.3)",
            _hover={"opacity": "0.8", "outline": "2px solid var(--blue-5)"},
            on_click=lambda: ProgressState.show_cell_detail(c_sid, c_aid),
        ),
        content=cell.get("tooltip", ""),
        side="top",
    )


def _heatmap_row(row: dict) -> rx.Component:
    """热力图一行：学生姓名 + 完成率 + N 个任务状态格。"""
    s = row.get("student", {})
    rate = s.get("completion_rate", 0)
    is_hl = row.get("is_highlight", False)
    hl_bg = "#fef2f2" if is_hl else "white"
    name_weight = "bold" if is_hl else "medium"
    rate_color = "#16a34a" if rate >= 80 else ("#ca8a04" if rate >= 50 else "#dc2626")

    return rx.hstack(
        rx.box(
            rx.text(
                s.get("full_name", ""),
                font_size="12px",
                font_weight=name_weight,
                white_space="nowrap",
                overflow="hidden",
                text_overflow="ellipsis",
                color="#1f2937",
            ),
            width="130px",
            min_width="130px",
            height="34px",
            display="flex",
            align_items="center",
            padding_left="8px",
            bg=hl_bg,
            flex_shrink="0",
        ),
        rx.box(
            rx.text(
                f"{rate}%",
                font_size="11px",
                font_weight="bold",
                color=rate_color,
            ),
            width="70px",
            min_width="70px",
            height="34px",
            display="flex",
            align_items="center",
            justify_content="center",
            bg=hl_bg,
            flex_shrink="0",
        ),
        rx.text("│", color="gray.200", font_size="11px"),
        rx.foreach(row.get("cells", []), _heatmap_cell),
        spacing="0",
        align="center",
        width="100%",
        flex_shrink="0",
        bg=hl_bg,
        border_bottom="1px solid var(--gray-3)",
    )


# ═══════════════════════════════════════════════════════════════
#  柱状图
# ═══════════════════════════════════════════════════════════════

def _bar_row(item: dict) -> rx.Component:
    rate = item.get("rate", 0)
    label = item.get("label", "")
    submitted = item.get("submitted", 0)
    total = item.get("total", 0)
    late_count = item.get("late", 0)
    bar_color = "#16a34a" if rate >= 80 else ("#ca8a04" if rate >= 50 else "#dc2626")
    bar_width = f"{max(float(rate), 2)}%"

    return rx.hstack(
        rx.box(
            rx.text(label, font_size="12px", white_space="nowrap", overflow="hidden",
                    text_overflow="ellipsis", max_width="160px"),
            width="170px", min_width="170px",
        ),
        rx.box(
            rx.box(
                height="22px", width=bar_width, bg=bar_color,
                border_radius="4px", transition="width 0.4s ease",
            ),
            width="100%", bg="var(--gray-3)", border_radius="4px", height="22px",
        ),
        rx.box(
            rx.hstack(
                rx.text(f"{rate}%", font_size="13px", font_weight="bold", color=bar_color),
                rx.text(f"({submitted}/{total})", font_size="11px", color="gray.400"),
                rx.text(f"含{late_count}迟交", font_size="10px", color="orange.500")
                if late_count > 0 else rx.fragment(),
                spacing="1",
            ),
            width="150px", min_width="150px", padding_left="8px",
        ),
        width="100%", spacing="3", align="center", padding_y="7px",
    )


def _bar_chart() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("📈 各任务完成率趋势", size="4"),
            rx.text("纵轴为完成比例（%），横轴为任务名称，按发布时间排序",
                    font_size="sm", color="gray.500"),
            rx.vstack(
                rx.foreach(ProgressState.completion_trend, _bar_row),
                width="100%",
            ),
            width="100%", padding="16px", spacing="3",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════
#  提交详情弹窗
# ═══════════════════════════════════════════════════════════════

def _detail_section(title: str, fields: list) -> rx.Component:
    """详情弹窗中一个信息区块。"""
    items = []
    for label, val in fields:
        items.append(
            rx.vstack(
                rx.text(label, font_size="xs", color="gray.400"),
                val if isinstance(val, rx.Component) else rx.text(str(val), font_size="sm"),
                spacing="0", align="start", flex="1",
            )
        )
    return rx.box(
        rx.vstack(
            rx.text(title, font_size="sm", font_weight="bold", color="gray.600"),
            rx.hstack(*items, width="100%", spacing="3", wrap="wrap"),
            spacing="2", align="start", width="100%",
        ),
        padding="12px", border_radius="6px", bg="var(--gray-1)", width="100%",
    )


def _detail_dialog() -> rx.Component:
    d = ProgressState.detail_data
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("📋 提交详情"),
            rx.alert_dialog.description(
                rx.vstack(
                    _detail_section("学生", [
                        ("姓名", d["student_name"]),
                        ("学号", d["student_no"]),
                        ("班级", d["class_name"]),
                    ]),
                    _detail_section("任务", [
                        ("任务名称", d["assignment_title"]),
                        ("截止时间", d["assignment_deadline"]),
                    ]),
                    _detail_section("提交信息", [
                        ("完成状态",
                         rx.badge(
                             d["status_label"],
                             color_scheme=rx.cond(
                                 d["is_late"], "orange",
                                 rx.cond(d["submission_id"] != None, "green", "red"),
                             ),
                             size="2",
                         )),
                        ("提交时间", d["submitted_at"]),
                        ("版本号", d["version_no"]),
                        ("批改状态", d["grading_status"]),
                    ]),
                    spacing="3", align="start", width="100%",
                ),
            ),
            rx.alert_dialog.action(
                rx.button("关闭", on_click=ProgressState.close_detail),
            ),
            max_width="520px",
        ),
        open=ProgressState.detail_open,
    )


# ═══════════════════════════════════════════════════════════════
#  客户端脚本（自动刷新）
# ═══════════════════════════════════════════════════════════════

def _auto_refresh_script() -> rx.Component:
    """注入 JS：每 10 秒自动点击刷新按钮。"""
    return rx.script("""
setInterval(function() {
    var btns = document.querySelectorAll('[data-refresh="progress"]');
    for (var i = 0; i < btns.length; i++) {
        try { btns[i].click(); } catch(e) {}
    }
}, 10000);
""")


# ═══════════════════════════════════════════════════════════════
#  主页面
# ═══════════════════════════════════════════════════════════════

def progress_page() -> rx.Component:
    """教师端 — 进度看板（热力图 + 柱状图）。"""
    content = rx.vstack(
        _filter_bar(),
        _summary_cards(),
        # 热力图
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("📊 学生 × 任务 完成状态矩阵", size="4"),
                    rx.spacer(),
                    rx.cond(
                        ProgressState.bottom_n > 0,
                        rx.badge(f"末 {ProgressState.bottom_n} 名高亮",
                                 color_scheme="red", variant="soft"),
                    ),
                    width="100%", align="center",
                ),
                rx.text("颜色：绿=已提交 黄=迟交 红=未提交 灰=未发布 · 点击单元格查看详情",
                        font_size="xs", color="gray.500"),
                rx.box(_heatmap_column_headers(), overflow_x="auto", width="100%"),
                rx.box(
                    rx.foreach(ProgressState.heatmap_rows, _heatmap_row),
                    overflow_y="auto", max_height="480px", width="100%",
                ),
                width="100%", padding="16px", spacing="2",
            ),
            width="100%",
        ),
        # 柱状图
        _bar_chart(),
        # 弹窗
        _detail_dialog(),
        # 脚本
        _auto_refresh_script(),
        rx.toast.provider(),
        width="100%", max_width="1200px", margin="0 auto", spacing="4",
        on_mount=ProgressState.on_mount,
    )
    return page_layout(title="📊 进度看板", content=content)
