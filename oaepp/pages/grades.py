"""F-S-031/F-S-032 成绩与反馈页面（学生端）

路由：/grades（由 app.py 自动发现机制注册）

功能：
- 顶部四维度得分卡片（出勤/考试/代码/PR）
- 评分详情表格：展示每次评阅的任务、得分、批改人、状态
- 评语卡片：展示教师评语、扣分项标签、改进建议条目
- 二次提交入口：允许重新提交时显示"前往重新提交"链接
"""
import reflex as rx

from oaepp.states.score import ScoreState
from oaepp.states.feedback import FeedbackState
from oaepp.components.layout import page_layout


# ── 得分卡片 ──
def _stat_card(
    label: str, score_var, sub_text: str, color: str,
) -> rx.Component:
    """单一维度得分卡片"""
    return rx.box(
        rx.text(label, size="1", color="gray", weight="medium"),
        rx.heading(score_var, size="6", color=color, margin_top="4px"),
        rx.text(sub_text, size="1", color="gray", margin_top="2px"),
        padding="16px 20px",
        bg="white",
        border_radius="8px",
        border="1px solid var(--gray-4)",
        flex="1",
    )


# ── 扣分项标签 ──
def _deduction_tag(item: dict) -> rx.Component:
    return rx.box(
        f"扣分：-{item['points']} · {item['reason']}",
        font_size="xs",
        bg="var(--red-2)",
        color="var(--red-9)",
        padding="2px 8px",
        border_radius="md",
    )


# ── 改进建议条目 ──
def _suggestion_item(text: str) -> rx.Component:
    return rx.hstack(
        rx.text("•", color="var(--blue-9)", font_weight="bold"),
        rx.text(text, size="2", color="gray"),
        spacing="2",
        align="start",
    )


# ── 评语卡片 ──
def _feedback_card(fb: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.avatar(size="sm", name=fb.get("grader_name", "教师")),
                rx.vstack(
                    rx.text(
                        f"{fb.get('assignment_title', '')}评语 · {fb.get('grader_name', '教师')}（教师）",
                        size="2", weight="semibold", color="gray",
                    ),
                    rx.text(
                        f"{fb.get('graded_at', '')} 批改",
                        size="1", color="gray",
                    ),
                    spacing="0",
                ),
                spacing="3",
            ),
            rx.spacer(),
            rx.text(
                f"{fb.get('total_score', 0):g}/10",
                size="4", weight="bold", color="var(--green-9)",
            ),
        ),
        rx.text(
            fb.get("comment", ""),
            size="2", color="gray",
            line_height="relaxed", margin_top="12px",
        ),
        rx.hstack(
            *[_deduction_tag(item) for item in (fb.get("deduction_items") or [])],
            spacing="2", flex_wrap="wrap", margin_top="12px",
        ),
        rx.vstack(
            *[_suggestion_item(s) for s in (fb.get("suggestions") or [])],
            spacing="2", margin_top="12px",
        ),
        rx.cond(
            fb.get("allow_resubmit", False),
            rx.box(
                rx.divider(margin_top="12px"),
                rx.text(
                    "此任务允许二次提交，可基于以上反馈修改后重新提交",
                    size="1", color="gray", margin_top="8px",
                ),
                rx.link(
                    "前往重新提交 →",
                    href="/assignments", size="1", color="var(--blue-9)",
                    margin_top="4px",
                ),
            ),
            rx.box(),
        ),
        bg="var(--blue-2)",
        border="1px solid var(--blue-4)",
        border_radius="xl",
        padding="20px",
        margin_top="12px",
    )


# ── 评分详情行 ──
def _detail_row(detail: dict) -> rx.Component:
    """单行评分详情 — 所有展示字段已在 State 中预计算"""
    return rx.table.row(
        rx.table.cell(rx.text(detail["assignment_title"], weight="medium", color="gray")),
        rx.table.cell(rx.text(detail["score_text"], weight="bold", color=detail["score_color"])),
        rx.table.cell(rx.text(detail["grader_name"], size="1", color="gray")),
        rx.table.cell(rx.text(detail["graded_at"], size="1", color="gray")),
        rx.table.cell(
            rx.box(
                detail["status_text"], font_size="xs",
                bg=detail["status_bg"], color=detail["status_fg"],
                padding="2px 8px", border_radius="full",
            )
        ),
        rx.table.cell(
            rx.cond(
                detail["has_score"],
                rx.text("查看评语", size="1", color="var(--blue-9)", cursor="pointer"),
                rx.text("—", size="1", color="gray"),
            ),
        ),
    )


# ── 主页面 ──
def grades_page() -> rx.Component:
    """成绩与反馈页面 — 使用全局 page_layout"""
    return page_layout(
        title="成绩与反馈",
        content=rx.vstack(
            # 标题行
            rx.hstack(
                rx.vstack(
                    rx.heading("成绩与反馈", size="6", color="gray"),
                    rx.text(ScoreState.title_text, size="2", color="gray"),
                    spacing="0",
                ),
                rx.spacer(),
                rx.button(
                    "下载成绩单 Excel",
                    bg="var(--green-9)", color="white",
                    size="2", border_radius="lg",
                ),
                width="100%",
                margin_bottom="24px",
            ),

            # 四维度得分卡片
            rx.hstack(
                _stat_card("出勤得分", ScoreState.attendance_score,
                           "出勤得分", "var(--green-9)"),
                _stat_card("考试得分", ScoreState.exam_score,
                           "考试得分", "var(--purple-9)"),
                _stat_card("代码提交", ScoreState.code_score,
                           "代码提交", "var(--orange-9)"),
                _stat_card("PR 贡献", ScoreState.pr_score,
                           "PR 贡献", "var(--blue-9)"),
                spacing="4",
                margin_bottom="24px",
            ),

            # 评阅详情表格
            rx.box(
                rx.hstack(
                    rx.text("代码评阅详情", size="2", weight="medium",
                            color="var(--blue-9)"),
                    rx.text("考试成绩", size="2", color="gray", cursor="pointer"),
                    rx.text("出勤记录", size="2", color="gray", cursor="pointer"),
                    rx.text("时间线", size="2", color="gray", cursor="pointer"),
                    padding="16px 20px 0 20px",
                    border_bottom="1px solid var(--gray-4)",
                    spacing="6",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("任务"),
                                rx.table.column_header_cell("得分"),
                                rx.table.column_header_cell("批改人"),
                                rx.table.column_header_cell("批改时间"),
                                rx.table.column_header_cell("状态"),
                                rx.table.column_header_cell(""),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(ScoreState.score_breakdown, _detail_row),
                        ),
                        width="100%",
                    ),
                    padding="20px",
                ),
                bg="white",
                border_radius="xl",
                border="1px solid var(--gray-4)",
                box_shadow="0 2px 6px rgba(0,0,0,0.04)",
                margin_bottom="24px",
            ),

            # 评语详情（当选中时展示）
            rx.cond(
                FeedbackState.current_feedback is not None,
                _feedback_card(FeedbackState.current_feedback),
            ),

            spacing="4",
            width="100%",
        ),
    )
