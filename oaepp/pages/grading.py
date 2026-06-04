"""
教师端作业在线批改页面 - F-T-014
包含批改队列、逐份批改、评语输入、二次提交标记等功能
"""
try:
    import reflex as rx
except Exception:
    rx = None

# 模拟数据
mock_submissions = [
    {
        "id": 1,
        "assignment_title": "第7章 软件需求规格说明书",
        "student_name": "张小明",
        "student_id": "20210001",
        "class_name": "计算机2101",
        "course_name": "工程实践4（2025春）",
        "submitted_at": "2025-05-26 21:32",
        "deadline": "2025-05-27 23:59",
        "file_url": "/uploads/20210001_srs.pdf",
        "text_content": None,
        "version_no": 1,
        "allow_resubmit": False,
        "is_late": False,
        "status": "pending"
    },
    {
        "id": 2,
        "assignment_title": "第6章 数据库设计",
        "student_name": "李华",
        "student_id": "20210002",
        "class_name": "计算机2101",
        "course_name": "工程实践4（2025春）",
        "submitted_at": "2025-05-25 18:45",
        "deadline": "2025-05-25 23:59",
        "file_url": "/uploads/20210002_db_design.pdf",
        "text_content": None,
        "version_no": 2,
        "allow_resubmit": True,
        "is_late": False,
        "status": "pending"
    },
    {
        "id": 3,
        "assignment_title": "第5章 系统架构设计",
        "student_name": "王芳",
        "student_id": "20210003",
        "class_name": "软件工程2101",
        "course_name": "工程实践4（2025春）",
        "submitted_at": "2025-05-24 00:12",
        "deadline": "2025-05-23 23:59",
        "file_url": "/uploads/20210003_arch.pdf",
        "text_content": None,
        "version_no": 1,
        "allow_resubmit": False,
        "is_late": True,
        "status": "pending"
    },
    {
        "id": 4,
        "assignment_title": "第7章 软件需求规格说明书",
        "student_name": "赵强",
        "student_id": "20210004",
        "class_name": "计算机2102",
        "course_name": "工程实践4（2025春）",
        "submitted_at": "2025-05-26 15:20",
        "deadline": "2025-05-27 23:59",
        "file_url": None,
        "text_content": "## 需求分析\n\n### 功能需求\n\n1. 用户登录模块\n2. 数据管理模块\n3. 报表生成模块\n\n### 非功能需求\n\n- 响应时间 < 200ms\n- 并发用户数 > 1000",
        "version_no": 1,
        "allow_resubmit": False,
        "is_late": False,
        "status": "pending"
    },
    {
        "id": 5,
        "assignment_title": "第6章 数据库设计",
        "student_name": "刘敏",
        "student_id": "20210005",
        "class_name": "软件工程2101",
        "course_name": "工程实践4（2025春）",
        "submitted_at": "2025-05-25 22:18",
        "deadline": "2025-05-25 23:59",
        "file_url": "/uploads/20210005_db.pdf",
        "text_content": None,
        "version_no": 1,
        "allow_resubmit": False,
        "is_late": False,
        "status": "pending"
    }
]

mock_courses = [
    "全部课程",
    "工程实践4（2025春）",
    "工程实践3（2024秋）",
    "工程实践2（2024春）"
]

mock_classes = [
    "全部班级",
    "计算机2101",
    "计算机2102",
    "软件工程2101"
]

last_feedback = ""

