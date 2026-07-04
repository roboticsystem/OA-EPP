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
        from states.score import ScoreState
    except ImportError:
        from oaepp.states.score import ScoreState

    try:
        from states.auth import AuthState
    except ImportError:
        from oaepp.states.auth import AuthState

    def _score_stat_card(label: str, value, icon: str) -> rx.Component:
        return rx.card(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=24, color="blue"),
                    padding="12px",
                    background_color="var(--blue-3)",
                    border_radius="8px",
                ),
                rx.vstack(
                    rx.text(label, size="2", color="gray"),
                    rx.heading(value, size="5"),
                    spacing="1",
                    align="start",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            padding="16px",
            width="100%",
        )

    def _dimension_cards() -> rx.Component:
        return rx.grid(
            _score_stat_card("出勤", ScoreState.attendance_score, "user_check"),
            _score_stat_card("考试", ScoreState.exam_score, "clipboard_check"),
            _score_stat_card("代码提交", ScoreState.code_score, "file_text"),
            _score_stat_card("PR审查", ScoreState.pr_score, "git_pull_request"),
            columns="4",
            spacing="4",
            width="100%",
        )

    def _score_detail_table() -> rx.Component:
        return rx.box(
            rx.heading("评分明细", size="5"),
            rx.divider(),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("维度"),
                        rx.table.column_header_cell("得分"),
                    ),
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell("出勤"),
                        rx.table.cell(rx.heading(ScoreState.attendance_score, size="3")),
                    ),
                    rx.table.row(
                        rx.table.cell("考试"),
                        rx.table.cell(rx.heading(ScoreState.exam_score, size="3")),
                    ),
                    rx.table.row(
                        rx.table.cell("代码提交"),
                        rx.table.cell(rx.heading(ScoreState.code_score, size="3")),
                    ),
                    rx.table.row(
                        rx.table.cell("PR审查"),
                        rx.table.cell(rx.heading(ScoreState.pr_score, size="3")),
                    ),
                    rx.table.row(
                        rx.table.cell("总分"),
                        rx.table.cell(rx.heading(ScoreState.total_score, size="3", color="blue")),
                    ),
                ),
                width="100%",
            ),
            padding="24px",
            border_radius="12px",
            background="white",
            border="1px solid var(--gray-4)",
            width="100%",
        )

    def score_page():
        content = rx.vstack(
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
                    rx.heading(
                        f"总分: {ScoreState.total_score}",
                        size="3",
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
            width="100%", max_width="1200px", margin="0 auto", spacing="4",
        )
        return page_layout(title="成绩看板", content=content)

    page_on_load = ScoreState.load_scores
