"""F-S-040 得分看板与可视化 — 学生端页面

路由: /dashboard（由 app.py 自动发现注册）
页面函数: dashboard_page()

需求对齐：
  - 雷达图展示出勤/考试/代码/PR 四维度得分
  - 柱状图展示各次考试历史趋势
  - 折线图展示全期总得分时间曲线
  - 展示任务完成率和即将到期任务
  - 支持按工程实践 1-4 筛选
"""

from __future__ import annotations

import reflex as rx

from oaepp.components.layout import page_layout
from oaepp.states.dashboard import (
    DashboardState,
    DIMENSION_COLORS,
    DIMENSION_LABELS,
)


# ═══════════════════════════════════════════════════════════════
#  课程筛选栏
# ═══════════════════════════════════════════════════════════════

def _filter_bar() -> rx.Component:
    """顶部筛选栏：课程选择。"""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text("课程筛选", font_size="xs", color="gray.500"),
                rx.select(
                    DashboardState.course_labels,
                    placeholder="选择课程...",
                    value=DashboardState.selected_course_label,
                    on_change=DashboardState.select_course_by_label,
                    size="2",
                    min_width="220px",
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.cond(
                DashboardState.error != "",
                rx.badge(
                    DashboardState.error,
                    color_scheme="red",
                    variant="soft",
                ),
            ),
            width="100%",
            spacing="4",
            align="end",
        ),
        width="100%",
        padding="16px 20px",
    )


# ═══════════════════════════════════════════════════════════════
#  四维度得分概览卡片
# ═══════════════════════════════════════════════════════════════

def _score_card(
    label: str,
    score: rx.Var,
    max_score: rx.Var,
    color: str,
) -> rx.Component:
    """单个得分卡片。"""
    return rx.card(
        rx.vstack(
            rx.text(label, font_size="xs", color="gray.400",
                    font_weight="medium", text_transform="uppercase"),
            rx.heading(score, size="6", color=f"var(--{color}-9)" if hasattr(rx, "color") else color),
            rx.text(
                rx.text.span("满分 "),
                rx.text.span(max_score),
                rx.text.span(" 分"),
                font_size="xs",
                color="gray.400",
            ),
            spacing="1",
            align="center",
        ),
        width="100%",
    )


def _summary_cards() -> rx.Component:
    """4 维度得分卡片 + 综合总分。"""
    return rx.hstack(
        rx.card(
            rx.vstack(
                rx.text("综合总分", font_size="xs", color="gray.400",
                        font_weight="medium"),
                rx.heading(
                    DashboardState.total_score,
                    size="7",
                    color="#3b82f6",
                ),
                rx.text("满分 100 分", font_size="xs", color="gray.400"),
                spacing="1",
                align="center",
            ),
            width="100%",
        ),
        _score_card("出勤得分", DashboardState.attendance_score,
                     DashboardState.attendance_max, "green"),
        _score_card("考试得分", DashboardState.exam_score,
                     DashboardState.exam_max, "purple"),
        _score_card("代码得分", DashboardState.code_score,
                     DashboardState.code_max, "orange"),
        _score_card("PR 得分", DashboardState.pr_score,
                     DashboardState.pr_max, "blue"),
        width="100%",
        spacing="4",
        wrap="wrap",
    )


# ═══════════════════════════════════════════════════════════════
#  雷达图（四维度对比）
# ═══════════════════════════════════════════════════════════════

