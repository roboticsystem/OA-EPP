try:
    import reflex as rx
except Exception:
    rx = None

# --- 状态管理 (State) ---
if rx is not None:
    class GradingState(rx.State):
        """批改页面的状态管理，包含模拟数据和交互逻辑"""

        # 1. 模拟的批改队列数据（默认已按截止时间升序排序）
        queue: list[dict[str, str | bool]] = [
            {"id": "task_001", "student": "张三", "course": "Python进阶", "class_name": "计科一班",
             "deadline": "2026-06-10", "submit_time": "2026-06-08", "allowed_resubmit": False, "status": "待批改"},
            {"id": "task_002", "student": "李四", "course": "数据结构", "class_name": "软工二班",
             "deadline": "2026-06-11", "submit_time": "2026-06-09", "allowed_resubmit": True, "status": "已打回重做"},
            {"id": "task_003", "student": "王五", "course": "Python进阶", "class_name": "计科一班",
             "deadline": "2026-06-12", "submit_time": "2026-06-10", "allowed_resubmit": False, "status": "待批改"},
        ]

        # 2. 当前选中批改的作业
        selected_id: str = ""

        # 3. 批改表单数据
        score_attendance: str = ""
        score_exam: str = ""
        score_code: str = ""
        score_pr: str = ""
        general_comment: str = ""
        improvement_suggestion: str = ""
        allow_resubmit: bool = False

        # 4. 快捷操作缓存（上一份评语）
        prev_general_comment: str = "作业完成度很高，代码规范良好。"
        prev_improvement_suggestion: str = "建议在第45行增加异常捕获（try-except）机制，以防空指针错误。"

        # ==========================================
        # 修复：手动定义 Setter 方法，防止 Reflex 自动生成失败
        # ==========================================
        def set_score_attendance(self, value: str):
            self.score_attendance = value

        def set_score_exam(self, value: str):
            self.score_exam = value

        def set_score_code(self, value: str):
            self.score_code = value

        def set_score_pr(self, value: str):
            self.score_pr = value

        def set_general_comment(self, value: str):
            self.general_comment = value

        def set_improvement_suggestion(self, value: str):
            self.improvement_suggestion = value

        def set_allow_resubmit(self, value: bool):
            self.allow_resubmit = value

        # ==========================================

        @rx.var
        def selected_task(self) -> dict:
            """获取当前选中的作业详情"""
            for item in self.queue:
                if item["id"] == self.selected_id:
                    return item
            return {}

        def select_task(self, task_id: str):
            """选中左侧队列中的任务"""
            self.selected_id = task_id
            # 切换作业时重置表单状态
            self.score_attendance = ""
            self.score_exam = ""
            self.score_code = ""
            self.score_pr = ""
            self.general_comment = ""
            self.improvement_suggestion = ""
            self.allow_resubmit = False

        def copy_prev_comments(self):
            """【快捷操作】复制上一份评语"""
            self.general_comment = self.prev_general_comment
            self.improvement_suggestion = self.prev_improvement_suggestion

        def submit_grading(self):
            """保存批改并触发后续联动"""
            if not self.selected_id:
                return rx.window_alert("请先选择一份作业！")

            # 1. 记录审计日志 (此处为模拟后端调用)
            # print(f"Audit Log: User=Teacher1, Task={self.selected_id}, Scores={self.score_attendance}/{self.score_exam}/{self.score_code}/{self.score_pr}, Resubmit={self.allow_resubmit}")

            # 2. 保存上一份评语以便下次使用
            self.prev_general_comment = self.general_comment
            self.prev_improvement_suggestion = self.improvement_suggestion

            # 3. 触发 F-S-030（成绩实时统计）与 F-S-031 状态更新的模拟事件，并发送站内通知
            return rx.window_alert("批改已保存！F-S-030/031状态已更新，学生已收到站内通知。")

