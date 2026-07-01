"""F-T-005 学生名单导入 — 教师端页面

路由: /student_import（由 app.py 自动发现注册）
页面函数: student_import_page()
状态类: StudentImportState（states/student_import.py）

功能：
- CSV 文件上传与解析
- 数据验证与错误高亮
- 增量导入/全量覆盖模式
- 导入日志记录
"""

import reflex as rx

from oaepp.components.layout import page_layout
from oaepp.components.common import empty_state, loading_spinner
from oaepp.states.student_import import StudentImportState


def upload_zone() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("upload", size=24, color="blue"),
                rx.heading("上传学生名单 CSV", size="4"),
                spacing="3",
            ),
            rx.text(
                "支持从教务系统导出的 CSV 文件，包含学号、姓名、班级、课程四个字段",
                size="2",
                color="gray",
            ),
            rx.divider(),
            rx.upload(
                rx.vstack(
                    rx.icon("file-up", size=32, color="gray"),
                    rx.text("点击或拖拽 CSV 文件到此处上传", size="3"),
                    rx.text("支持 .csv 格式，编码自动检测", size="1", color="gray"),
                    spacing="2",
                    padding="32px",
                ),
                accept={".csv"},
                multiple=False,
                on_drop=StudentImportState.handle_upload(rx.upload_files()),
                id="csv_upload",
            ),
            rx.cond(
                StudentImportState.is_parsing,
                loading_spinner("解析中..."),
                rx.fragment(),
            ),
            rx.cond(
                StudentImportState.parse_error,
                rx.box(
                    rx.text(StudentImportState.parse_error, color="red"),
                    padding="12px",
                    background="#fef2f2",
                    border="1px solid #fecaca",
                    border_radius="8px",
                    margin_top="16px",
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
        padding="24px",
        background="white",
        border="1px solid var(--gray-4)",
        border_radius="12px",
    )


def import_settings() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("settings", size=20, color="blue"),
                rx.text("导入设置", font_weight="bold"),
                spacing="2",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("目标课程 *", font_size="sm", color="gray.600"),
                    rx.select.root(
                        rx.select.trigger(placeholder="选择课程"),
                        rx.select.content(
                            rx.select.group(
                                *[
                                    rx.select.item(
                                        f"{c['code']} - {c['name']}",
                                        value=c["id"],
                                    )
                                    for c in StudentImportState.courses
                                ]
                            ),
                        ),
                        value=StudentImportState.selected_course_id,
                        on_change=StudentImportState.set_selected_course,
                        width="100%",
                    ),
                    spacing="1",
                    width="50%",
                ),
                rx.vstack(
                    rx.text("导入模式", font_size="sm", color="gray.600"),
                    rx.hstack(
                        rx.button(
                            "增量导入",
                            variant=rx.cond(
                                StudentImportState.import_mode == "incremental",
                                "solid",
                                "outline",
                            ),
                            color_scheme="blue",
                            on_click=StudentImportState.set_import_mode("incremental"),
                            size="2",
                        ),
                        rx.button(
                            "全量覆盖",
                            variant=rx.cond(
                                StudentImportState.import_mode == "overwrite",
                                "solid",
                                "outline",
                            ),
                            color_scheme="orange",
                            on_click=StudentImportState.set_import_mode("overwrite"),
                            size="2",
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        "全量覆盖将禁用该课程下所有现有学生",
                        font_size="xs",
                        color="orange.500",
                    ),
                    spacing="1",
                    width="50%",
                ),
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        padding="20px",
        background="white",
        border="1px solid var(--gray-4)",
        border_radius="12px",
    )


def data_preview_table() -> rx.Component:
    def row_component(row: dict, idx: int) -> rx.Component:
        errors = row.get("_errors", [])
        is_error = len(errors) > 0
        bg_color = "#fef2f2" if is_error else "white"
        border_color = "#fecaca" if is_error else "var(--gray-4)"

        return rx.tr(
            rx.td(row.get("_line_num", idx + 2)),
            rx.td(
                rx.input(
                    value=row.get("student_no", ""),
                    on_change=lambda v: StudentImportState.update_row_field(
                        idx, "student_no", v
                    ),
                    size="1",
                    width="120px",
                )
            ),
            rx.td(
                rx.input(
                    value=row.get("full_name", ""),
                    on_change=lambda v: StudentImportState.update_row_field(
                        idx, "full_name", v
                    ),
                    size="1",
                    width="100px",
                )
            ),
            rx.td(
                rx.input(
                    value=row.get("class_name", ""),
                    on_change=lambda v: StudentImportState.update_row_field(
                        idx, "class_name", v
                    ),
                    size="1",
                    width="120px",
                )
            ),
            rx.td(row.get("course_code", "")),
            rx.td(
                rx.vstack(
                    *[rx.text(e, color="red", font_size="xs") for e in errors],
                    spacing="1",
                )
                if is_error
                else rx.icon("check", size=16, color="green")
            ),
            style={
                "background": bg_color,
                "border-bottom": f"1px solid {border_color}",
            },
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("数据预览", size="4"),
                rx.spacer(),
                rx.hstack(
                    rx.badge(
                        f"有效: {StudentImportState.success_count}",
                        color_scheme="green",
                        variant="soft",
                    ),
                    rx.badge(
                        f"错误: {StudentImportState.error_count}",
                        color_scheme="red",
                        variant="soft",
                    ),
                    spacing="2",
                ),
                spacing="4",
                width="100%",
            ),
            rx.divider(),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("行号"),
                            rx.table.column_header_cell("学号"),
                            rx.table.column_header_cell("姓名"),
                            rx.table.column_header_cell("班级"),
                            rx.table.column_header_cell("课程代码"),
                            rx.table.column_header_cell("状态"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(StudentImportState.parsed_rows, row_component)
                    ),
                ),
                overflow_x="auto",
                max_height="400px",
                overflow_y="auto",
            ),
            spacing="3",
            width="100%",
        ),
        padding="24px",
        background="white",
        border="1px solid var(--gray-4)",
        border_radius="12px",
    )


