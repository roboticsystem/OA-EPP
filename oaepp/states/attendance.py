"""F-S-052 课堂点名状态管理。

仅使用 SELECT / INSERT / UPDATE / DELETE 操作，不修改数据库结构。
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

try:
    from oaepp.constants import ATTENDANCE_STATUS
except ImportError:
    from constants import ATTENDANCE_STATUS

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

    # ── 数据与 UI 绑定方法 ────────────────────────────────────────

    async def load_attendance(self, user_id: int = 0) -> None:
        """加载当前用户 / 课堂考勤数据。"""
        if user_id:
            self.current_user_id = user_id

        current_user_id = self._resolve_rx_var(self.current_user_id, 0)
        current_role = self._resolve_rx_var(self.current_role, "")

        if current_user_id == 0 or current_role == "":
            current_user_id, current_role = self._get_auth_user_context()
            self.current_user_id = current_user_id
            self.current_role = current_role

        if current_user_id != 0 and self._resolve_rx_var(self.current_student_no, "") == "":
            self.current_student_no = self._load_student_no(current_user_id) or ""

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

    def _resolve_rx_var(self, value: Any, default: Any = None) -> Any:
        """Extract actual value from Reflex rx.Var-like state values."""
        if value is None:
            return default

        if isinstance(value, (str, int, float, bool)):
            return value

        try:
            if hasattr(value, "_value") and getattr(value, "_value", None) is not None:
                return value._value
            if hasattr(value, "value") and getattr(value, "value", None) is not None:
                return value.value
        except Exception:
            pass

        if hasattr(value, "_var_data") or hasattr(value, "_var_state") or hasattr(value, "_var_type"):
            return default

        return value

    def _get_auth_user_context(self) -> tuple[int, str]:
        """Read authentication state as plain Python values for business logic."""
        try:
            from oaepp.states.auth import AuthState
        except Exception:
            from states.auth import AuthState

        auth_user_id_var = getattr(AuthState, "current_user_id", 0)
        auth_role_var = getattr(AuthState, "current_role", "")

        raw_uid = self._resolve_rx_var(auth_user_id_var, 0)
        raw_role = self._resolve_rx_var(auth_role_var, "")

        uid = raw_uid if isinstance(raw_uid, int) else int(raw_uid) if isinstance(raw_uid, (float, bool)) else 0
        role = raw_role if isinstance(raw_role, str) else str(raw_role) if raw_role is not None else ""

        return uid, role

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
        if session_id:
            if self.session_id == 0:
                self.session_id = session_id
            elif session_id != self.session_id:
                self.attendance_message = "当前点名会话已过期，请刷新后重试。"
                return
        else:
            session_id = self.session_id

        rollcall_active = self._resolve_rx_var(self.rollcall_active, False)
        if self.session_id == 0 and not rollcall_active:
            self.attendance_message = "当前点名会话未开始，请先刷新或重新发起点名。"
            return

        current_user_id = self._resolve_rx_var(self.current_user_id, 0)
        current_role = self._resolve_rx_var(self.current_role, "")
        if current_user_id == 0:
            current_user_id, current_role = self._get_auth_user_context()
            self.current_user_id = current_user_id
            self.current_role = current_role

        if current_user_id == 0:
            self.attendance_message = "无法识别当前用户，请先登录。"

        now = datetime.datetime.now()

        if self.confirm_deadline is None:
            self.attendance_status = "present"
        elif now <= self.confirm_deadline:
            self.attendance_status = "present"
        else:
            self.attendance_status = "late"

        self.rollcall_active = False
        self._save_attendance(current_user_id, self.attendance_status)
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

        selected_student_no = self._resolve_rx_var(self.selected_student_no, "")
        if selected_student_no == "":
            self.attendance_message = "请先输入学号后再标记考勤。"
            return

        student_user_id = self._resolve_student_user_id(selected_student_no)
        if student_user_id is None:
            self.attendance_message = "未找到该学生学号。"
            return

        self._ensure_current_course()
        self._save_attendance(student_user_id, status)
        self.attendance_message = f"已为 {selected_student_no} 标记为 {status}。"
        self._load_student_list()
        self._load_attendance_history()

    # ── 内部数据库方法 ────────────────────────────────────────

    def _ensure_current_course(self) -> None:
        current_course_id = self._resolve_rx_var(self.current_course_id, 0)
        if current_course_id == 0 and self.courses:
            first = self.courses[0]
            current_course_id = first.get("id", 0) or 0
            self.current_course_id = current_course_id
            self.current_course_name = first.get("name", "") or ""
            return

        if current_course_id and self.courses:
            match = next((course for course in self.courses if course.get("id") == current_course_id), None)
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

        current_course_id = self._resolve_rx_var(self.current_course_id, 0)
        if current_course_id == 0:
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
                    (current_course_id, current_course_id),
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
        current_user_id = self._resolve_rx_var(self.current_user_id, 0)
        if current_user_id == 0:
            self.attendance_history = []
            return

        current_role = self._resolve_rx_var(self.current_role, "")
        is_teacher = current_role == "teacher"
        filters = ""
        params: List[Any] = []

        current_course_id = self._resolve_rx_var(self.current_course_id, 0)
        if is_teacher:
            if current_course_id == 0:
                self.attendance_history = []
                return
            filters = "WHERE ar.course_id = %s"
            params = [current_course_id]
        else:
            params = [current_user_id]

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
        current_course_id = self._resolve_rx_var(self.current_course_id, 0)
        if current_course_id == 0:
            self.attendance_message = "请先选择课程后再保存考勤。"
            return

        try:
            from oaepp.database import transaction_sync
        except Exception:
            from database import transaction_sync

        now = datetime.datetime.now()
        enable_geofence = self._resolve_rx_var(self.enable_geofence, False)
        geo_hash = self._resolve_rx_var(self.geo_hash, "")
        geo_value = geo_hash.strip() if enable_geofence and geo_hash else None

        try:
            with transaction_sync() as cur:
                cur.execute(
                    "SELECT id FROM attendance_records WHERE course_id = %s AND student_user_id = %s AND DATE(checkin_at) = %s",
                    (current_course_id, student_user_id, now.date()),
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
                        (current_course_id, student_user_id, status, now, geo_value),
                    )
        except Exception as e:
            self.attendance_message = f"保存考勤失败: {e}"
            return

    def _check_teacher(self) -> bool:
        current_role = self._resolve_rx_var(self.current_role, "")
        if current_role == "teacher":
            return True
        _, role = self._get_auth_user_context()
        return role == "teacher"