def _radar_chart() -> rx.Component:
    """雷达图 — 展示出勤/考试/代码/PR 四维度得分对比。"""
    return rx.card(
        rx.vstack(
            rx.heading("📊 四维度雷达图", size="4"),
            rx.text(
                "展示出勤、考试、代码、PR 四个维度的得分对比",
                font_size="sm",
                color="gray.500",
            ),
            rx.cond(
                DashboardState.radar_data.length() > 0,
                rx.recharts.radar_chart(
                    rx.recharts.radar(
                        data_key="score",
                        stroke="#3b82f6",
                        fill="#3b82f6",
                        fill_opacity=0.25,
                    ),
                    rx.recharts.polar_grid(),
                    rx.recharts.polar_angle_axis(data_key="dimension"),
                    rx.recharts.polar_radius_axis(),
                    data=DashboardState.radar_data,
                    width="100%",
                    height=280,
                ),
                rx.center(
                    rx.text(
                        "暂无维度得分数据",
                        color="gray.400",
                        font_size="sm",
                    ),
                    height="280px",
                    width="100%",
                ),
            ),
            # 图例
            rx.hstack(
                *[
                    rx.hstack(
                        rx.box(
                            width="10px",
                            height="10px",
                            bg=color,
                            border_radius="2px",
                        ),
                        rx.text(label, font_size="xs", color="gray.500"),
                        spacing="1",
                    )
                    for label, color in [
                        ("出勤", "#22c55e"),
                        ("考试", "#a855f7"),
                        ("代码", "#f97316"),
                        ("PR", "#3b82f6"),
                    ]
                ],
                spacing="4",
                justify="center",
                width="100%",
            ),
            width="100%",
            padding="16px",
            spacing="3",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════
#  柱状图（历次考试得分趋势）
# ═══════════════════════════════════════════════════════════════

def _bar_chart() -> rx.Component:
    """柱状图 — 展示历次考试得分历史趋势。"""
    return rx.card(
        rx.vstack(
            rx.heading("📈 历次考试得分", size="4"),
            rx.text(
                "展示各次考试的成绩变化趋势",
                font_size="sm",
                color="gray.500",
            ),
            rx.cond(
                DashboardState.exam_history.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="score",
                        fill="#3b82f6",
                        radius=[4, 4, 0, 0],
                    ),
                    rx.recharts.x_axis(data_key="exam_title"),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.exam_history,
                    width="100%",
                    height=250,
                ),
                rx.center(
                    rx.text(
                        "暂无考试记录",
                        color="gray.400",
                        font_size="sm",
                    ),
                    height="250px",
                    width="100%",
                ),
            ),
            width="100%",
            padding="16px",
            spacing="3",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════
#  折线图（全期总得分趋势）
# ═══════════════════════════════════════════════════════════════

def _line_chart() -> rx.Component:
    """折线图 — 展示全期总得分时间曲线。"""
    return rx.card(
        rx.vstack(
            rx.heading("📉 总分变化曲线", size="4"),
            rx.text(
                "展示全期总得分的累计变化趋势",
                font_size="sm",
                color="gray.500",
            ),
            rx.cond(
                DashboardState.total_score_trend.length() > 0,
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="score",
                        stroke="#3b82f6",
                        stroke_width=2.5,
                        dot=True,
                        type_="monotone",
                    ),
                    rx.recharts.x_axis(data_key="date"),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.total_score_trend,
                    width="100%",
                    height=250,
                ),
                rx.center(
                    rx.text(
                        "暂无得分记录",
                        color="gray.400",
                        font_size="sm",
                    ),
                    height="250px",
                    width="100%",
                ),
            ),
            width="100%",
            padding="16px",
            spacing="3",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════
#  任务完成率 & 即将到期任务
# ═══════════════════════════════════════════════════════════════

def _completion_card() -> rx.Component:
    """任务完成率卡片。"""
    return rx.card(
        rx.vstack(
            rx.heading("✅ 任务完成率", size="4"),
            rx.hstack(
                rx.circular_progress(
                    value=DashboardState.completion_rate,
                    size="100px",
                    color="#22c55e",
                    track_color="var(--gray-4)",
                ),
                rx.vstack(
                    rx.heading(
                        rx.text.span(DashboardState.completion_rate),
                        rx.text.span("%"),
                        size="6",
                    ),
                    rx.text(
                        f"已完成 {DashboardState.completed_count} / "
                        f"{DashboardState.total_tasks} 个任务",
                        font_size="sm",
                        color="gray.500",
                    ),
                    rx.text(
                        rx.text.span(
                            DashboardState.total_tasks - DashboardState.completed_count
                        ),
                        rx.text.span(" 个待完成"),
                        font_size="xs",
                        color="orange.500",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="6",
                align="center",
            ),
            width="100%",
            padding="16px",
            spacing="3",
        ),
        width="100%",
    )


def _deadline_badge(has_submitted: bool, days_left: str) -> rx.Component:
    """截止状态标签。"""
    if has_submitted:
        return rx.badge("已提交", color_scheme="green", variant="soft", size="1")
    if "已截止" in days_left:
        return rx.badge("已截止", color_scheme="red", variant="soft", size="1")
    # 判断紧急程度
    try:
        days = int(days_left.replace("剩余 ", "").replace(" 天", ""))
        if days <= 2:
            return rx.badge(days_left, color_scheme="red", variant="soft", size="1")
        elif days <= 5:
            return rx.badge(days_left, color_scheme="orange", variant="soft", size="1")
    except (ValueError, AttributeError):
        pass
    return rx.badge(days_left, color_scheme="blue", variant="soft", size="1")


def _task_row(task: dict) -> rx.Component:
    """单个即将到期任务行。"""
    has_submitted = task.get("has_submitted", False)
    days_left = task.get("days_left", "")
    return rx.hstack(
        rx.hstack(
            rx.icon(
                "check_circle" if has_submitted else "circle",
                size=16,
                color="#22c55e" if has_submitted else "var(--gray-7)",
            ),
            rx.vstack(
                rx.text(
                    task.get("title", ""),
                    font_size="sm",
                    font_weight="medium",
                    color="var(--gray-12)",
                ),
                rx.text(
                    f"截止：{task.get('deadline', '')}",
                    font_size="xs",
                    color="gray.500",
                ),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
            flex="1",
        ),
        _deadline_badge(has_submitted, days_left),
        width="100%",
        padding_y="8px",
        border_bottom="1px solid var(--gray-4)",
    )


def _upcoming_deadlines_card() -> rx.Component:
    """即将到期任务列表。"""
    return rx.card(
        rx.vstack(
            rx.heading("⏰ 即将到期任务", size="4"),
            rx.cond(
                DashboardState.upcoming_deadlines.length() > 0,
                rx.vstack(
                    rx.foreach(
                        DashboardState.upcoming_deadlines,
                        _task_row,
                    ),
                    width="100%",
                ),
                rx.center(
                    rx.text(
                        "暂无即将到期任务",
                        color="gray.400",
                        font_size="sm",
                    ),
                    padding_y="40px",
                    width="100%",
                ),
            ),
            width="100%",
            padding="16px",
            spacing="3",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════
#  主页面
# ═══════════════════════════════════════════════════════════════

def dashboard_page() -> rx.Component:
    """学生端 — 得分看板（雷达图 + 柱状图 + 折线图 + 任务完成率）。"""
    content = rx.vstack(
        # 课程筛选
        _filter_bar(),
        # 得分概览卡片
        _summary_cards(),
        # 图表行：雷达图 | 柱状图
        rx.hstack(
            _radar_chart(),
            _bar_chart(),
            width="100%",
            spacing="4",
            wrap="wrap",
        ),
        # 折线图
        _line_chart(),
        # 任务完成率 & 即将到期
        rx.hstack(
            _completion_card(),
            _upcoming_deadlines_card(),
            width="100%",
            spacing="4",
            wrap="wrap",
            align_items="start",
        ),
        rx.toast.provider(),
        width="100%",
        max_width="1200px",
        margin="0 auto",
        spacing="4",
        on_mount=DashboardState.on_mount,
    )
    return page_layout(title="📊 得分看板", content=content)
