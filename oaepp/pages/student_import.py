"""F-T-005 学生名单导入页面（教师端）

对应原型：prototype/admin_students.html（学生名单导入功能）
路由：/student_import（由 app.py 自动发现机制注册）

验收要点：
- 支持CSV格式导入，错误行高亮提示并可修正重导
- 自动校验学号唯一性/字段完整性/班级合法性
- 导入后自动创建账号（默认密码为学号）
- 发送激活邀请（邮件或首页公告）
- 支持增量导入和全量覆盖两种模式
- 日志导入记录时间/批次/操作人/记录数
"""
try:
    import reflex as rx
except Exception:
    rx = None

student_import_page = None
if rx is not None:
    try:
        from states.student_import import StudentImportState
    except ImportError:
        from oaepp.states.student_import import StudentImportState

    _BG = "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)"

    def _file_upload_area() -> rx.Component:
        """文件上传区域"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("CSV文件上传", weight="bold", size="3"),
                    rx.button(
                        "下载模板",
                        size="1",
                        variant="outline",
                        color_scheme="indigo",
                        on_click=StudentImportState.download_template,
                    ),
                    justify="between",
                    width="100%",
                ),
                rx.text(
                    "请上传包含学号、姓名、班级、课程字段的CSV文件。点击下载模板查看格式要求。",
                    color="gray",
                    size="1",
                ),
                rx.upload(
                    rx.box(
                        rx.vstack(
                            rx.icon(tag="upload", size=32, color="gray"),
                            rx.text("点击或拖拽文件到此处上传", size="3"),
                            rx.text("支持 .csv 格式，文件大小不超过 10MB", size="1", color="gray"),
                            rx.text("上传后仅解析校验，请点击确认导入完成导入", size="1", color="gray"),
                            spacing="2",
                            padding="24px",
                        ),
                        border="2px dashed var(--gray-4)",
                        border_radius="8px",
                        background="var(--gray-1)",
                        width="100%",
                    ),
                    accept={".csv": []},
                    on_drop=StudentImportState.handle_file_upload,
                    max_files=1,
                    multiple=False,
                ),
                spacing="3",
                width="100%",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
        )

    def _import_mode_selector() -> rx.Component:
        """导入模式选择器"""
        return rx.box(
            rx.vstack(
                rx.text("导入模式", weight="bold", size="3"),
                rx.hstack(
                    rx.radio(
                        ["incremental", "overwrite"],
                        value=StudentImportState.import_mode,
                        on_change=StudentImportState.set_import_mode,
                        direction="row",
                    ),
                    rx.box(flex="1"),
                    rx.text(
                        rx.cond(
                            StudentImportState.import_mode == "incremental",
                            "增量导入：仅导入新学生，已存在的学生跳过",
                            "全量覆盖：删除课程原有学生后重新导入",
                        ),
                        size="1",
                        color="gray",
                    ),
                    spacing="3",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
        )

    def _validation_results() -> rx.Component:
        """校验结果展示"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("数据校验结果", weight="bold", size="3"),
                    rx.hstack(
                        rx.badge(
                            f"有效: {StudentImportState.valid_count}",
                            color_scheme="green",
                            variant="soft",
                            size="1",
                        ),
                        rx.badge(
                            f"无效: {StudentImportState.invalid_count}",
                            color_scheme="red",
                            variant="soft",
                            size="1",
                        ),
                        spacing="2",
                    ),
                    justify="between",
                    width="100%",
                ),
                rx.divider(),
                rx.cond(
                    StudentImportState.has_parsed_rows,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("行号"),
                                rx.table.column_header_cell("学号"),
                                rx.table.column_header_cell("姓名"),
                                rx.table.column_header_cell("班级"),
                                rx.table.column_header_cell("课程"),
                                rx.table.column_header_cell("状态"),
                                rx.table.column_header_cell("错误信息"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                StudentImportState.parsed_rows,
                                lambda row: rx.table.row(
                                    rx.table.cell(row["row_num"], font_size="xs"),
                                    rx.table.cell(row["student_no"], font_size="xs", font_family="monospace"),
                                    rx.table.cell(row["full_name"], font_size="xs"),
                                    rx.table.cell(row["class_name"], font_size="xs"),
                                    rx.table.cell(row["course"], font_size="xs"),
                                    rx.table.cell(
                                        rx.cond(
                                            row["valid"],
                                            rx.badge("有效", color_scheme="green", variant="soft", size="1"),
                                            rx.badge("无效", color_scheme="red", variant="soft", size="1"),
                                        )
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            rx.cond(
                                                row["errors"] != "",
                                                row["errors"],
                                                "-",
                                            ),
                                            color=rx.cond(row["errors"] != "", "red", "gray"),
                                            size="1",
                                        ),
                                        font_size="xs",
                                    ),
                                    background_color=rx.cond(
                                        row["valid"],
                                        "transparent",
                                        "#fef2f2",
                                    ),
                                    _hover={"bg": "#f9fafb"},
                                ),
                            ),
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                    ),
                    rx.text("请上传文件以查看校验结果", color="gray", size="2"),
                ),
                spacing="3",
                width="100%",
            ),
            border="1px solid #e5e7eb",
            border_radius="8px",
            padding="16px",
            width="100%",
            max_height="400px",
            overflow_y="auto",
        )

    def _import_button() -> rx.Component:
        """导入按钮"""
        return rx.button(
            rx.cond(
                StudentImportState.is_loading,
                rx.text("导入中..."),
                rx.hstack(
                    rx.icon(tag="upload", size=16),
                    rx.text("确认导入"),
                    spacing="2",
                ),
            ),
            on_click=StudentImportState.handle_import,
            disabled=StudentImportState.is_import_disabled,
            color_scheme="indigo",
            size="3",
        )

    def _import_result() -> rx.Component:
        """导入结果展示"""
        return rx.cond(
            StudentImportState.has_import_result,
            rx.callout(
                StudentImportState.import_result,
                color_scheme=rx.cond(
                    StudentImportState.import_success,
                    "green",
                    "red",
                ),
                width="100%",
            ),
            rx.box(),
        )

    def _file_errors() -> rx.Component:
        """文件错误信息展示"""
        return rx.cond(
            StudentImportState.has_file_errors,
            rx.vstack(
                rx.foreach(
                    StudentImportState.file_errors,
                    lambda error: rx.callout(
                        error,
                        color_scheme="red",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.box(),
        )

    def student_import_page():
        """学生名单导入页面"""
        return rx.center(
            rx.box(
                rx.vstack(
                    rx.heading("学生名单导入", size="6"),
                    rx.text(
                        "从教务系统导出学生名单CSV文件，导入平台并自动创建学生账号",
                        color="gray",
                        size="1",
                    ),
                    rx.divider(),
                    _import_mode_selector(),
                    _file_upload_area(),
                    _file_errors(),
                    _validation_results(),
                    _import_button(),
                    _import_result(),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                max_width="1000px",
                width="100%",
                padding="28px",
                border_radius="12px",
                box_shadow="0 10px 30px rgba(0,0,0,0.08)",
                background="white",
            ),
            min_height="100vh",
            width="100%",
            background=_BG,
            padding="20px",
        )