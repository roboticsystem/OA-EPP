"""
教师后台 - 学生 GitHub 账号绑定管理页面
支持CSV批量导入、单条操作、筛选导出
"""
import reflex as rx
from dataclasses import dataclass
from typing import List, Dict, Any
import csv
import io
import re
from datetime import datetime


@dataclass
class BindingData:
    """学生-GitHub绑定数据模型"""
    id: int = 0
    student_user_id: int = 0
    student_name: str = ""
    class_name: str = ""
    github_username: str = ""
    github_name: str = ""
    course_name: str = ""
    term: str = ""


class BindingState(rx.State):
    """页面状态管理"""
    # 数据列表
    bindings: List[BindingData] = []
    filtered_bindings: List[BindingData] = []

    # 筛选条件
    search_keyword: str = ""
    filter_class: str = "全部班级"
    filter_course: str = "全部课程"

    # 弹窗控制
    show_modal: bool = False
    show_import_modal: bool = False
    is_editing: bool = False
    editing_id: int = 0

    # 表单数据
    form_student_user_id: str = ""
    form_student_name: str = ""
    form_github_username: str = ""
    form_github_name: str = ""

    # CSV导入数据
    import_text: str = ""

    def on_mount(self):
        """页面加载时初始化数据"""
        self.load_bindings()

    def load_bindings(self):
        """加载绑定数据（当前使用模拟数据）"""
        self.bindings = [
            BindingData(
                id=1, student_user_id=1001, student_name="张三",
                class_name="软件工程1班", github_username="zhangsan-dev",
                github_name="Zhang San",
                course_name="软件工程实践", term="2024春"
            ),
            BindingData(
                id=2, student_user_id=1002, student_name="李明",
                class_name="软件工程1班", github_username="liming2024",
                course_name="软件工程实践", term="2024春"
            ),
            BindingData(
                id=3, student_user_id=1003, student_name="王芳",
                class_name="软件工程2班", github_username="wangfang-git",
                github_name="Wang Fang",
                course_name="软件工程实践", term="2024春"
            ),
            BindingData(
                id=4, student_user_id=1004, student_name="刘强",
                class_name="软件工程2班", github_username="liuqiang-code",
                course_name="软件工程实践", term="2024春"
            ),
        ]
        self.update_filters()

    def update_filters(self):
        """根据筛选条件更新列表"""
        result = list(self.bindings)

        if self.search_keyword:
            kw = self.search_keyword.lower()
            result = [
                b for b in result
                if kw in str(b.student_user_id).lower()
                or kw in b.student_name.lower()
                or kw in b.github_username.lower()
            ]

        if self.filter_class != "全部班级":
            result = [b for b in result if b.class_name == self.filter_class]

        if self.filter_course != "全部课程":
            result = [b for b in result if b.course_name == self.filter_course]

        self.filtered_bindings = result

    def set_search_keyword(self, value: str):
        """设置搜索关键词"""
        self.search_keyword = value
        self.update_filters()

    def set_filter_class(self, value: str):
        """设置班级筛选"""
        self.filter_class = value
        self.update_filters()

    def set_filter_course(self, value: str):
        """设置课程筛选"""
        self.filter_course = value
        self.update_filters()

    def set_form_student_user_id(self, value: str):
        """设置表单学生ID"""
        self.form_student_user_id = value

    def set_form_student_name(self, value: str):
        """设置表单学生姓名"""
        self.form_student_name = value

    def set_form_github_username(self, value: str):
        """设置表单GitHub用户名"""
        self.form_github_username = value

    def set_form_github_name(self, value: str):
        """设置表单GitHub显示名"""
        self.form_github_name = value

    def open_add_modal(self):
        """打开新增弹窗"""
        self.is_editing = False
        self.editing_id = 0
        self.form_student_user_id = ""
        self.form_student_name = ""
        self.form_github_username = ""
        self.form_github_name = ""
        self.show_modal = True

    def open_edit_modal(self, binding: BindingData):
        """打开编辑弹窗"""
        self.is_editing = True
        self.editing_id = binding.id
        self.form_student_user_id = str(binding.student_user_id)
        self.form_student_name = binding.student_name
        self.form_github_username = binding.github_username
        self.form_github_name = binding.github_name
        self.show_modal = True

    def close_modal(self):
        """关闭弹窗"""
        self.show_modal = False
        self.show_import_modal = False

    def open_import_modal(self):
        """打开导入弹窗"""
        self.import_text = ""
        self.show_import_modal = True

    def set_import_text(self, value: str):
        """设置导入文本"""
        self.import_text = value

    def process_csv_import(self):
        """处理CSV导入"""
        if not self.import_text.strip():
            return rx.window_alert("请输入CSV内容")
        return self.parse_csv(self.import_text)

    def validate_github_username(self, username: str) -> bool:
        """验证GitHub用户名格式"""
        if not username:
            return False
        return bool(re.match(r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$", username))

    def check_conflict(self, student_user_id: int, github_username: str, exclude_id: int = 0) -> str:
        """检查绑定冲突"""
        for b in self.bindings:
            if b.id == exclude_id:
                continue
            if b.student_user_id == student_user_id:
                return f"学生ID {student_user_id} 已绑定 GitHub 账号: {b.github_username}"
            if b.github_username.lower() == github_username.lower():
                return f"GitHub 账号 {github_username} 已被学生 {b.student_name} 绑定"
        return ""

    def save_binding(self):
        """保存绑定记录"""
        if not self.form_student_user_id or not self.form_github_username:
            return rx.window_alert("学生ID和GitHub用户名不能为空")

        if not self.form_student_user_id.isdigit():
            return rx.window_alert("学生ID必须是数字")

        if not self.validate_github_username(self.form_github_username):
            return rx.window_alert("GitHub用户名格式不正确")

        conflict = self.check_conflict(
            int(self.form_student_user_id),
            self.form_github_username,
            self.editing_id
        )
        if conflict:
            return rx.window_alert(conflict)

        if self.is_editing:
            for i, b in enumerate(self.bindings):
                if b.id == self.editing_id:
                    self.bindings[i] = BindingData(
                        id=b.id,
                        student_user_id=int(self.form_student_user_id),
                        student_name=self.form_student_name,
                        class_name=b.class_name,
                        github_username=self.form_github_username,
                        github_name=self.form_github_name,
                        course_name=b.course_name,
                        term=b.term
                    )
                    break
        else:
            new_id = max(b.id for b in self.bindings) + 1 if self.bindings else 1
            self.bindings.append(BindingData(
                id=new_id,
                student_user_id=int(self.form_student_user_id),
                student_name=self.form_student_name,
                github_username=self.form_github_username,
                github_name=self.form_github_name
            ))

        self.recalculate_scores(int(self.form_student_user_id))
        self.close_modal()
        self.load_bindings()
        return rx.window_alert("保存成功")

    def delete_binding(self, binding_id: int):
        """删除绑定记录"""
        binding = next((b for b in self.bindings if b.id == binding_id), None)
        if binding:
            self.bindings = [b for b in self.bindings if b.id != binding_id]
            self.recalculate_scores(binding.student_user_id)
            self.load_bindings()
            return rx.window_alert("删除成功")

    def recalculate_scores(self, student_user_id: int):
        """重算学生成绩"""
        print(f"已为重算学生 {student_user_id} 的成绩")

    async def handle_upload(self, files: list):
        """处理文件上传"""
        if not files:
            return rx.window_alert("请选择CSV文件")
        
        file = files[0]
        try:
            # 读取文件内容
            content = file.read().decode('utf-8-sig')
            return self.parse_csv(content)
        except Exception as e:
            return rx.window_alert(f"文件读取失败: {str(e)}")

    def parse_csv(self, content: str):
        """解析CSV内容"""
        try:
            reader = csv.DictReader(io.StringIO(content))

            # 检查表头
            fieldnames = reader.fieldnames
            if not fieldnames:
                return rx.window_alert("CSV文件为空或格式不正确")

            # 支持两种表头格式
            header_mapping = {}
            for header in fieldnames:
                header_clean = header.strip()
                if header_clean in ['学号', '学生ID', 'student_id']:
                    header_mapping['学号'] = header_clean
                elif header_clean in ['姓名', '学生姓名', 'name']:
                    header_mapping['姓名'] = header_clean
                elif header_clean in ['GitHub用户名', 'github', 'github_username']:
                    header_mapping['GitHub用户名'] = header_clean

            if '学号' not in header_mapping or '姓名' not in header_mapping or 'GitHub用户名' not in header_mapping:
                return rx.window_alert("CSV表头不正确，需要包含：学号、姓名、GitHub用户名")

            imported_count = 0
            error_messages = []

            for row_num, row in enumerate(reader, start=2):
                student_id = row.get(header_mapping['学号'], '').strip()
                student_name = row.get(header_mapping['姓名'], '').strip()
                github_username = row.get(header_mapping['GitHub用户名'], '').strip()

                # 验证数据
                if not student_id:
                    error_messages.append(f"第{row_num}行：学号不能为空")
                    continue
                if not student_id.isdigit():
                    error_messages.append(f"第{row_num}行：学号必须是数字")
                    continue
                if not student_name:
                    error_messages.append(f"第{row_num}行：姓名不能为空")
                    continue
                if not github_username:
                    error_messages.append(f"第{row_num}行：GitHub用户名不能为空")
                    continue
                if not self.validate_github_username(github_username):
                    error_messages.append(f"第{row_num}行：GitHub用户名格式不正确")
                    continue

                # 检查冲突
                conflict = self.check_conflict(int(student_id), github_username)
                if conflict:
                    error_messages.append(f"第{row_num}行：{conflict}")
                    continue

                # 添加新记录
                new_id = max(b.id for b in self.bindings) + 1 if self.bindings else 1
                self.bindings.append(BindingData(
                    id=new_id,
                    student_user_id=int(student_id),
                    student_name=student_name,
                    github_username=github_username
                ))
                imported_count += 1

            self.load_bindings()

            if error_messages:
                error_text = "\n".join(error_messages[:5])
                if len(error_messages) > 5:
                    error_text += f"\n...还有{len(error_messages) - 5}条错误"
                return rx.window_alert(f"导入完成：成功{imported_count}条\n\n错误：\n{error_text}")
            else:
                return rx.window_alert(f"导入成功：共导入{imported_count}条记录")

        except Exception as e:
            return rx.window_alert(f"解析CSV失败: {str(e)}")

    def export_csv(self):
        """导出CSV文件"""
        data = self.filtered_bindings if self.filtered_bindings else self.bindings

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['学号', '姓名', '班级', 'GitHub用户名', 'GitHub显示名', '课程'])

        for b in data:
            writer.writerow([
                b.student_user_id,
                b.student_name,
                b.class_name,
                b.github_username,
                b.github_name,
                b.course_name
            ])

        return rx.download(
            data=output.getvalue(),
            filename=f"github_bindings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime_type='text/csv'
        )


def github_bindings_page() -> rx.Component:
    """GitHub绑定管理页面组件"""
    return rx.container(
        rx.vstack(
            # 页面标题
            rx.heading("学生-GitHub账号绑定管理", size="8", color="blue.600", margin_bottom="6"),

            # 统计卡片
            rx.hstack(
                rx.card(
                    rx.hstack(
                        rx.icon("users", size=32, color="blue.500"),
                        rx.vstack(
                            rx.text("总绑定数", size="2", color="gray.500", weight="medium"),
                            rx.heading(BindingState.bindings.length(), size="7", color="blue.600"),
                            spacing="1",
                            align_items="start",
                        ),
                        spacing="4",
                        align_items="center",
                    ),
                    width="240px",
                    box_shadow="sm",
                    border_radius="lg",
                ),
                spacing="4",
                margin_bottom="6",
                width="100%",
            ),

            # 操作栏 - 导入导出和新增
            rx.card(
                rx.hstack(
                    rx.hstack(
                        rx.upload(
                            rx.button(
                                rx.hstack(
                                    rx.icon("upload", size=16),
                                    rx.text("选择CSV"),
                                    spacing="2",
                                ),
                                color_scheme="cyan",
                                variant="soft",
                            ),
                            id="csv_upload",
                            accept={"text/csv": [".csv"]},
                            max_files=1,
                            border="1px dashed",
                            border_color="gray.300",
                            padding="2",
                            border_radius="md",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("file-check", size=16),
                                rx.text("导入"),
                                spacing="2",
                            ),
                            on_click=BindingState.handle_upload(rx.selected_files("csv_upload")),
                            color_scheme="blue",
                            variant="solid",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("download", size=16),
                                rx.text("导出"),
                                spacing="2",
                            ),
                            on_click=BindingState.export_csv,
                            color_scheme="orange",
                            variant="soft",
                        ),
                        rx.divider(orientation="vertical", height="32px"),
                        rx.button(
                            rx.hstack(
                                rx.icon("plus", size=16),
                                rx.text("新增绑定"),
                                spacing="2",
                            ),
                            on_click=BindingState.open_add_modal,
                            color_scheme="green",
                            variant="solid",
                        ),
                        spacing="3",
                    ),
                    rx.spacer(),
                ),
                width="100%",
                margin_bottom="4",
                padding="4",
            ),

            # 筛选栏
            rx.card(
                rx.hstack(
                    rx.hstack(
                        rx.icon("search", size=18, color="gray.400"),
                        rx.input(
                            placeholder="搜索学号/姓名/GitHub账号...",
                            value=BindingState.search_keyword,
                            on_change=BindingState.set_search_keyword,
                            width="300px",
                            border="none",
                            _focus={"box_shadow": "none"},
                        ),
                        spacing="2",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                        padding_x="3",
                        align_items="center",
                    ),
                    rx.select(
                        ["全部班级", "软件工程1班", "软件工程2班"],
                        value=BindingState.filter_class,
                        on_change=BindingState.set_filter_class,
                        width="160px",
                        variant="soft",
                    ),
                    rx.select(
                        ["全部课程", "软件工程实践"],
                        value=BindingState.filter_course,
                        on_change=BindingState.set_filter_course,
                        width="160px",
                        variant="soft",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("refresh-cw", size=14),
                            rx.text("重置"),
                            spacing="2",
                        ),
                        on_click=BindingState.load_bindings,
                        variant="ghost",
                        size="2",
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="100%",
                margin_bottom="4",
                padding="4",
            ),

        # 数据表格
        rx.card(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("hash", size=14), rx.text("学号")), width="100px"
                        ),
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("user", size=14), rx.text("姓名")), width="120px"
                        ),
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("building", size=14), rx.text("班级")), width="150px"
                        ),
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("book-open", size=14), rx.text("课程")), width="150px"
                        ),
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("git-branch", size=14), rx.text("GitHub用户名")), width="180px"
                        ),
                        rx.table.column_header_cell(
                            rx.hstack(rx.icon("settings", size=14), rx.text("操作")), width="120px"
                        ),
                        background="gray.50",
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        BindingState.filtered_bindings,
                        lambda binding: rx.table.row(
                            rx.table.cell(
                                rx.badge(binding.student_user_id, color_scheme="blue", variant="soft")
                            ),
                            rx.table.cell(
                                rx.hstack(
                                    rx.avatar(fallback=binding.student_name[0], size="1"),
                                    rx.text(binding.student_name, weight="medium"),
                                    spacing="2",
                                )
                            ),
                            rx.table.cell(binding.class_name),
                            rx.table.cell(binding.course_name),
                            rx.table.cell(
                                rx.hstack(
                                    rx.icon("git-branch", size=14),
                                    rx.link(
                                        binding.github_username,
                                        href=f"https://github.com/{binding.github_username}",
                                        is_external=True,
                                        color="blue.500",
                                    ),
                                    spacing="2",
                                )
                            ),
                            rx.table.cell(
                                rx.hstack(
                                    rx.button(
                                        rx.icon("pencil", size=14),
                                        size="1",
                                        variant="soft",
                                        color_scheme="blue",
                                        on_click=lambda: BindingState.open_edit_modal(binding)
                                    ),
                                    rx.button(
                                        rx.icon("trash-2", size=14),
                                        size="1",
                                        variant="soft",
                                        color_scheme="red",
                                        on_click=lambda: BindingState.delete_binding(binding.id)
                                    ),
                                    spacing="2"
                                )
                            ),
                            _hover={"background": "gray.50"},
                        )
                    )
                ),
                width="100%",
                variant="surface",
            ),
            width="100%",
            padding="0",
            overflow="hidden",
        ),

        # 新增/编辑弹窗
        rx.cond(
            BindingState.show_modal,
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.hstack(
                            rx.cond(BindingState.is_editing, rx.icon("pencil", size=20), rx.icon("user-plus", size=20)),
                            rx.cond(BindingState.is_editing, "编辑绑定", "新增绑定"),
                            spacing="2",
                        )
                    ),
                    rx.vstack(
                        rx.form.field(
                            rx.form.label("学生学号", weight="medium"),
                            rx.input(
                                placeholder="请输入学号",
                                value=BindingState.form_student_user_id,
                                on_change=lambda v: BindingState.set_form_student_user_id(v),
                            ),
                        ),
                        rx.form.field(
                            rx.form.label("学生姓名", weight="medium"),
                            rx.input(
                                placeholder="请输入姓名",
                                value=BindingState.form_student_name,
                                on_change=lambda v: BindingState.set_form_student_name(v),
                            ),
                        ),
                        rx.form.field(
                            rx.form.label("GitHub用户名", weight="medium"),
                            rx.input(
                                placeholder="请输入GitHub用户名",
                                value=BindingState.form_github_username,
                                on_change=lambda v: BindingState.set_form_github_username(v),
                            ),
                        ),
                        rx.form.field(
                            rx.form.label("GitHub显示名", weight="medium"),
                            rx.input(
                                placeholder="可选，默认为空",
                                value=BindingState.form_github_name,
                                on_change=lambda v: BindingState.set_form_github_name(v),
                            ),
                        ),
                        rx.hstack(
                            rx.button(
                                rx.hstack(rx.icon("x", size=16), rx.text("取消")),
                                on_click=BindingState.close_modal,
                                variant="soft",
                                color_scheme="gray",
                            ),
                            rx.button(
                                rx.hstack(rx.icon("check", size=16), rx.text("保存")),
                                on_click=BindingState.save_binding,
                                color_scheme="blue",
                            ),
                            spacing="3",
                            justify="end",
                            width="100%",
                        ),
                        spacing="4",
                        padding="4",
                        width="100%",
                    ),
                    max_width="450px",
                ),
                open=BindingState.show_modal
            )
        ),

        # CSV导入弹窗
        rx.cond(
            BindingState.show_import_modal,
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("CSV批量导入"),
                    rx.vstack(
                        rx.text("请粘贴CSV内容（表头：学号,姓名,GitHub用户名）："),
                        rx.text_area(
                            placeholder="学号,姓名,GitHub用户名\n1001,张三,zhangsan\n1002,李四,lisi",
                            value=BindingState.import_text,
                            on_change=lambda v: BindingState.set_import_text(v),
                            height="200px",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button("取消", on_click=BindingState.close_modal),
                            rx.button("导入", on_click=BindingState.process_csv_import, color_scheme="blue"),
                            spacing="4"
                        ),
                        spacing="4",
                        padding="4"
                    )
                ),
                open=BindingState.show_import_modal
            )
        ),

            padding="6",
            spacing="4",
            width="100%",
            max_width="1200px",
            on_mount=BindingState.on_mount
        )
    )
