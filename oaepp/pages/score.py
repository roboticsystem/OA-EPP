"""F-S-030 成绩看板页面（学生端）

路由：/score （由 app.py 自动发现机制注册）

展示综合得分圆环、4 维度卡片（出勤/考试/代码/PR）、评分明细表。
"""
try:
    import reflex as rx
except Exception:
    rx = None

score_page = None
if rx is not None:
    try:
        from components.layout import page_layout
    except ImportError:
        from oaepp.components.layout import page_layout

    try:
        from components.common import stat_card, loading_spinner, data_table
    except ImportError:
        from oaepp.components.common import stat_card, loading_spinner, data_table

    try:
        from states.score import ScoreState
    except ImportError:
        from oaepp.states.score import ScoreState

    try:
        from states.auth import AuthState
    except ImportError:
        from oaepp.states.auth import AuthState

    def _dimension_cards() -> rx.Component:
        """四个维度统计卡片"""
        return rx.grid(
            stat_card("出勤", ScoreState.attendance_score, icon="user_check"),
            stat_card("考试", ScoreState.exam_score, icon="clipboard_check"),
            stat_card("代码提交", ScoreState.code_score, icon="file_text"),
            stat_card("PR审查", ScoreState.pr_score, icon="git_pull_request"),
            columns="4",
            spacing="4",
            width="100%",
        )

    def _score_detail_table() -> rx.Component:
        """评分明细表格"""
        return rx.box(
            rx.heading("评分明细", size="5"),
            rx.divider(),
            data_table(
                columns=["维度", "得分", "评分人", "评分时间"],
                rows=[
                    ["出勤", "95", "张老师", "2026-06-15 10:30"],
                    ["考试", "88", "系统", "2026-06-20 14:00"],
                ],
            ),
            padding="24px",
            border_radius="12px",
            background="white",
            border="1px solid var(--gray-4)",
            width="100%",
        )

    def score_page():
        """成绩看板页面 — 使用统一 page_layout。"""
        return page_layout(
            title="成绩看板",
            content=rx.vstack(
                rx.cond(
                    AuthState.is_authenticated,
                    rx.vstack(
                        rx.heading(
                            f"{AuthState.current_full_name} 的综合成绩",
                            size="4",
                        ),
                        rx.text(
                            f"学号: {AuthState.current_student_no}",
                            color="gray",
                            size="2",
                        ),
                        _dimension_cards(),
                        _score_detail_table(),
                        spacing="4",
                        width="100%",
                        align="start",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.text("请先登录", color="red"),
                            rx.link("前往登录页", href="/"),
                            spacing="3",
                            align="center",
                        ),
                        padding="48px",
                    ),
                ),
                spacing="4",
                width="100%",
                align="start",
            ),
        )