# --- UI 组件库 ---
if rx is not None:
    def filter_bar() -> rx.Component:
        """过滤器组件"""
        return rx.hstack(
            rx.select(["所有课程", "Python进阶", "数据结构"], placeholder="课程筛选", width="100%"),
            rx.select(["所有班级", "计科一班", "软工二班"], placeholder="班级筛选", width="100%"),
            rx.select(["截止时间 (升序)", "提交时间 (降序)"], placeholder="排序方式", width="100%"),
            spacing="2",
            margin_bottom="4",
        )


    def queue_item(task: dict) -> rx.Component:
        """队列单项渲染，如果允许二次提交，则背景色改变以作区分"""
        return rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text(task["student"], font_weight="bold"),
                    rx.badge(task["course"], color_scheme="blue"),
                    justify="between",
                    width="100%",
                ),
                rx.text(f"截止: {task['deadline']}", font_size="sm", color="gray"),
                rx.text(f"提交: {task['submit_time']}", font_size="sm", color="gray"),
                width="100%",
                align_items="start",
            ),
            # 允许二次提交的任务，颜色显著不同（橘色边框/浅色背景示意）
            background_color=rx.cond(task["allowed_resubmit"], rx.color("orange", 2), rx.color("gray", 2)),
            border_color=rx.cond(task["allowed_resubmit"], rx.color("orange", 6), rx.color("gray", 4)),
            border_width="1px",
            width="100%",
            cursor="pointer",
            on_click=GradingState.select_task(task["id"]),
            _hover={"opacity": 0.8},
            margin_bottom="2"
        )


    def grading_workspace() -> rx.Component:
        """右侧主工作台：打分与评语区"""
        return rx.box(
            rx.cond(
                GradingState.selected_id == "",
                rx.center(rx.text("👈 请在左侧选择一份学生作业进行批改", color="gray"), height="100%"),
                rx.vstack(
                    # 学生信息头部
                    rx.heading(f"正在批改: {GradingState.selected_task['student']} 的作业", size="6"),
                    rx.divider(),

                    # 提交内容展示区（已修复：使用 code_block）
                    rx.card(
                        rx.vstack(
                            rx.text("提交内容预览", font_weight="bold"),
                            rx.code_block(
                                "print('Hello, World!')\ndef fibonacci(n):\n    return n",
                                language="python",
                                show_line_numbers=True,
                                width="100%",
                            ),
                            rx.link("📎 下载附件 (main.py)", href="#", color="blue"),
                            align_items="start",
                            width="100%"
                        ),
                        width="100%",
                        margin_bottom="4"
                    ),

                    # 按维度打分
                    rx.text("多维度打分", font_weight="bold"),
                    rx.grid(
                        rx.box(rx.text("出勤分"), rx.input(placeholder="0-10", value=GradingState.score_attendance,
                                                           on_change=GradingState.set_score_attendance)),
                        rx.box(rx.text("考试分"), rx.input(placeholder="0-40", value=GradingState.score_exam,
                                                           on_change=GradingState.set_score_exam)),
                        rx.box(rx.text("代码分"), rx.input(placeholder="0-30", value=GradingState.score_code,
                                                           on_change=GradingState.set_score_code)),
                        rx.box(rx.text("PR 质量分"), rx.input(placeholder="0-20", value=GradingState.score_pr,
                                                              on_change=GradingState.set_score_pr)),
                        columns="4",
                        spacing="4",
                        width="100%",
                        margin_bottom="4"
                    ),

                    # 评语填写区
                    rx.hstack(
                        rx.text("总体评语及改进建议", font_weight="bold"),
                        # 快捷按钮
                        rx.button("复制上一份评语", size="1", variant="soft", on_click=GradingState.copy_prev_comments),
                        justify="between",
                        width="100%"
                    ),
                    rx.text_area(placeholder="总体评语...", value=GradingState.general_comment,
                                 on_change=GradingState.set_general_comment, width="100%", min_height="80px"),

                    # Markdown 支持的改进建议
                    rx.text("分项改进建议 (支持 Markdown 预览):", font_size="sm"),
                    rx.text_area(placeholder="改进建议...", value=GradingState.improvement_suggestion,
                                 on_change=GradingState.set_improvement_suggestion, width="100%", min_height="80px"),
                    rx.cond(
                        GradingState.improvement_suggestion != "",
                        rx.box(rx.markdown(GradingState.improvement_suggestion), background_color=rx.color("blue", 2),
                               padding="2", border_radius="md", width="100%")
                    ),

                    # 允许二次提交开关
                    rx.hstack(
                        rx.checkbox("允许学生根据建议进行二次提交", checked=GradingState.allow_resubmit,
                                    on_change=GradingState.set_allow_resubmit),
                        margin_y="4"
                    ),

                    # 提交按钮
                    rx.button("保存批改并通知学生", color_scheme="green", size="3", width="100%",
                              on_click=GradingState.submit_grading),

                    width="100%",
                    align_items="start",
                )
            ),
            width="100%",
            height="100%",
            padding="4",
            border_left=f"1px solid {rx.color('gray', 4)}"
        )

# --- 主页面组装 ---
if rx is not None:
    @rx.page(route="/grading")
    def grading_page():
        return rx.container(
            rx.vstack(
                rx.heading("教师端 - 作业在线批改", size="8", margin_bottom="4"),

                # 页面采用左右两栏布局：30% 队列，70% 工作台
                rx.flex(
                    # 左侧：筛选器与批改队列
                    rx.box(
                        filter_bar(),
                        rx.vstack(
                            rx.foreach(GradingState.queue, queue_item),
                            width="100%",
                            overflow_y="auto",
                            height="75vh",
                        ),
                        width="30%",
                        padding_right="4",
                    ),

                    # 右侧：逐份在线批改工作台
                    rx.box(
                        grading_workspace(),
                        width="70%",
                    ),
                    width="100%",
                    direction="row",
                    align="stretch",
                ),
                width="100%",
                max_width="1200px",
            ),
            padding="4",
        )