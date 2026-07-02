"""F-T-008 教师成绩导出页面

对应 State : oaepp.states.teacher_grade_export.TeacherGradeExportState
路由       : /teacher_grade_export （由 app.py 自动发现机制注册）
"""
try:
    import reflex as rx
except Exception:
    rx = None

teacher_grade_export_page = None
if rx is not None:
    try:
        from oaepp.states.teacher_grade_export import TeacherGradeExportState
    except ImportError:
        try:
            from states.teacher_grade_export import TeacherGradeExportState
        except ImportError:
            TeacherGradeExportState = None

    def _export_tab() -> rx.Component:
        """成绩单导出 Tab"""
        return rx.box(
            rx.vstack(
                rx.heading("成绩单导出", size="5"),
                rx.text("按班级/课程/学期筛选导出全班成绩单（.xlsx），导出前可预览并修正个别单元格。", color="gray", size="2"),
                rx.divider(),
                rx.button(
                    rx.cond(
                        TeacherGradeExportState.is_exporting,
                        rx.text("加载中..."),
                        rx.hstack(rx.icon(tag="download", size=16), rx.text("预览数据"), spacing="2"),
                    ),
                    on_click=TeacherGradeExportState.preview,
                    disabled=TeacherGradeExportState.is_exporting,
                    color_scheme="blue",
                    size="3",
                ),
                rx.cond(
                    TeacherGradeExportState.preview_rows.length() > 0,
                    rx.vstack(
                        rx.text(f"共 {TeacherGradeExportState.preview_rows.length()} 条记录", font_size="0.9rem"),
                        rx.button(
                            "导出 Excel",
                            on_click=TeacherGradeExportState.export_excel,
                            color_scheme="green",
                            size="3",
                        ),
                    ),
                ),
                padding="1em",
            ),
            width="100%",
        )

    def teacher_grade_export_page() -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.heading("教师成绩管理", size="6"),
                _export_tab(),
                spacing="4",
                width="100%",
            ),
            padding="2em",
            width="100%",
        )
