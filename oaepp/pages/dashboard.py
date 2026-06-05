"""F-S-040 学生任务完成状态看板页面"""

try:
    import reflex as rx
except Exception:
    rx = None

from states.dashboard import DashboardState


class DashboardPageState(DashboardState):
    """页面专用状态"""
    loaded: bool = False
    
    async def on_load(self):
        await self._load_all_data()
        self.loaded = True
    
    def handle_sort_select(self, value):
        """处理排序选择"""
        self.sort_label = value
        if value == "按完成率升序（落后置顶）":
            self.sort_order = "asc"
        else:
            self.sort_order = "desc"
        self._calculate_completion_rates()
    
    async def handle_course_select(self, value):
        """处理课程选择"""
        for course in self.courses:
            if f"{course['code']} - {course['name']}" == value:
                self.selected_course = course["id"]
                break
        await self.refresh_data()
    
    def handle_highlight_count_input(self, value):
        """处理高亮人数输入"""
        try:
            count = int(value)
            self.highlight_count = max(1, min(20, count))
        except (ValueError, TypeError):
            self.highlight_count = 1
        self._calculate_completion_rates()


def heatmap_table():
    """热力图表格"""
    return rx.cond(
        DashboardPageState.loaded,
        rx.html(DashboardPageState.heatmap_html),
        rx.text("加载中...")
    )


def bar_chart():
    """柱状图组件"""
    return rx.cond(
        DashboardPageState.loaded,
        rx.html(DashboardPageState.barchart_html),
        rx.text("加载中...")
    )


def dashboard_page():
    """Dashboard 页面入口"""
    if rx is None:
        return "Reflex not available"
    
    return rx.container(
        rx.vstack(
            # 页面标题
            rx.heading("进度看板 — 全班任务完成状态总览", size="2", margin_bottom="16px"),
            
            # 筛选区域
            rx.box(
                rx.hstack(
                    # 排序方式
                    rx.vstack(
                        rx.text("排序:", font_size="12px", font_weight="bold", margin_bottom="4px"),
                        rx.select(
                            ["按完成率升序（落后置顶）", "按完成率降序（优秀置顶）"],
                            value=DashboardPageState.sort_label,
                            on_change=DashboardPageState.handle_sort_select,
                            width="220px"
                        ),
                        spacing="2"
                    ),
                    
                    # 置顶人数
                    rx.vstack(
                        rx.text("置顶倒数前", font_size="12px", font_weight="bold", margin_bottom="4px"),
                        rx.hstack(
                            rx.input(
                                type="number",
                                value=DashboardPageState.highlight_count,
                                on_change=DashboardPageState.handle_highlight_count_input,
                                width="60px"
                            ),
                            rx.text("名", font_size="12px"),
                            spacing="2"
                        ),
                        spacing="2"
                    ),
                    
                    spacing="8",
                    justify="start"
                ),
                padding="16px",
                background_color="#f9fafb",
                border="1px solid #e5e7eb",
                border_radius="8px",
                margin_bottom="16px"
            ),
            
            # 图例
            rx.box(
                rx.hstack(
                    rx.text("图例:", font_size="12px", font_weight="bold", margin_right="12px"),
                    rx.hstack(
                        rx.box(width="12px", height="12px", background_color="#22c55e", border_radius="2px", margin_right="4px"),
                        rx.text("已提交（准时）", font_size="12px"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.box(width="12px", height="12px", background_color="#eab308", border_radius="2px", margin_right="4px"),
                        rx.text("迟交", font_size="12px"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.box(width="12px", height="12px", background_color="#ef4444", border_radius="2px", margin_right="4px"),
                        rx.text("未提交", font_size="12px"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.box(width="12px", height="12px", background_color="#9ca3af", border_radius="2px", margin_right="4px"),
                        rx.text("任务未发布", font_size="12px"),
                        spacing="2"
                    ),
                    rx.text("（点击单元格查看提交详情）", font_size="12px", color="#9ca3af"),
                    spacing="6",
                    justify="start"
                ),
                margin_bottom="16px"
            ),
            
            # 热力图区域
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("🔥", font_size="20px"),
                        rx.heading("学生 × 任务 完成状态热力图", size="3"),
                        spacing="2"
                    ),
                    heatmap_table(),
                    spacing="4"
                ),
                margin_bottom="24px",
                padding="16px",
                background_color="white",
                border="1px solid #e5e7eb",
                border_radius="8px"
            ),
            
            # 柱状图区域
            rx.box(
                rx.vstack(
                    rx.heading("各任务完成率趋势", size="3"),
                    rx.box(
                        bar_chart(),
                        padding="16px",
                        background_color="white",
                        border="1px solid #e5e7eb",
                        border_radius="8px"
                    ),
                    rx.hstack(
                        rx.text("共 ", font_size="12px", color="#6b7280"),
                        rx.text(DashboardPageState.students.length(), font_size="12px", color="#6b7280"),
                        rx.text(" 名学生 · ", font_size="12px", color="#6b7280"),
                        rx.text(DashboardPageState.assignments.length(), font_size="12px", color="#6b7280"),
                        rx.text(" 个活跃任务", font_size="12px", color="#6b7280"),
                        justify="center"
                    ),
                    spacing="4"
                ),
                padding="16px",
                background_color="white",
                border="1px solid #e5e7eb",
                border_radius="8px"
            ),
            
            spacing="6",
            padding="16px",
            width="100%"
        ),
        on_mount=DashboardPageState.on_load
    )