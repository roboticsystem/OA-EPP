"""F-S-030 成绩查询页面 — Reflex 组件

学生登录后可实时查看综合得分及各维度分项，展示评分人和评分时间。
"""
try:
    import reflex as rx
except Exception:
    rx = None

score_page = None
if rx is not None:

    def score_page():
        return rx.center(
            rx.box(
                rx.vstack(
                    rx.heading("成绩查询", size="6"),
                    rx.text("研究生课程《机器人系统》"),
                    rx.divider(),
                    rx.text("登录后可查看个人综合得分", color="gray"),
                    rx.vstack(
                        rx.text("学号", weight="medium"),
                        rx.input(placeholder="请输入学号", name="student_no", width="100%"),
                        rx.text("密码", weight="medium"),
                        rx.input(type_="password", placeholder="请输入密码", name="password", width="100%"),
                        rx.button("查询成绩", width="100%"),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    rx.divider(),
                    rx.text("评分维度：出勤 / 考试 / 代码提交 / PR审查", font_size="sm"),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                max_width="460px",
                width="100%",
                padding="28px",
                border_radius="12px",
                box_shadow="0 10px 30px rgba(0,0,0,0.08)",
                background="white",
            ),
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #f0f4f8 0%, #e2e8f0 100%)",
            padding="20px",
        )
