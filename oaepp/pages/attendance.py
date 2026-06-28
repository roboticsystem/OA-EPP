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

    def _build_attendance_stats(records: list[dict]):
        total = len(records)
        present = sum(1 for item in records if str(item.get("status", "")).lower() == "present")
        late = sum(1 for item in records if str(item.get("status", "")).lower() == "late")
        absent = sum(1 for item in records if str(item.get("status", "")).lower() == "absent")
        rate = round(((present + late) / total) * 100, 1) if total else 0.0
        return {
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "rate": rate,
        }

    def _build_rollcall_window_info():
        if not AttendanceState.rollcall_active or not AttendanceState.confirm_deadline:
            return 0, "未开启点名"

        remaining_seconds = max(
            0,
            int((AttendanceState.confirm_deadline - datetime.datetime.now()).total_seconds()),
        )
        window_percent = max(0, min(100, int((remaining_seconds / 60) * 100)))
        return window_percent, f"{remaining_seconds}s 剩余"

    def _render_attendance_item(record: dict):
        status_color = {
            "present": "green",
            "late": "orange",
            "absent": "red",
        }.get(record.get("status", ""), "gray")

        meta = []
        if record.get("course_code") or record.get("course_name"):
            meta.append(record.get("course_code") or record.get("course_name"))
        if record.get("student_no") or record.get("student_name"):
            meta.append(f"{record.get('student_no','')} {record.get('student_name','')}".strip())
        label = " / ".join([part for part in meta if part]) or "-"

        time_text = record.get("checkin_at") or "未签到"
        geo_text = record.get("geo_hash") or ""
        if geo_text:
            time_text += f" · {geo_text}"

        return rx.hstack(
            rx.text(label, width="220px", no_of_lines=1),
            rx.text(record.get("status", "-"), color=status_color, width="80px", weight="medium"),
            rx.text(str(time_text), color="gray", size="sm", no_of_lines=1),
            spacing="4",
            align="start",
            width="100%",
        )

    def attendance_page():
        title = rx.heading("课堂点名与考勤", size="2")
        role_label = AuthState.current_role or "访客"
        user_label = rx.text(f"当前用户: {AuthState.current_full_name} ({role_label})", color="gray")
        attendance_stats = _build_attendance_stats(AttendanceState.attendance_history)
        window_percent, window_status = _build_rollcall_window_info()

        control_panel = rx.box(
            rx.vstack(
                rx.text("点名控制", weight="bold", size="md"),
                rx.hstack(
                    rx.text("课程ID", width="72px", align_self="center"),
                    rx.input(
                        placeholder="请输入课程ID",
                        value=str(AttendanceState.current_course_id or ""),
                        on_change=AttendanceState.set_current_course_id,
                        width="180px",
                    ),
                    rx.button("刷新数据", on_click=AttendanceState.load_attendance, color_scheme="blue"),
                    spacing="3",
                ),
                rx.text(
                    f"当前课程: {AttendanceState.current_course_name or '未选择'}",
                    color="gray",
                    size="sm",
                ),
                rx.hstack(
                    rx.button("开始点名", on_click=AttendanceState.start_rollcall, color_scheme="green"),
                    rx.button("确认签到", on_click=AttendanceState.confirm_attendance, color_scheme="teal"),
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
                rx.text(AttendanceState.attendance_message, color="green", size="sm"),
                rx.box(
                    rx.text("当前点名窗口：", weight="medium"),
                    rx.text(
                        str(AttendanceState.confirm_deadline) if AttendanceState.confirm_deadline else "未开启点名",
                        color="gray",
                        size="sm",
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
                rx.text("出勤概览与规则", weight="bold", size="md"),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("出勤率", size="sm", color="gray"),
                            rx.text(f"{attendance_stats['rate']}%", size="2xl", weight="bold"),
                            spacing="1",
                        ),
                        padding="12px 16px",
                        border="1px solid #e2e8f0",
                        border_radius="12px",
                        min_width="130px",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("出勤", size="sm", color="gray"),
                            rx.text(str(attendance_stats["present"]), size="2xl", weight="bold"),
                            spacing="1",
                        ),
                        padding="12px 16px",
                        border="1px solid #e2e8f0",
                        border_radius="12px",
                        min_width="110px",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("迟到", size="sm", color="gray"),
                            rx.text(str(attendance_stats["late"]), size="2xl", weight="bold"),
                            spacing="1",
                        ),
                        padding="12px 16px",
                        border="1px solid #e2e8f0",
                        border_radius="12px",
                        min_width="110px",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("缺勤", size="sm", color="gray"),
                            rx.text(str(attendance_stats["absent"]), size="2xl", weight="bold"),
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
                    rx.text(window_status, color="gray", size="sm"),
                    spacing="1",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("得分规则", weight="medium"),
                        rx.text("• 出勤得分 = 出勤率 × 本项满分（15 分）", color="gray", size="sm"),
                        rx.text("• 迟到按半额计入；缺勤按 0 分处理。", color="gray", size="sm"),
                        rx.text("• 最终成绩以教师确认结果为准。", color="gray", size="sm"),
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
                rx.text("学生名单 / 本次状态", weight="bold", size="md"),
                rx.text("教师可以手动选择学号标记学生出勤状态。", color="gray", size="sm"),
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
                    *[
                        rx.hstack(
                            rx.text(f"{item['student_no']} {item['full_name']}", width="240px", no_of_lines=1),
                            rx.text(item.get("class_name", ""), width="120px", color="gray", size="sm"),
                            rx.text(item.get("status", "未签到"), width="100px", weight="medium"),
                            rx.text(str(item.get("checkin_at") or "-"), color="gray", size="sm"),
                            spacing="4",
                            align="start",
                            width="100%",
                        )
                        for item in AttendanceState.student_list
                    ],
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
                    "历史出勤记录" if AuthState.current_role == "teacher" else "我的历史出勤记录",
                    weight="bold",
                    size="md",
                ),
                rx.text(
                    "教师端按课程和日期查看班级出勤记录。" if AuthState.current_role == "teacher" else "仅显示当前登录学生的出勤明细。",
                    color="gray",
                    size="sm",
                ),
                rx.vstack(
                    *[_render_attendance_item(record) for record in AttendanceState.attendance_history],
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
                                size="sm",
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
