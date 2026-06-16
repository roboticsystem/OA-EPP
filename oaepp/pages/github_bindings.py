"""F-T-001 学生-GitHub账号对应表管理页面 (教师功能)

功能：
- 管理全班学生与GitHub账号的完整映射表
- 支持CSV批量导入（学号/姓名/GitHub用户名）并自动校验
- 支持单条手动新增/编辑/删除
- 变更后关联学生历史成绩自动重算
- 支持按班级/课程筛选与导出
"""
import reflex as rx
try:
    from oaepp.components.layout import page_layout
    from oaepp.components.common import stat_card, empty_state, loading_spinner
    from oaepp.states.teacher_github_map import StudentGitHubState
except ImportError:
    from components.layout import page_layout
    from components.common import stat_card, empty_state, loading_spinner
    from states.teacher_github_map import StudentGitHubState


def _status_badge(status: str) -> rx.Component:
    """状态标签"""
    color = {
        "approved": "green",
        "pending": "yellow",
        "rejected": "red"
    }.get(status, "gray")
    
    label = {
        "approved": "已通过",
        "pending": "待审核",
        "rejected": "已拒绝"
    }.get(status, status)
    
    return rx.badge(label, color_scheme=color, size="2")


def _binding_row(binding: dict) -> rx.Component:
    """单行绑定数据"""
    return rx.table.row(
        rx.table.cell(binding["student_no"]),
        rx.table.cell(binding["full_name"]),
        rx.table.cell(binding["class_name"]),
        rx.table.cell(
            rx.hstack(
                rx.icon(tag="folder-git", size=16),
                rx.text(binding["github_username"]),
                spacing="2",
            )
        ),
        rx.table.cell(rx.cond(binding["github_name"], binding["github_name"], "-")),
        rx.table.cell(_status_badge(binding["verify_status"])),
        rx.table.cell(binding["grade_count"].to_string()),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon(tag="pencil", size=16),
                    size="2",
                    variant="soft",
                    on_click=lambda: StudentGitHubState.open_edit_dialog(binding),
                ),
                rx.button(
                    rx.icon(tag="trash-2", size=16),
                    size="2",
                    variant="soft",
                    color_scheme="red",
                    on_click=lambda: StudentGitHubState.delete_binding(binding["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _course_select() -> rx.Component:
    """课程选择器"""
    return rx.select.root(
        rx.select.trigger(width="240px"),
        rx.select.content(
            rx.select.group(
                rx.foreach(
                    StudentGitHubState.courses,
                    lambda c: rx.select.item(
                        f"{c['code']} - {c['name']}",
                        value=c["id"].to_string()
                    )
                )
            ),
        ),
        placeholder="全部课程",
        value=rx.cond(
            StudentGitHubState.selected_course_id,
            StudentGitHubState.selected_course_id.to_string(),
            None
        ),
        on_change=StudentGitHubState.set_selected_course,
    )


def _class_select() -> rx.Component:
    """班级选择器"""
    return rx.select.root(
        rx.select.trigger(width="160px"),
        rx.select.content(
            rx.select.group(
                rx.foreach(
                    StudentGitHubState.class_names,
                    lambda c: rx.select.item(c, value=c)
                )
            ),
        ),
        placeholder="全部班级",
        value=StudentGitHubState.selected_class_name,
        on_change=StudentGitHubState.set_selected_class,
    )


def _filter_bar() -> rx.Component:
    """筛选栏"""
    return rx.hstack(
        # 课程筛选
        rx.vstack(
            rx.text("课程", size="2", color="gray"),
            _course_select(),
            spacing="1",
            align="start",
        ),
        # 班级筛选
        rx.vstack(
            rx.text("班级", size="2", color="gray"),
            _class_select(),
            spacing="1",
            align="start",
        ),
        # 搜索框
        rx.vstack(
            rx.text("搜索", size="2", color="gray"),
            rx.hstack(
                rx.input(
                    placeholder="学号/姓名/GitHub用户名",
                    value=StudentGitHubState.search_keyword,
                    on_change=StudentGitHubState.set_search_keyword,
                    width="200px",
                ),
                rx.button(
                    rx.icon(tag="search", size=16),
                    on_click=StudentGitHubState.do_search,
                ),
                spacing="2",
            ),
            spacing="1",
            align="start",
        ),
        rx.box(flex="1"),
        # 操作按钮
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon(tag="download", size=16),
                    rx.text("导出CSV"),
                    spacing="2",
                ),
                on_click=StudentGitHubState.export_csv,
                variant="soft",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=16),
                    rx.text("新增绑定"),
                    spacing="2",
                ),
                on_click=StudentGitHubState.open_add_dialog,
                color_scheme="green",
            ),
            spacing="3",
        ),
        spacing="4",
        align="end",
        width="100%",
        padding="16px 0",
    )