def import_confirm_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("确认导入"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text(
                        f"即将导入 {StudentImportState.success_count} 条有效数据",
                        size="3",
                    ),
                    rx.text(
                        f"导入模式: {StudentImportState.import_mode}",
                        size="2",
                        color="gray",
                    ),
                    rx.cond(
                        StudentImportState.import_mode == "overwrite",
                        rx.box(
                            rx.text(
                                "警告：全量覆盖将禁用该课程下所有现有学生！",
                                color="red",
                                font_weight="bold",
                            ),
                            padding="12px",
                            background="#fef2f2",
                            border="1px solid #fecaca",
                            border_radius="8px",
                            margin_top="12px",
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                )
            ),
            rx.hstack(
                rx.button(
                    "取消",
                    variant="outline",
                    on_click=rx.alert_dialog.close(),
                ),
                rx.button(
                    "确认导入",
                    color_scheme="blue",
                    on_click=rx.event.trigger(
                        StudentImportState.execute_import(
                            [r for r in StudentImportState.parsed_rows if r.get("_valid")]
                        ),
                        after=rx.alert_dialog.close(),
                    ),
                    loading=StudentImportState.is_importing,
                ),
                spacing="2",
                justify="end",
                width="100%",
            ),
        ),
        open=False,
        id="import_confirm_dialog",
    )


def import_button() -> rx.Component:
    return rx.button(
        rx.icon("check-circle", size=18),
        "确认导入",
        size="3",
        color_scheme="green",
        on_click=StudentImportState.confirm_import(),
        loading=StudentImportState.is_importing,
        disabled=StudentImportState.has_errors
        or not StudentImportState.has_data
        or StudentImportState.is_importing,
    )


def import_result() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("info", size=20, color="blue"),
                rx.text(StudentImportState.import_result, size="3"),
                spacing="2",
            ),
            spacing="2",
        ),
        padding="16px",
        background="#eff6ff",
        border="1px solid #bfdbfe",
        border_radius="8px",
        margin_top="16px",
    )


def import_logs() -> rx.Component:
    def log_row(log: dict) -> rx.Component:
        return rx.tr(
            rx.td(log.get("created_at", "")),
            rx.td(log.get("batch_no", "")),
            rx.td(
                rx.badge(
                    log.get("import_mode", ""),
                    color_scheme="blue"
                    if log.get("import_mode") == "增量导入"
                    else "orange",
                    variant="soft",
                )
            ),
            rx.td(log.get("course_code", "")),
            rx.td(log.get("file_name", "")),
            rx.td(
                f"{log.get('success_rows', 0)}/{log.get('total_rows', 0)}"
            ),
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("history", size=20, color="blue"),
                rx.heading("导入日志", size="4"),
                rx.button(
                    "刷新",
                    size="1",
                    on_click=StudentImportState.load_import_logs(),
                ),
                spacing="3",
            ),
            rx.divider(),
            rx.cond(
                StudentImportState.logs_loading,
                loading_spinner("加载日志中..."),
                rx.cond(
                    len(StudentImportState.logs) == 0,
                    empty_state("暂无导入记录"),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("时间"),
                                    rx.table.column_header_cell("批次号"),
                                    rx.table.column_header_cell("模式"),
                                    rx.table.column_header_cell("课程"),
                                    rx.table.column_header_cell("文件名"),
                                    rx.table.column_header_cell("结果"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(StudentImportState.logs, log_row)
                            ),
                        ),
                        overflow_x="auto",
                    ),
                ),
            ),
            spacing="3",
            width="100%",
        ),
        padding="24px",
        background="white",
        border="1px solid var(--gray-4)",
        border_radius="12px",
        margin_top="24px",
    )


def student_import_page() -> rx.Component:
    return page_layout(
        title="学生名单导入",
        content=rx.vstack(
            upload_zone(),
            rx.cond(
                StudentImportState.has_data,
                rx.vstack(
                    import_settings(),
                    data_preview_table(),
                    rx.hstack(
                        rx.spacer(),
                        import_button(),
                        spacing="4",
                        width="100%",
                    ),
                    rx.cond(
                        StudentImportState.import_result,
                        import_result(),
                        rx.fragment(),
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.fragment(),
            ),
            import_logs(),
            rx.toast.provider(),
            spacing="4",
            width="100%",
            max_width="1200px",
            on_mount=StudentImportState.load_courses(),
        ),
    )