class GradingState(rx.State):
    """批改页面状态管理"""
    submissions = mock_submissions
    selected_submission = None
    current_index = 0
    filters = {
        "course": "全部课程",
        "class_name": "全部班级",
        "time_filter": "all"
    }
    
    # 评分数据
    scores = {
        "attendance": "",
        "exam": "",
        "code": "",
        "pr": ""
    }
    overall_comment = ""
    dimension_comments = {
        "attendance": "",
        "exam": "",
        "code": "",
        "pr": ""
    }
    allow_resubmit = False
    
    filtered_submissions = mock_submissions
    show_markdown_preview = False
    last_feedback = ""

    @rx.var
    def pending_count(self):
        return len([s for s in self.filtered_submissions if s["status"] == "pending"])

    @rx.var
    def allow_resubmit_count(self):
        return len([s for s in self.filtered_submissions if s["allow_resubmit"]])

    def apply_filters(self):
        """应用筛选条件"""
        self.filtered_submissions = [
            s for s in self.submissions
            if (self.filters["course"] == "全部课程" or s["course_name"] == self.filters["course"])
            and (self.filters["class_name"] == "全部班级" or s["class_name"] == self.filters["class_name"])
        ]
        # 默认按截止时间升序排列
        self.filtered_submissions.sort(key=lambda x: x["deadline"])
        if self.filtered_submissions:
            self.select_submission(0)

    def select_submission(self, index):
        """选择要批改的作业"""
        if 0 <= index < len(self.filtered_submissions):
            self.current_index = index
            self.selected_submission = self.filtered_submissions[index]
            # 重置评分和评语
            self.scores = {"attendance": "", "exam": "", "code": "", "pr": ""}
            self.overall_comment = ""
            self.dimension_comments = {"attendance": "", "exam": "", "code": "", "pr": ""}
            self.allow_resubmit = self.selected_submission.get("allow_resubmit", False)

    def next_submission(self):
        """下一份作业"""
        if self.current_index < len(self.filtered_submissions) - 1:
            self.select_submission(self.current_index + 1)

    def prev_submission(self):
        """上一份作业"""
        if self.current_index > 0:
            self.select_submission(self.current_index - 1)

    def copy_last_feedback(self):
        """复制上一份评语"""
        if self.last_feedback:
            self.overall_comment = self.last_feedback

    def save_grading(self):
        """保存批改结果"""
        if not self.selected_submission:
            return
        
        # 保存当前评语作为"上一份评语"
        self.last_feedback = self.overall_comment
        
        # 模拟保存到数据库（实际应用中应调用 API）
        print(f"批改保存: {self.selected_submission['student_name']} - {self.scores}")
        print(f"评语: {self.overall_comment}")
        print(f"允许二次提交: {self.allow_resubmit}")
        
        # 标记为已批改
        self.selected_submission["status"] = "graded"
        self.selected_submission["allow_resubmit"] = self.allow_resubmit
        
        # 自动触发通知（模拟）
        print(f"已通知学生: {self.selected_submission['student_name']}")
        
        # 记录审计日志（模拟）
        print(f"审计日志: 批改人=李老师, 时间={__import__('datetime').datetime.now()}, 学生={self.selected_submission['student_name']}, 分值={self.scores}, 允许重提={self.allow_resubmit}")
        
        # 自动跳转到下一份
        self.next_submission()

def filter_section():
    """筛选区域"""
    return rx.card(
        rx.vstack(
            rx.heading("筛选条件", size="sm", style={"font-weight": "bold"}),
            rx.hstack(
                rx.select(
                    mock_courses,
                    value=GradingState.filters["course"],
                    placeholder="选择课程",
                    on_change=lambda v: GradingState.set_filters(GradingState.filters | {"course": v}),
                    style={"flex": 1}
                ),
                rx.select(
                    mock_classes,
                    value=GradingState.filters["class_name"],
                    placeholder="选择班级",
                    on_change=lambda v: GradingState.set_filters(GradingState.filters | {"class_name": v}),
                    style={"flex": 1}
                ),
                rx.select(
                    ["全部时间", "截止时间升序", "提交时间降序"],
                    value=GradingState.filters["time_filter"],
                    placeholder="排序方式",
                    on_change=lambda v: GradingState.set_filters(GradingState.filters | {"time_filter": v}),
                    style={"flex": 1}
                ),
                rx.button(
                    "应用筛选",
                    on_click=GradingState.apply_filters,
                    color_scheme="blue"
                ),
                spacing="3",
                width="100%"
            ),
            spacing="4",
            padding="16px"
        ),
        style={"margin-bottom": "16px"}
    )

def queue_item(submission, index):
    """队列列表项"""
    is_selected = GradingState.current_index == index
    is_allow_resubmit = submission.get("allow_resubmit", False)
    is_late = submission.get("is_late", False)
    
    bg_color = "bg-amber-50 border-amber-200" if is_allow_resubmit else "bg-white border-gray-100"
    border_color = "border-blue-400" if is_selected else ""
    
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(submission["student_name"], style={"font-weight": "bold"}),
                rx.text(f"学号: {submission['student_id']}", style={"font-size": "12px", "color": "#666"}),
                rx.text(submission["class_name"], style={"font-size": "12px", "color": "#666"}),
                spacing="1",
                style={"flex": 1}
            ),
            rx.box(
                rx.text(submission["assignment_title"], style={"font-size": "12px", "color": "#888"}),
                rx.text(f"提交于 {submission['submitted_at']}", style={"font-size": "11px", "color": "#aaa"}),
                spacing="1",
                style={"flex": 1.5}
            ),
            rx.box(
                rx.cond(
                    is_allow_resubmit,
                    rx.badge("允许重提", color_scheme="amber", variant="outline"),
                    rx.cond(
                        is_late,
                        rx.badge("迟交", color_scheme="red", variant="outline"),
                        rx.badge("待批改", color_scheme="blue", variant="outline")
                    )
                ),
                style={"flex": "none"}
            ),
            spacing="4",
            padding="12px 16px"
        ),
        border=f"2px solid {('blue' if is_selected else 'gray')}",
        border_radius="8px",
        background=bg_color,
        cursor="pointer",
        on_click=lambda: GradingState.select_submission(index),
        _hover={"background": "#f8fafc"}
    )

