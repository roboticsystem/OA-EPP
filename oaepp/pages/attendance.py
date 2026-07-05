"""课堂点名页面。"""
import datetime

try:
    import reflex as rx
except Exception:
    rx = None

attendance_page = None
if rx is not None:
    try:
        from states.attendance import AttendanceState
    except ImportError:
        from oaepp.states.attendance import AttendanceState

    try:
        from states.auth import AuthState
    except ImportError:
        from oaepp.states.auth import AuthState

    def _build_attendance_stats(records):
        return {
            "total": 0,
            "present": 0,
            "late": 0,
            "absent": 0,
            "rate": 0.0,
        }

    def _build_rollcall_window_info():
        return rx.cond(
            AttendanceState.rollcall_active,
            rx.cond(
                AttendanceState.confirm_deadline != "",
                50,
                0,
            ),
            0,
        ), rx.cond(
            AttendanceState.rollcall_active,
            "点名进行中",
            "未开启点名",
        )

    def _render_attendance_item(record):
        return rx.hstack(
            rx.text(record["student_no"], " ", record["full_name"], width="220px", no_of_lines=1),
            rx.text(
                rx.cond(record["status"] == "present", "出勤",
                    rx.cond(record["status"] == "late", "迟到",
                        rx.cond(record["status"] == "absent", "缺勤", record["status"]))),
                color=rx.cond(record["status"] == "present", "green",
                    rx.cond(record["status"] == "late", "orange",
                        rx.cond(record["status"] == "absent", "red", "gray"))),
                width="80px",
                weight="medium",
            ),
            rx.text(record.get("checkin_at", "未签到"), color="gray", size="2", no_of_lines=1),
            spacing="4",
            align="start",
            width="100%",
        )

    def attendance_page():
        title = rx.heading("课堂点名与考勤", size="2")
        user_label = rx.text(
            "当前用户: ", AuthState.current_full_name,
            " (", rx.cond(AuthState.current_role != "", AuthState.current_role, "访客"), ")",
            color="gray",
        )
        attendance_stats = _build_attendance_stats(AttendanceState.attendance_history)
        window_percent, window_status = _build_rollcall_window_info()

        control_panel = rx.box(
            rx.vstack(
                rx.text("点名控制", weight="bold", size="3"),
                rx.hstack(
                    rx.text("课程ID", width="72px", align_self="center"),
                    rx.input(
                        placeholder="请输入课程ID",
                        value=AttendanceState.current_course_id.to(str),
                        on_change=AttendanceState.set_current_course_id,
                        width="180px",
                    ),
                    rx.button("刷新数据", on_click=lambda: AttendanceState.load_attendance(), color_scheme="blue"),
                    spacing="3",
                ),
                rx.text(
                    "当前课程: ", AttendanceState.current_course_name,
                    color="gray",
                    size="2",
                ),
                rx.hstack(
                    rx.button("开始点名", on_click=lambda: AttendanceState.start_rollcall(), color_scheme="green"),
                    rx.button("确认签到", on_click=lambda: AttendanceState.confirm_attendance(), color_scheme="teal"),
                    spacing="3",
                ),
                rx.hstack(
                    rx.checkbox(
                        is_checked=AttendanceState.enable_geofence,
                        on_change=AttendanceState.toggle_geofence,
                        label="启用地理围栏辅助",
                    ),
                    spacing="4",
                    wrap="wrap",
                ),
                rx.cond(
                    AttendanceState.enable_geofence,
                    rx.input(
                        placeholder="可选：输入地理位置标签 / 坐标摘要",
                        value=AttendanceState.geo_hash,
                        on_change=AttendanceState.set_geo_hash,
                        width="100%",
                    ),
                    rx.box(),
                ),
                rx.text(AttendanceState.attendance_message, color="green", size="2"),
                rx.box(
                    rx.text("当前点名窗口：", weight="medium"),
                    rx.cond(
                        AttendanceState.confirm_deadline != "",
                        rx.text(AttendanceState.confirm_deadline, color="gray", size="2"),
                        rx.text("未开启点名", color="gray", size="2"),
                    ),
                ),
                rx.hstack(
                    rx.text("历史查询日期", width="96px", align_self="center"),
                    rx.input(
                        type="date",
                        value=AttendanceState.history_date,
                        on_change=AttendanceState.set_history_date,
                        width="180px",
                    ),
                    rx.button("查询历史", on_click=AttendanceState.load_history, color_scheme="blue"),
                    spacing="3",
                    wrap="wrap",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="20px",
            border="1px solid #e2e8f0",
            border_radius="16px",
            background="white",
            width="100%",
        )

        summary_panel = rx.box(
            rx.vstack(
                rx.text("出勤概览与规则", weight="bold", size="3"),
                    rx.hstack(
                        rx.box(
                            rx.vstack(
                                rx.text("出勤率", size="2", color="gray"),
                                rx.text(str(attendance_stats["rate"]), "%", size="6", weight="bold"),
                                spacing="1",
                            ),
                            padding="12px 16px",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            min_width="130px",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("出勤", size="2", color="gray"),
                                rx.text(str(attendance_stats["present"]), size="6", weight="bold"),
                                spacing="1",
                            ),
                            padding="12px 16px",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            min_width="110px",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("迟到", size="2", color="gray"),
                                rx.text(str(attendance_stats["late"]), size="6", weight="bold"),
                                spacing="1",
                            ),
                            padding="12px 16px",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            min_width="110px",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("缺勤", size="2", color="gray"),
                                rx.text(str(attendance_stats["absent"]), size="6", weight="bold"),
                                spacing="1",
                            ),
                            padding="12px 16px",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            min_width="110px",
                        ),
                        spacing="3",
                        wrap="wrap",
                    ),
                rx.vstack(
                    rx.text("点名窗口进度", weight="medium"),
                    rx.progress(value=window_percent, max=100, color_scheme="green"),
                    rx.text(window_status, color="gray", size="2"),
                    spacing="1",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("得分规则", weight="medium"),
                        rx.text("• 出勤得分 = 出勤率 × 本项满分（15 分）", color="gray", size="2"),
                        rx.text("• 迟到按半额计入；缺勤按 0 分处理。", color="gray", size="2"),
                        rx.text("• 最终成绩以教师确认结果为准。", color="gray", size="2"),
                        spacing="1",
                    ),
                    padding="12px 16px",
                    border="1px solid #e2e8f0",
                    border_radius="12px",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="20px",
            border="1px solid #e2e8f0",
            border_radius="16px",
            background="white",
            width="100%",
        )

        student_panel = rx.box(
            rx.vstack(
                rx.text("学生名单 / 本次状态", weight="bold", size="3"),
                rx.text("教师可以手动选择学号标记学生出勤状态。", color="gray", size="2"),
                rx.hstack(
                    rx.input(
                        placeholder="请输入学生学号",
                        value=AttendanceState.selected_student_no,
                        on_change=AttendanceState.set_selected_student_no,
                        width="240px",
                    ),
                    rx.button("出勤", on_click=AttendanceState.mark_present, color_scheme="green"),
                    rx.button("迟到", on_click=AttendanceState.mark_late, color_scheme="orange"),
                    rx.button("缺勤", on_click=AttendanceState.mark_absent, color_scheme="red"),
                    spacing="3",
                    wrap="wrap",
                ),
                rx.vstack(
                    rx.foreach(
                        AttendanceState.student_list,
                        lambda item: rx.hstack(
                            rx.text(item["student_no"], " ", item["full_name"], width="240px", no_of_lines=1),
                            rx.text(item.get("class_name", ""), width="120px", color="gray", size="2"),
                            rx.text(item.get("status", "未签到"), width="100px", weight="medium"),
                            rx.text(item.get("checkin_at", "-"), color="gray", size="2"),
                            spacing="4",
                            align="start",
                            width="100%",
                        ),
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="20px",
            border="1px solid #e2e8f0",
            border_radius="16px",
            background="white",
            width="100%",
        )

        history_panel = rx.box(
            rx.vstack(
                rx.text(
                    rx.cond(AuthState.current_role == "teacher", "历史出勤记录", "我的历史出勤记录"),
                    weight="bold",
                    size="3",
                ),
                rx.text(
                    rx.cond(
                        AuthState.current_role == "teacher",
                        "教师端按课程和日期查看班级出勤记录。",
                        "仅显示当前登录学生的出勤明细。",
                    ),
                    color="gray",
                    size="2",
                ),
                rx.vstack(
                    rx.foreach(
                        AttendanceState.attendance_history,
                        _render_attendance_item,
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            padding="20px",
            border="1px solid #e2e8f0",
            border_radius="16px",
            background="white",
            width="100%",
        )

        return rx.center(
            rx.box(
                rx.vstack(
                    title,
                    user_label,
                    rx.divider(),
                    control_panel,
                    summary_panel,
                    rx.cond(
                        AuthState.current_role == "teacher",
                        student_panel,
                        rx.box(
                            rx.text(
                                "学生端请在教师开始点名后点击“确认签到”。",
                                color="gray",
                                size="2",
                            ),
                            padding="16px",
                            border="1px solid #e2e8f0",
                            border_radius="16px",
                            width="100%",
                        ),
                    ),
                    history_panel,
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
                max_width="1080px",
                width="100%",
                padding="28px",
                border_radius="18px",
                background="rgba(255,255,255,0.96)",
                box_shadow="0 24px 80px rgba(15,23,42,0.08)",
            ),
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)",
            padding="24px",
        )