def _stat_card(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    """统计卡片组件"""
    # 判断是否为字符串（非Var类型）
    is_str = isinstance(value, str)
    
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
                rx.heading(value if is_str else value.to_string(), size="5"),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        width="100%",
        padding="20px",
    )


def _stats_bar() -> rx.Component:
    """统计栏"""
    return rx.grid(
        _stat_card(
            "总绑定数",
            StudentGitHubState.bindings.length(),
            icon="users"
        ),
        _stat_card(
            "已通过",
            StudentGitHubState.student_github_map.length(),
            icon="check-check"
        ),
        _stat_card(
            "待审核",
            "-",
            icon="clock"
        ),
        columns="3",
        spacing="4",
        width="100%",
    )


def _bindings_table() -> rx.Component:
    """绑定数据表格"""
    return rx.cond(
        StudentGitHubState.loading,
        loading_spinner("加载中..."),
        rx.cond(
            StudentGitHubState.bindings.length() == 0,
            empty_state("暂无绑定数据，请导入或手动添加"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("学号"),
                        rx.table.column_header_cell("姓名"),
                        rx.table.column_header_cell("班级"),
                        rx.table.column_header_cell("GitHub用户名"),
                        rx.table.column_header_cell("GitHub显示名"),
                        rx.table.column_header_cell("状态"),
                        rx.table.column_header_cell("成绩数"),
                        rx.table.column_header_cell("操作"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(StudentGitHubState.bindings, _binding_row)
                ),
                width="100%",
            ),
        ),
    )


