"""F-T-012 成绩权重配置页面

对应 State : oaepp.states.teacher_grade_weight.GradeWeightState
路由       : /teacher_grade_weight （由 app.py 自动发现机制注册）
"""
try:
    import reflex as rx
except Exception:
    rx = None

teacher_grade_weight_page = None
if rx is not None:
    try:
        from oaepp.states.teacher_grade_weight import GradeWeightState
    except ImportError:
        try:
            from states.teacher_grade_weight import GradeWeightState
        except ImportError:
            GradeWeightState = None

    def _weight_editor() -> rx.Component:
        """权重编辑器组件"""
        return rx.box(
            rx.vstack(
                rx.heading("得分权重配置", size="5"),
                rx.text("调整各维度占总评的百分比，四项权重之和必须等于 100%", color="gray", size="2"),
                rx.divider(),
                rx.hstack(
                    rx.vstack(
                        rx.text(f"出勤：{GradeWeightState.attendance_weight}%", font_weight="bold"),
                        rx.slider(on_change=GradeWeightState.set_attendance_weight, min_=0, max_=100, default_value=15),
                        rx.text(f"考试：{GradeWeightState.exam_weight}%", font_weight="bold"),
                        rx.slider(on_change=GradeWeightState.set_exam_weight, min_=0, max_=100, default_value=30),
                        rx.text(f"代码：{GradeWeightState.code_weight}%", font_weight="bold"),
                        rx.slider(on_change=GradeWeightState.set_code_weight, min_=0, max_=100, default_value=35),
                        rx.text(f"PR：{GradeWeightState.pr_weight}%", font_weight="bold"),
                        rx.slider(on_change=GradeWeightState.set_pr_weight, min_=0, max_=100, default_value=20),
                        spacing="3",
                    ),
                    rx.box(
                        rx.text(GradeWeightState.validation_message, font_size="0.85rem"),
                        rx.button("保存权重", on_click=GradeWeightState.save_weights, color_scheme="blue"),
                        rx.button("重置默认", on_click=GradeWeightState.reset_to_default, variant="outline"),
                        spacing="3",
                    ),
                    spacing="6",
                ),
                padding="1em",
            ),
            width="100%",
        )

    def teacher_grade_weight_page() -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.heading("成绩权重管理", size="6"),
                _weight_editor(),
                spacing="4",
                width="100%",
            ),
            padding="2em",
            width="100%",
        )
