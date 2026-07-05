"""F-S-032 成绩与反馈页面（学生端）

对应原型：prototype/grades.html
路由：/grades （由 app.py 自动发现机制注册）

当前承载功能：F-S-032 "下载成绩单 Excel"。
其它成绩可视化（F-S-030 / F-S-031）由其他需求扩展。
"""
try:
    import reflex as rx
except Exception:
    rx = None

grades_page = None
if rx is not None:
    try:
        from components.layout import page_layout
    except ImportError:
        from oaepp.components.layout import page_layout

    try:
        from states.grade_export import GradeExportState
    except ImportError:
        from oaepp.states.grade_export import GradeExportState

    def _export_card() -> rx.Component:
        """成绩单导出卡片 — 单一职责：触发 .xlsx 下载。"""
        return rx.box(
            rx.vstack(
                rx.heading("成绩单导出", size="5"),
                rx.text(
                    "下载本人全期成绩单（.xlsx），包含学号、姓名、各任务得分、"
                    "总评成绩、提交时间、批改时间。仅含本人数据。",
                    color="gray",
                    size="2",
                ),
                rx.divider(),
                rx.button(
                    rx.cond(
                        GradeExportState.is_exporting,
                        rx.text("导出中..."),
                        rx.hstack(
                            rx.icon(tag="download", size=16),
                            rx.text("下载成绩单 Excel"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    on_click=GradeExportState.export_my_grades,
                    disabled=GradeExportState.is_exporting,
                    color_scheme="green",
                    size="3",
                ),
                rx.cond(
                    GradeExportState.export_error != "",
                    rx.box(
                        rx.text(GradeExportState.export_error, color="red", size="2"),
                        padding="8px 12px",
                        background="#fef2f2",
                        border_radius="8px",
                        border="1px solid #fecaca",
                    ),
                    rx.box(),
                ),
                rx.cond(
                    GradeExportState.export_filename != "",
                    rx.text(
                        f"上次导出：{GradeExportState.export_filename}",
                        color="gray",
                        size="1",
                    ),
                    rx.box(),
                ),
                spacing="3",
                align="stretch",
                width="100%",
            ),
            padding="24px",
            border_radius="12px",
            background="white",
            border="1px solid var(--gray-4)",
            box_shadow="0 2px 6px rgba(0,0,0,0.04)",
            width="100%",
            max_width="720px",
        )

    def grades_page():
        """成绩与反馈页面 — 使用统一 page_layout 提供侧栏+顶栏布局。"""
        return page_layout(
            title="成绩与反馈",
            content=rx.vstack(
                _export_card(),
                spacing="4",
                width="100%",
                align="start",
            ),
        )
