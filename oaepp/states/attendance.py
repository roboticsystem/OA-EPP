"""F-S-052 课堂点名状态管理。

仅使用 SELECT / INSERT / UPDATE / DELETE 操作，不修改数据库结构。
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from oaepp.constants import ATTENDANCE_STATUS

try:
    import reflex as rx  # noqa: F401
except Exception:
    rx = None


class AttendanceState(rx.State if rx is not None else object):
    session_id: int = 0
    confirm_deadline: Optional[datetime.datetime] = None
    attendance_status: str = "pending"
    current_user_id: int = 0
    current_role: str = ""
    current_course_id: int = 0
    current_course_name: str = ""
    current_student_no: str = ""
    selected_student_no: str = ""
    enable_geofence: bool = False
    geo_hash: str = ""
    attendance_message: str = ""
    student_list: List[Dict[str, Any]] = []
    attendance_history: List[Dict[str, Any]] = []
    history_date: str = ""
    courses: List[Dict[str, Any]] = []
    rollcall_active: bool = False

    def __init__(self):
        self.session_id = 0
        self.confirm_deadline = None
        self.attendance_status = "pending"
        self.current_user_id = 0
        self.current_role = ""
        self.current_course_id = 0
        self.current_course_name = ""
        self.current_student_no = ""
        self.selected_student_no = ""
        self.enable_geofence = False
        self.geo_hash = ""
        self.attendance_message = ""
        self.student_list = []
        self.attendance_history = []
        self.history_date = ""
        self.courses = []
        self.rollcall_active = False

    # ── 数据与 UI 绑定方法 ────────────────────────────────────────

    async def load_attendance(self, user_id: int = 0) -> None:
        """加载当前用户 / 课堂考勤数据。"""
        if user_id:
            self.current_user_id = user_id

        if not self.current_user_id or not self.current_role:
            try:
                from oaepp.states.auth import AuthState
            except Exception:
                from states.auth import AuthState
            self.current_user_id = getattr(AuthState, "current_user_id", 0) or 0
            self.current_role = getattr(AuthState, "current_role", "") or ""

        if self.current_user_id and not self.current_student_no:
            self.current_student_no = self._load_student_no(self.current_user_id) or ""

        self._load_courses()
        self._ensure_current_course()
        self._load_student_list()
        self._load_attendance_history()
        self.attendance_message = "考勤数据已刷新"

    def set_current_course_id(self, course_id: str) -> None:
        """通过输入值设置当前课程 ID。"""
        try:
            self.current_course_id = int(course_id)
        except (TypeError, ValueError):
            self.current_course_id = 0
        self._ensure_current_course()
        self._load_student_list()

    def set_selected_student_no(self, student_no: str) -> None:
        self.selected_student_no = student_no.strip()

    def set_geo_hash(self, geo_hash: str) -> None:
        self.geo_hash = geo_hash.strip()

    def toggle_geofence(self, checked: Optional[bool] = None) -> None:
        if checked is None:
            self.enable_geofence = not self.enable_geofence
        else:
            self.enable_geofence = bool(checked)

    async def start_rollcall(self, duration_seconds: int = 60) -> None:
        """教师开启点名会话，默认 60 秒窗口。"""
        self._ensure_current_course()
        self.session_id = int(datetime.datetime.now().timestamp())
        self.confirm_deadline = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
        self.attendance_status = "pending"
        self.rollcall_active = True
        self.attendance_message = f"点名已开始，{duration_seconds} 秒内可签到。"

    async def confirm_attendance(self, session_id: int = 0) -> None:
        """学生端确认签到；超过截止时间自动标记迟到。"""
        if not session_id:
            session_id = self.session_id

        if session_id != self.session_id or not self.rollcall_active:
            self.attendance_message = "当前点名会话已过期，请刷新后重试。"
            return

        if not self.current_user_id:
            try:
                from oaepp.states.auth import AuthState
            except Exception:
                from states.auth import AuthState
            self.current_user_id = getattr(AuthState, "current_user_id", 0) or 0
            self.current_role = getattr(AuthState, "current_role", "") or ""

        if not self.current_user_id:
            self.attendance_message = "无法识别当前用户，请先登录。"
            return

        now = datetime.datetime.now()
        if self.confirm_deadline is None:
            self.attendance_status = "absent"
        elif now <= self.confirm_deadline:
            self.attendance_status = "present"
        else:
            self.attendance_status = "late"

        self.rollcall_active = False
        self._save_attendance(self.current_user_id, self.attendance_status)
        self.attendance_message = f"签到已记录：{self.attendance_status}" if self.attendance_status != "absent" else "已记录缺勤。"
        self._load_attendance_history()
        self._load_student_list()

    async def mark_present(self) -> None:
        await self._teacher_mark("present")

    async def mark_late(self) -> None:
        await self._teacher_mark("late")

    async def mark_absent(self) -> None:
        await self._teacher_mark("absent")

    async def load_history(self) -> None:
        """按日期刷新历史出勤记录。"""
        self._load_attendance_history()
        self.attendance_message = "历史记录已更新"

    def set_history_date(self, date_text: str) -> None:
        """设置用于查询的出勤日期。"""
        self.history_date = date_text.strip()

    async def _teacher_mark(self, status: str) -> None:
        if status not in ATTENDANCE_STATUS:
            self.attendance_message = "无效的考勤状态。"
            return

        if not self.selected_student_no:
            self.attendance_message = "请先输入学号后再标记考勤。"
            return

        student_user_id = self._resolve_student_user_id(self.selected_student_no)
        if not student_user_id:
            self.attendance_message = "未找到该学生学号。"
            return

        self._ensure_current_course()
        self._save_attendance(student_user_id, status)
        self.attendance_message = f"已为 {self.selected_student_no} 标记为 {status}。"
        self._load_student_list()
        self._load_attendance_history()

    # ── 内部数据库方法 ────────────────────────────────────────

    def _ensure_current_course(self) -> None:
        if self.current_course_id == 0 and self.courses:
            first = self.courses[0]
            self.current_course_id = first.get("id", 0) or 0
            self.current_course_name = first.get("name", "") or ""
            return

        if self.current_course_id and self.courses:
            match = next((course for course in self.courses if course.get("id") == self.current_course_id), None)
            if match:
                self.current_course_name = match.get("name", "") or ""
            else:
                self.current_course_name = ""

    def _load_student_no(self, user_id: int) -> Optional[str]:
        try:
            from oaepp.database import db_sync
        except Exception:
            from database import db_sync

        try:
            with db_sync() as cur:
                cur.execute(
                    "SELECT student_no FROM users WHERE id = %s AND role = 'student'",
                    (user_id,),
                )
                row = cur.fetchone()
                return row.get("student_no") if row else None
        except Exception:
            return None

    def _resolve_student_user_id(self, student_no: str) -> Optional[int]:
        try:
            from oaepp.database import db_sync
        except Exception:
            from database import db_sync

        try:
            with db_sync() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                    (student_no,),
                )
                row = cur.fetchone()
                return int(row["id"]) if row else None
        except Exception:
            return None

    def _load_courses(self) -> None:
        try:
            from oaepp.database import db_sync
        except Exception:
            from database import db_sync

        try:
            with db_sync() as cur:
                cur.execute("SELECT id, code, name FROM courses ORDER BY code ASC")
                rows = cur.fetchall() or []

            self.courses = [
                {
                    "id": int(row["id"]),
                    "code": row.get("code", ""),
                    "name": row.get("name", ""),
                }
                for row in rows
            ]
        except Exception:
            self.courses = []

    def _load_student_list(self) -> None:
        if not self._check_teacher():
            self.student_list = []
            return

        if self.current_course_id == 0:
            self.student_list = []
            return

        try:
            from oaepp.database import db_sync
        except Exception:
            from database import db_sync

        try:
            with db_sync() as cur:
                cur.execute(
                    """
                    SELECT u.id AS user_id,
                           u.student_no,
                           u.full_name,
                           s.class_name,
                           ar.status,
                           ar.checkin_at
                    FROM users u
                    JOIN students s ON s.user_id = u.id
                    LEFT JOIN attendance_records ar
                        ON ar.student_user_id = s.user_id
                        AND ar.course_id = %s
                        AND ar.checkin_at = (
                            SELECT MAX(checkin_at)
                            FROM attendance_records
                            WHERE student_user_id = s.user_id AND course_id = %s
                        )
                    WHERE u.role = 'student'
                    ORDER BY u.student_no ASC
                    """,
                    (self.current_course_id, self.current_course_id),
                )
                rows = cur.fetchall() or []

            self.student_list = [
                {
                    "user_id": int(row["user_id"]),
                    "student_no": row.get("student_no", ""),
                    "full_name": row.get("full_name", ""),
                    "class_name": row.get("class_name", ""),
                    "status": row.get("status") or "未签到",
                    "checkin_at": row.get("checkin_at"),
                }
                for row in rows
            ]
        except Exception:
            self.student_list = []

    def _load_attendance_history(self) -> None:
        if not self.current_user_id:
            self.attendance_history = []
            return

        is_teacher = self.current_role == "teacher"
        filters = ""
        params: List[Any] = []

        if is_teacher:
            if self.current_course_id == 0:
                self.attendance_history = []
                return
            filters = "WHERE ar.course_id = %s"
            params = [self.current_course_id]
        else:
            filters = "WHERE ar.student_user_id = %s"
            params = [self.current_user_id]

        if self.history_date:
            filters += " AND DATE(ar.checkin_at) = %s"
            params.append(self.history_date)

        try:
            from oaepp.database import db_sync
        except Exception:
            from database import db_sync

        try:
            with db_sync() as cur:
                cur.execute(
                    f"""
                    SELECT ar.id, ar.course_id, ar.student_user_id, ar.status, ar.checkin_at, ar.geo_hash,
                           c.code AS course_code, c.name AS course_name,
                           u.student_no AS student_no, u.full_name AS student_name
                    FROM attendance_records ar
                    LEFT JOIN courses c ON c.id = ar.course_id
                    LEFT JOIN users u ON u.id = ar.student_user_id
                    {filters}
                    ORDER BY ar.checkin_at DESC
                    """,
                    tuple(params),
                )
                rows = cur.fetchall() or []

            self.attendance_history = [
                {
                    "id": int(row["id"]),
                    "course_id": int(row["course_id"]),
                    "course_code": row.get("course_code", ""),
                    "course_name": row.get("course_name", ""),
                    "student_no": row.get("student_no", ""),
                    "student_name": row.get("student_name", ""),
                    "status": row.get("status", ""),
                    "checkin_at": row.get("checkin_at"),
                    "geo_hash": row.get("geo_hash", ""),
                }
                for row in rows
            ]
        except Exception:
            self.attendance_history = []

    def _save_attendance(self, student_user_id: int, status: str) -> None:
        if status not in ATTENDANCE_STATUS:
            return

        self._ensure_current_course()
        if self.current_course_id == 0:
            self.attendance_message = "请先选择课程后再保存考勤。"
            return

        try:
            from oaepp.database import transaction_sync
        except Exception:
            from database import transaction_sync

        now = datetime.datetime.now()
        geo_value = self.geo_hash.strip() if self.enable_geofence and self.geo_hash else None

        try:
            with transaction_sync() as cur:
                cur.execute(
                    "SELECT id FROM attendance_records WHERE course_id = %s AND student_user_id = %s AND DATE(checkin_at) = %s",
                    (self.current_course_id, student_user_id, now.date()),
                )
                row = cur.fetchone()
                if row:
                    record_id = int(row["id"])
                    cur.execute(
                        "UPDATE attendance_records SET status = %s, checkin_at = %s, geo_hash = %s WHERE id = %s",
                        (status, now, geo_value, record_id),
                    )
                else:
                    cur.execute(
                        "INSERT INTO attendance_records (course_id, student_user_id, status, checkin_at, geo_hash) VALUES (%s, %s, %s, %s, %s)",
                        (self.current_course_id, student_user_id, status, now, geo_value),
                    )
        except Exception as e:
            self.attendance_message = f"保存考勤失败: {e}"
            return

    def _check_teacher(self) -> bool:
        if self.current_role == "teacher":
            return True
        try:
            from oaepp.states.auth import AuthState
        except Exception:
            from states.auth import AuthState
        role = getattr(AuthState, "current_role", "") or ""
        return role == "teacher"