def _edit_dialog() -> rx.Component:
    """编辑/新增对话框"""
    return rx.dialog.root(
        rx.dialog.trigger(rx.box()),
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    StudentGitHubState.is_new_binding,
                    "新增GitHub绑定",
                    "编辑GitHub绑定"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    StudentGitHubState.is_new_binding,
                    "为学生绑定GitHub账号",
                    "修改学生的GitHub绑定信息"
                )
            ),
            rx.vstack(
                # 错误提示
                rx.cond(
                    StudentGitHubState.error_message,
                    rx.callout(
                        StudentGitHubState.error_message,
                        icon="circle-x",
                        color_scheme="red",
                        width="100%",
                    ),
                    rx.box()
                ),
                # 成功提示
                rx.cond(
                    StudentGitHubState.success_message,
                    rx.callout(
                        StudentGitHubState.success_message,
                        icon="check-check",
                        color_scheme="green",
                        width="100%",
                    ),
                    rx.box()
                ),
                # 学号
                rx.vstack(
                    rx.text("学号 *", size="2", weight="bold"),
                    rx.input(
                        placeholder="请输入学号",
                        value=StudentGitHubState.form_student_no,
                        on_change=StudentGitHubState.set_form_student_no,
                        disabled=~StudentGitHubState.is_new_binding,
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                # 姓名
                rx.vstack(
                    rx.text("姓名 *", size="2", weight="bold"),
                    rx.input(
                        placeholder="请输入姓名",
                        value=StudentGitHubState.form_full_name,
                        on_change=StudentGitHubState.set_form_full_name,
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                # GitHub用户名
                rx.vstack(
                    rx.text("GitHub用户名 *", size="2", weight="bold"),
                    rx.input(
                        placeholder="请输入GitHub用户名（不含@）",
                        value=StudentGitHubState.form_github_username,
                        on_change=StudentGitHubState.set_form_github_username,
                    ),
                    rx.text(
                        "GitHub用户名格式：字母数字开头，可包含连字符，最长39字符",
                        size="1",
                        color="gray",
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                # GitHub显示名
                rx.vstack(
                    rx.text("GitHub显示名", size="2", weight="bold"),
                    rx.input(
                        placeholder="可选，GitHub个人资料中的显示名称",
                        value=StudentGitHubState.form_github_name,
                        on_change=StudentGitHubState.set_form_github_name,
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_top="16px",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("取消", variant="soft", color_scheme="gray")
                ),
                rx.button(
                    "保存",
                    on_click=StudentGitHubState.save_binding,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                padding_top="24px",
            ),
            max_width="480px",
        ),
        open=StudentGitHubState.show_edit_dialog,
        on_open_change=lambda open: rx.cond(
            ~open,
            StudentGitHubState.close_edit_dialog,
            rx.noop()
        ),
    )


def _conflict_dialog() -> rx.Component:
    """冲突提示对话框"""
    return rx.dialog.root(
        rx.dialog.trigger(rx.box()),
        rx.dialog.content(
            rx.dialog.title("绑定冲突"),
            rx.dialog.description("检测到以下冲突，是否强制覆盖？"),
            rx.callout(
                StudentGitHubState.conflict_message,
                icon="triangle-alert",
                color_scheme="yellow",
                width="100%",
                margin_top="16px",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("取消", variant="soft", color_scheme="gray")
                ),
                rx.button(
                    "强制覆盖",
                    on_click=StudentGitHubState.confirm_conflict,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                padding_top="24px",
            ),
            max_width="400px",
        ),
        open=StudentGitHubState.show_conflict_dialog,
        on_open_change=lambda open: rx.cond(
            ~open,
            StudentGitHubState.cancel_conflict,
            rx.noop()
        ),
    )


def _import_section() -> rx.Component:
    """CSV导入区域"""
    return rx.vstack(
        rx.text("CSV批量导入", size="3", weight="bold"),
        rx.text(
            "上传CSV文件，格式要求：包含 学号、姓名、GitHub用户名 三列",
            size="2",
            color="gray",
        ),
        rx.upload(
            rx.vstack(
                rx.icon(tag="cloud-upload", size=32, color="gray"),
                rx.text("点击或拖拽上传CSV文件", size="2", color="gray"),
                spacing="2",
                align="center",
                padding="24px",
            ),
            id="csv_upload",
            accept={".csv": ".csv"},
            max_files=1,
            on_drop=StudentGitHubState.handle_csv_upload(rx.upload_files("csv_upload")),
            border="1px dashed var(--gray-6)",
            border_radius="8px",
            width="100%",
        ),
        rx.cond(
            StudentGitHubState.csv_content,
            rx.hstack(
                rx.icon(tag="file-check", size=16, color="green"),
                rx.text(f"已选择: {StudentGitHubState.csv_filename}", size="2", color="green"),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="file-up", size=16),
                        rx.text("开始导入"),
                        spacing="2",
                    ),
                    on_click=lambda: StudentGitHubState.import_csv(),
                    loading=StudentGitHubState.import_loading,
                    color_scheme="blue",
                ),
                spacing="3",
            ),
            rx.box()
        ),
        # 导入结果
        rx.cond(
            StudentGitHubState.import_success_count > 0,
            rx.callout(
                StudentGitHubState.import_success_message,
                icon="check-check",
                color_scheme="green",
                width="100%",
            ),
            rx.box()
        ),
        rx.cond(
            StudentGitHubState.import_failed_count > 0,
            rx.vstack(
                rx.callout(
                    StudentGitHubState.import_failed_message,
                    icon="circle-x",
                    color_scheme="red",
                    width="100%",
                ),
                rx.foreach(
                    StudentGitHubState.import_failed_list,
                    lambda item: rx.text(
                        f"行: {item['row']}, 原因: {item['reason']}",
                        size="2",
                        color="red"
                    )
                ),
                spacing="2",
                width="100%",
            ),
            rx.box()
        ),
        rx.cond(
            StudentGitHubState.import_conflicts_count > 0,
            rx.callout(
                StudentGitHubState.import_conflicts_message,
                icon="triangle-alert",
                color_scheme="yellow",
                width="100%",
            ),
            rx.box()
        ),
        spacing="3",
        align="start",
        width="100%",
        padding="16px",
        background_color="var(--gray-2)",
        border_radius="8px",
    )


def github_bindings_page() -> rx.Component:
    """学生-GitHub账号对应表管理页面"""
    return rx.container(
        rx.vstack(
            # 页面标题
            rx.heading("学生-GitHub账号对应表管理", size="6"),
            rx.divider(),
            
            # 统计栏
            _stats_bar(),
            
            # 导入区域
            _import_section(),
            
            # 筛选栏
            _filter_bar(),
            
            # 消息提示
            rx.cond(
                StudentGitHubState.error_message,
                rx.callout(
                    StudentGitHubState.error_message,
                    icon="circle-x",
                    color_scheme="red",
                    width="100%",
                ),
                rx.box()
            ),
            rx.cond(
                StudentGitHubState.success_message,
                rx.callout(
                    StudentGitHubState.success_message,
                    icon="check-check",
                    color_scheme="green",
                    width="100%",
                ),
                rx.box()
            ),
            
            # 数据表格
            _bindings_table(),
            
            # 对话框
            _edit_dialog(),
            _conflict_dialog(),
            
            spacing="4",
            width="100%",
            on_mount=StudentGitHubState.on_mount,
        ),
        size="4",
        padding="4",
    )
