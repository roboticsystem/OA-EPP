"""F-T-012 教师权重调整 — admin_grades 页面

教师端成绩管理页面，包含：
- 四维度权重滑块与数字输入联动
- 实时差异热力图预览
- 历史方案回滚
- 审计日志查看
"""

try:
    import reflex as rx
except Exception:
    rx = None

admin_grades_page = None

if rx is not None:
    try:
        from states.teacher_grade_weight import GradeWeightState
    except ImportError:
        try:
            from oaepp.states.teacher_grade_weight import GradeWeightState
        except ImportError:
            GradeWeightState = None

    # ── 样式常量 ──
    CARD_STYLE = {
        "padding": "20px",
        "border_radius": "12px",
        "background": "white",
        "box_shadow": "0 2px 12px rgba(0,0,0,0.06)",
    }

    LABEL_STYLE = {"font_size": "14px", "font_weight": "500", "color": "#374151"}

    COLOR_MAP = {"up": "#22c55e", "down": "#ef4444", "unchanged": "#9ca3af"}

    LABEL_MAP = {
        "attendance": "出勤",
        "exam": "考试",
        "code": "代码提交",
        "pr": "PR贡献",
    }

    # ── 子组件 ──

    def _weight_slider_row(label: str, pct_field: str, raw_field: str, color: str):
        """单个维度的滑块 + 数字输入行"""
        pct_var = getattr(GradeWeightState, pct_field)
        return rx.hstack(
            rx.box(
                rx.text(label, **LABEL_STYLE),
                width="100px",
            ),
            rx.el.input(
                type="range",
                min=0,
                max=100,
                value=pct_var,
                on_change=getattr(GradeWeightState, f"set_{pct_field}_raw"),
                style={"width": "280px", "accent_color": color},
            ),
            rx.input(
                value=pct_var,
                on_change=getattr(GradeWeightState, f"set_{pct_field}_raw"),
                type_="number",
                min_=0,
                max_=100,
                width="70px",
                text_align="center",
            ),
            rx.text("%", color="gray"),
            spacing="3",
            align="center",
            width="100%",
        )

    def _heatmap_cell(student):
        """单个学生的热力图单元格"""
        return rx.hstack(
            rx.text(student["student_no"], font_size="12px", width="90px", color="#6b7280"),
            rx.text(student["full_name"], font_size="13px", width="80px"),
            rx.text(student["old_total"].to(str), font_size="12px", width="55px", color="#9ca3af"),
            rx.text("→", font_size="12px", color="#9ca3af"),
            rx.text(
                student["new_total"].to(str),
                font_size="12px", width="55px", font_weight="600",
            ),
            rx.text(
                rx.cond(
                    student["direction"] == "up", "▲ +",
                    rx.cond(student["direction"] == "down", "▼ ", "— "),
                ),
                student["diff"].to(str),
                font_size="12px", font_weight="bold", width="80px",
                color=rx.cond(
                    student["direction"] == "up", "#22c55e",
                    rx.cond(student["direction"] == "down", "#ef4444", "#9ca3af"),
                ),
            ),
            spacing="2", align="center", padding="4px 8px",
            border_radius="6px", width="100%",
        )

    def _history_card(item):
        """单个历史方案卡片"""
        return rx.hstack(
            rx.vstack(
                rx.text(item["modified_at"].to(str), font_size="13px", font_weight="500"),
                rx.text(
                    "出勤:", item["attendance"].to(str), "% 考试:", item["exam"].to(str),
                    "% 代码:", item["code"].to(str), "% PR:", item["pr"].to(str), "%",
                    font_size="12px", color="#6b7280",
                ),
                rx.text("修改人: ", item["modified_by"].to(str), font_size="11px", color="#9ca3af"),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.button(
                "回滚", size="2", color_scheme="orange",
                on_click=lambda: GradeWeightState.rollback_to(item["id"]),
            ),
            spacing="3", align="center", padding="12px 16px",
            border_radius="8px", background="#f9fafb",
            border="1px solid #e5e7eb", width="100%",
        )

    def _audit_log_row(log):
        """单条审计日志行"""
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(log["course_name"].to(str), font_weight="600", font_size="13px"),
                    rx.text("·", color="gray"),
                    rx.text(log["modified_by"].to(str), font_size="12px", color="#6b7280"),
                    rx.text("·", color="gray"),
                    rx.text(log["modified_at"].to(str), font_size="12px", color="#9ca3af"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.text("出勤:", font_size="12px", color="gray"),
                    rx.text(
                        log["old_weights"]["attendance"].to(str), "% → ",
                        log["new_weights"]["attendance"].to(str), "%",
                        font_size="12px",
                    ),
                    rx.text("考试:", font_size="12px", color="gray"),
                    rx.text(
                        log["old_weights"]["exam"].to(str), "% → ",
                        log["new_weights"]["exam"].to(str), "%",
                        font_size="12px",
                    ),
                    rx.text("代码:", font_size="12px", color="gray"),
                    rx.text(
                        log["old_weights"]["code"].to(str), "% → ",
                        log["new_weights"]["code"].to(str), "%",
                        font_size="12px",
                    ),
                    rx.text("PR:", font_size="12px", color="gray"),
                    rx.text(
                        log["old_weights"]["pr"].to(str), "% → ",
                        log["new_weights"]["pr"].to(str), "%",
                        font_size="12px",
                    ),
                    spacing="1",
                    flex_wrap="wrap",
                ),
                spacing="1",
                align="start",
            ),
            padding="10px 14px",
            border_radius="8px",
            background="white",
            border="1px solid #e5e7eb",
            width="100%",
        )

    # ── 主页面 ──

    def admin_grades_page():
        """教师端成绩管理页面 — 权重调整"""
        return rx.center(
            rx.box(
                rx.vstack(
                    # 页头
                    rx.hstack(
                        rx.heading("成绩管理 · 权重调整", size="6"),
                        rx.spacer(),
                        rx.text("F-T-012", color="gray", font_size="12px"),
                        spacing="4",
                        align="center",
                        width="100%",
                    ),
                    rx.divider(),
                    # 课程选择
                    rx.hstack(
                        rx.text("选择课程:", font_weight="500", font_size="14px"),
                        rx.select(
                            GradeWeightState.course_options,
                            placeholder="请选择课程",
                            value=GradeWeightState.selected_course_label,
                            on_change=GradeWeightState.set_selected_course_by_label,
                            width="400px",
                        ),
                        rx.button("刷新课程", on_click=GradeWeightState.load_courses, size="2", variant="outline"),
                        spacing="3",
                        align="center",
                    ),
                    # 状态消息
                    rx.cond(
                        GradeWeightState.status_message != "",
                        rx.box(
                            rx.text(
                                GradeWeightState.status_message,
                                color=rx.cond(
                                    GradeWeightState.status_type == "success",
                                    "#16a34a",
                                    rx.cond(
                                        GradeWeightState.status_type == "error",
                                        "#dc2626",
                                        "#6b7280",
                                    ),
                                ),
                                font_size="13px",
                            ),
                            padding="8px 14px",
                            border_radius="8px",
                            width="100%",
                        ),
                    ),
                    # 标签页切换
                    rx.hstack(
                        rx.button(
                            "权重调整",
                            on_click=lambda: GradeWeightState.set_active_tab("weights"),
                            variant=rx.cond(GradeWeightState.active_tab == "weights", "solid", "outline"),
                            size="2",
                        ),
                        rx.button(
                            "历史方案",
                            on_click=lambda: GradeWeightState.set_active_tab("history"),
                            variant=rx.cond(GradeWeightState.active_tab == "history", "solid", "outline"),
                            size="2",
                        ),
                        rx.button(
                            "审计日志",
                            on_click=lambda: GradeWeightState.set_active_tab("audit"),
                            variant=rx.cond(GradeWeightState.active_tab == "audit", "solid", "outline"),
                            size="2",
                        ),
                        spacing="2",
                    ),
                    # ── Tab 1: 权重调整 ──
                    rx.cond(
                        GradeWeightState.active_tab == "weights",
                        rx.vstack(
                            # 权重调整面板
                            rx.box(
                                rx.vstack(
                                    rx.text("评分维度权重配置", font_weight="600", font_size="15px"),
                                    rx.text(
                                        "拖动滑块或直接输入百分比，各维度自动归一化至合计 100%",
                                        font_size="12px",
                                        color="gray",
                                    ),
                                    _weight_slider_row("出勤 Attendance", "attendance_pct", "attendance_weight", "blue"),
                                    _weight_slider_row("考试 Exam", "exam_pct", "exam_weight", "green"),
                                    _weight_slider_row("代码提交 Code", "code_pct", "code_weight", "purple"),
                                    _weight_slider_row("PR贡献 PR", "pr_pct", "pr_weight", "orange"),
                                    rx.divider(),
                                    rx.hstack(
                                        rx.text(
                                            "合计: ", GradeWeightState.total_pct, "%",
                                            font_weight="bold",
                                            font_size="16px",
                                            color=rx.cond(
                                                GradeWeightState.is_balanced,
                                                "#16a34a",
                                                "#dc2626",
                                            ),
                                        ),
                                        rx.spacer(),
                                        rx.button(
                                            "重置默认",
                                            on_click=GradeWeightState.reset_to_default,
                                            color_scheme="gray",
                                            variant="outline",
                                            size="2",
                                        ),
                                        rx.button(
                                            "保存权重方案",
                                            on_click=GradeWeightState.save_weights,
                                            color_scheme="blue",
                                            loading=GradeWeightState.is_saving,
                                        ),
                                        spacing="3",
                                        align="center",
                                        width="100%",
                                    ),
                                    spacing="4",
                                    align="stretch",
                                ),
                                **CARD_STYLE,
                            ),
                            # 热力图预览
                            rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("差异热力图预览", font_weight="600", font_size="15px"),
                                        rx.spacer(),
                                        rx.cond(
                                            GradeWeightState.show_heatmap,
                                            rx.hstack(
                                                rx.text(
                                                    "▲ ", GradeWeightState.heatmap_up_count, "人涨分",
                                                    color="#22c55e",
                                                    font_size="12px",
                                                ),
                                                rx.text(
                                                    "▼ ", GradeWeightState.heatmap_down_count, "人降分",
                                                    color="#ef4444",
                                                    font_size="12px",
                                                ),
                                                rx.text(
                                                    "— ", GradeWeightState.heatmap_unchanged_count, "人不变",
                                                    color="#9ca3af",
                                                    font_size="12px",
                                                ),
                                                spacing="3",
                                            ),
                                        ),
                                        spacing="3",
                                        align="center",
                                        width="100%",
                                    ),
                                    rx.cond(
                                        GradeWeightState.show_heatmap,
                                        rx.cond(
                                            GradeWeightState.heatmap_data.length() > 0,
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.text("学号", font_size="12px", color="gray", width="90px"),
                                                    rx.text("姓名", font_size="12px", color="gray", width="80px"),
                                                    rx.text("原总分", font_size="12px", color="gray", width="55px"),
                                                    rx.text("", width="20px"),
                                                    rx.text("新总分", font_size="12px", color="gray", width="55px"),
                                                    rx.text("变化", font_size="12px", color="gray", width="80px"),
                                                    spacing="2",
                                                    padding="4px 8px",
                                                ),
                                                rx.divider(),
                                                rx.foreach(
                                                    GradeWeightState.heatmap_data,
                                                    _heatmap_cell,
                                                ),
                                                spacing="1",
                                                align="stretch",
                                                max_height="400px",
                                                overflow_y="auto",
                                                width="100%",
                                            ),
                                            rx.box(
                                                rx.text("暂无学生成绩数据", color="#9ca3af", font_size="13px", text_align="center"),
                                                padding="40px",
                                                width="100%",
                                            ),
                                        ),
                                        rx.box(
                                            rx.text("选择课程后调整权重即可实时预览热力图", color="#9ca3af", font_size="13px", text_align="center"),
                                            padding="40px",
                                            width="100%",
                                        ),
                                    ),
                                    spacing="3",
                                    align="stretch",
                                ),
                                **CARD_STYLE,
                            ),
                            spacing="4",
                            align="stretch",
                            width="100%",
                        ),
                    ),
                    # ── Tab 2: 历史方案 ──
                    rx.cond(
                        GradeWeightState.active_tab == "history",
                        rx.box(
                            rx.vstack(
                                rx.text("历史权重方案", font_weight="600", font_size="15px"),
                                rx.text(
                                    "可查看历史方案并一键回滚至任意版本",
                                    font_size="12px",
                                    color="gray",
                                ),
                                rx.cond(
                                    GradeWeightState.weight_history.length() > 0,
                                    rx.foreach(
                                        GradeWeightState.weight_history,
                                        _history_card,
                                    ),
                                    rx.text(
                                        "暂无历史方案记录",
                                        color="#9ca3af",
                                        font_size="13px",
                                    ),
                                ),
                                spacing="3",
                                align="stretch",
                            ),
                            **CARD_STYLE,
                        ),
                    ),
                    # ── Tab 3: 审计日志 ──
                    rx.cond(
                        GradeWeightState.active_tab == "audit",
                        rx.box(
                            rx.vstack(
                                rx.text("审计日志", font_weight="600", font_size="15px"),
                                rx.text(
                                    "记录每次权重修改（修改人、时间、旧值→新值），不可删除",
                                    font_size="12px",
                                    color="gray",
                                ),
                                rx.cond(
                                    GradeWeightState.audit_log.length() > 0,
                                    rx.foreach(
                                        GradeWeightState.audit_log,
                                        _audit_log_row,
                                    ),
                                    rx.text(
                                        "暂无审计日志",
                                        color="#9ca3af",
                                        font_size="13px",
                                    ),
                                ),
                                spacing="3",
                                align="stretch",
                            ),
                            **CARD_STYLE,
                        ),
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                max_width="900px",
                width="100%",
            ),
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
            padding="24px",
        )