def queue_section():
    """批改队列区域"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("批改队列", size="sm", style={"font-weight": "bold"}),
                rx.badge(f"待批改: {GradingState.pending_count}", color_scheme="blue"),
                rx.badge(f"允许重提: {GradingState.allow_resubmit_count}", color_scheme="amber"),
                justify="space-between",
                align="center",
                width="100%"
            ),
            rx.divider(),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        GradingState.filtered_submissions,
                        lambda s, i: queue_item(s, i)
                    ),
                    spacing="2"
                ),
                style={"height": "500px", "width": "100%"}
            ),
            spacing="3",
            padding="16px"
        ),
        style={"flex": 1, "min-width": "500px"}
    )

def score_input(label, dimension, max_score=100):
    """单个维度评分输入"""
    return rx.box(
        rx.hstack(
            rx.text(label, style={"width": "80px", "font-weight": "bold"}),
            rx.input(
                value=GradingState.scores[dimension],
                on_change=lambda v: GradingState.set_scores(GradingState.scores | {dimension: v}),
                placeholder=f"0-{max_score}",
                type="number",
                min=0,
                max=max_score,
                style={"width": "80px", "text-align": "center"}
            ),
            rx.text(f"/ {max_score}", style={"color": "#999"}),
            spacing="2",
            width="100%"
        )
    )

def dimension_comment(label, dimension):
    """分项评语输入"""
    return rx.box(
        rx.text(label, style={"font-weight": "bold", "margin-bottom": "4px"}),
        rx.textarea(
            value=GradingState.dimension_comments[dimension],
            on_change=lambda v: GradingState.set_dimension_comments(GradingState.dimension_comments | {dimension: v}),
            placeholder=f"请输入{label}改进建议（支持 Markdown）",
            rows=2,
            style={"width": "100%", "font-size": "13px"}
        ),
        spacing="2"
    )

def grading_section():
    """批改区域"""
    return rx.card(
        rx.vstack(
            rx.cond(
                GradingState.selected_submission,
                rx.fragment(
                    # 学生信息头部
                    rx.hstack(
                        rx.box(
                            rx.heading(GradingState.selected_submission["student_name"], size="lg", style={"font-weight": "bold"}),
                            rx.text(f"学号: {GradingState.selected_submission['student_id']} | {GradingState.selected_submission['class_name']}"),
                            spacing="1"
                        ),
                        rx.hstack(
                            rx.button(
                                "上一份",
                                on_click=GradingState.prev_submission,
                                disabled=GradingState.current_index == 0,
                                variant="outline"
                            ),
                            rx.text(f"{GradingState.current_index + 1} / {len(GradingState.filtered_submissions)}", style={"padding": "0 12px"}),
                            rx.button(
                                "下一份",
                                on_click=GradingState.next_submission,
                                disabled=GradingState.current_index == len(GradingState.filtered_submissions) - 1,
                                variant="outline"
                            ),
                            spacing="2"
                        ),
                        justify="space-between",
                        width="100%"
                    ),
                    rx.divider(),
                    
                    # 作业信息
                    rx.box(
                        rx.text("作业: " + GradingState.selected_submission["assignment_title"], style={"font-weight": "bold"}),
                        rx.hstack(
                            rx.text(f"课程: {GradingState.selected_submission['course_name']}"),
                            rx.text(f"版本: v{GradingState.selected_submission['version_no']}"),
                            rx.text(f"提交时间: {GradingState.selected_submission['submitted_at']}"),
                            rx.text(f"截止时间: {GradingState.selected_submission['deadline']}"),
                            spacing="4",
                            style={"font-size": "13px", "color": "#666"}
                        ),
                        spacing="2",
                        style={"padding": "12px", "background": "#f8fafc", "border-radius": "8px", "margin-bottom": "16px"}
                    ),
                    
                    # 提交内容预览
                    rx.box(
                        rx.heading("提交内容", size="sm", style={"font-weight": "bold", "margin-bottom": "12px"}),
                        rx.cond(
                            GradingState.selected_submission["file_url"],
                            rx.hstack(
                                rx.icon("file-text", size=24),
                                rx.link(
                                    GradingState.selected_submission["file_url"].split("/")[-1],
                                    href=GradingState.selected_submission["file_url"],
                                    style={"color": "#3b82f6", "font-weight": "medium"}
                                ),
                                spacing="2"
                            ),
                            rx.box(
                                rx.markdown(GradingState.selected_submission["text_content"]),
                                style={"border": "1px solid #e5e7eb", "padding": "12px", "border-radius": "8px", "max-height": "200px", "overflow-y": "auto"}
                            )
                        ),
                        spacing="2"
                    ),
                    rx.divider(),
                    
                    # 多维度评分
                    rx.box(
                        rx.heading("维度评分", size="sm", style={"font-weight": "bold", "margin-bottom": "12px"}),
                        rx.vstack(
                            score_input("出勤", "attendance", 15),
                            score_input("考试", "exam", 30),
                            score_input("代码", "code", 35),
                            score_input("PR", "pr", 20),
                            spacing="3"
                        ),
                        style={"padding": "12px", "background": "#f8fafc", "border-radius": "8px"}
                    ),
                    rx.divider(),
                    
                    # 评语输入
                    rx.box(
                        rx.hstack(
                            rx.heading("总体评语", size="sm", style={"font-weight": "bold"}),
                            rx.button(
                                "复制上一份评语",
                                on_click=GradingState.copy_last_feedback,
                                variant="outline",
                                size="sm",
                                style={"font-size": "12px"}
                            ),
                            justify="space-between",
                            width="100%",
                            style={"margin-bottom": "12px"}
                        ),
                        rx.hstack(
                            rx.textarea(
                                value=GradingState.overall_comment,
                                on_change=GradingState.set_overall_comment,
                                placeholder="请输入总体评语（支持 Markdown 格式）",
                                rows=4,
                                style={"flex": 1}
                            ),
                            rx.button(
                                "预览",
                                on_click=GradingState.toggle_show_markdown_preview,
                                variant="outline",
                                size="sm"
                            ),
                            spacing="3"
                        ),
                        rx.cond(
                            GradingState.show_markdown_preview,
                            rx.box(
                                rx.heading("预览", size="xs", style={"font-weight": "bold", "margin-bottom": "8px"}),
                                rx.markdown(GradingState.overall_comment),
                                style={"border": "1px solid #e5e7eb", "padding": "12px", "border-radius": "8px", "margin-top": "8px"}
                            )
                        ),
                        spacing="2"
                    ),
                    rx.divider(),
                    
                    # 分项改进建议
                    rx.box(
                        rx.heading("分项改进建议", size="sm", style={"font-weight": "bold", "margin-bottom": "12px"}),
                        rx.grid(
                            dimension_comment("出勤", "attendance"),
                            dimension_comment("考试", "exam"),
                            dimension_comment("代码", "code"),
                            dimension_comment("PR", "pr"),
                            columns=2,
                            spacing="4"
                        ),
                        spacing="2"
                    ),
                    rx.divider(),
                    
                    # 允许二次提交开关
                    rx.hstack(
                        rx.text("允许二次提交", style={"font-weight": "bold"}),
                        rx.switch(
                            is_checked=GradingState.allow_resubmit,
                            on_change=GradingState.set_allow_resubmit
                        ),
                        rx.text("勾选后学生可重新提交", style={"font-size": "13px", "color": "#666"}),
                        justify="space-between",
                        style={"padding": "12px", "background": "#fefce8", "border-radius": "8px"}
                    ),
                    rx.divider(),
                    
                    # 操作按钮
                    rx.hstack(
                        rx.button("保存并下一份", on_click=GradingState.save_grading, color_scheme="green"),
                        rx.button("保存", on_click=GradingState.save_grading, variant="outline"),
                        spacing="3",
                        justify="end"
                    ),
                    spacing="4"
                ),
                rx.box(
                    rx.icon("file-question", size=48, style={"color": "#ccc"}),
                    rx.text("请从左侧队列选择一份作业开始批改", style={"color": "#999"}),
                    spacing="4",
                    style={"text-align": "center", "padding": "100px 0"}
                )
            ),
            spacing="4",
            padding="20px",
            style={"flex": 2}
        )
    )

def grading_page():
    """教师端作业批改主页面"""
    return rx.box(
        # 顶部导航
        rx.box(
            rx.hstack(
                rx.heading("🎓 教师端 - 作业在线批改", size="lg", style={"font-weight": "bold"}),
                rx.box(
                    rx.text("李老师"),
                    rx.avatar(fallback="李"),
                    spacing="2",
                    style={"display": "flex", "align-items": "center", "gap": "12px"}
                ),
                justify="space-between",
                align="center"
            ),
            style={"background": "#1e40af", "color": "white", "padding": "16px 24px", "box-shadow": "0 2px 8px rgba(0,0,0,0.1)"}
        ),
        
        # 主体内容
        rx.box(
            rx.vstack(
                filter_section(),
                rx.hstack(
                    queue_section(),
                    grading_section(),
                    spacing="4",
                    style={"width": "100%"}
                ),
                spacing="4",
                padding="20px",
                style={"max-width": "1600px", "margin": "0 auto"}
            ),
            style={"min-height": "calc(100vh - 70px)", "background": "#f1f5f9"}
        ),
        style={"min-height": "100vh"}
    )

# 导出页面供 app.py 使用
if rx is not None:
    page = grading_page