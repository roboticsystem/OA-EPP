"""F-T-005 学生名单导入状态管理

职责：
- CSV 文件上传与解析（支持中文/英文表头，编码检测）
- 数据验证（学号唯一性/字段完整性/班级合法性）
- 增量导入与全量覆盖两种模式
- 导入日志记录
- 发送激活邀请通知

数据库表：users, students, enrollments, notifications
"""

from __future__ import annotations

import csv
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.models import User, Student, Course, Enrollment, Notification
from oaepp.utils.helpers import validate_student_no


_HEADER_MAPPING = {
    "学号": "student_no",
    "student_no": "student_no",
    "studentno": "student_no",
    "student-id": "student_no",
    "student_id": "student_no",
    "id": "student_no",
    "姓名": "full_name",
    "name": "full_name",
    "full_name": "full_name",
    "班级": "class_name",
    "class": "class_name",
    "class_name": "class_name",
    "course_class": "class_name",
    "课程": "course_code",
    "course": "course_code",
    "course_code": "course_code",
    "课程代码": "course_code",
    "coursecode": "course_code",
}


def _normalize_header(header: str) -> str:
    return header.strip().lower()


def _detect_encoding(content: bytes) -> str:
    for encoding in ["utf-8-sig", "gbk", "gb2312", "utf-8"]:
        try:
            content.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _parse_csv(content: bytes) -> tuple[List[Dict[str, str]], str]:
    encoding = _detect_encoding(content)
    text = content.decode(encoding)

    lines = text.splitlines()
    if not lines:
        return [], ""

    header_row = lines[0]
    reader = csv.reader([header_row])
    raw_headers = next(reader)

    field_indices: Dict[str, int] = {}
    for idx, raw_header in enumerate(raw_headers):
        normalized = _normalize_header(raw_header)
        mapped = _HEADER_MAPPING.get(normalized)
        if mapped:
            field_indices[mapped] = idx

    required_fields = {"student_no", "full_name", "class_name", "course_code"}
    missing_fields = required_fields - set(field_indices.keys())
    if missing_fields:
        raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")

    rows: List[Dict[str, str]] = []
    for line_num, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        try:
            reader = csv.reader([line])
            row_data = next(reader)
            parsed: Dict[str, str] = {}
            for field, idx in field_indices.items():
                parsed[field] = row_data[idx].strip() if idx < len(row_data) else ""
            parsed["_line_num"] = str(line_num)
            rows.append(parsed)
        except Exception:
            raise ValueError(f"第 {line_num} 行格式错误")

    return rows, encoding


def _hash_password(password: str) -> str:
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


StudentImportState = None

if rx is not None:
    class StudentImportState(rx.State):
        uploaded_file: str = ""
        parsed_rows: List[Dict[str, Any]] = []
        import_mode: str = "incremental"
        selected_course_id: int = 0
        courses: List[Dict[str, Any]] = []
        valid_classes: List[str] = []

        is_parsing: bool = False
        is_importing: bool = False
        parse_error: str = ""
        import_error: str = ""
        import_result: str = ""

        logs: List[Dict[str, Any]] = []
        logs_loading: bool = False

        @rx.var
        def has_data(self) -> bool:
            return len(self.parsed_rows) > 0

        @rx.var
        def has_errors(self) -> bool:
            return any(row.get("_errors") for row in self.parsed_rows)

        @rx.var
        def success_count(self) -> int:
            return sum(1 for row in self.parsed_rows if not row.get("_errors"))

        @rx.var
        def error_count(self) -> int:
            return sum(1 for row in self.parsed_rows if row.get("_errors"))

        def load_courses(self):
            try:
                with rx.session() as session:
                    courses = session.exec(
                        rx.select(Course.id, Course.code, Course.name)
                    ).all()
                    self.courses = [
                        {"id": c.id, "code": c.code, "name": c.name}
                        for c in courses
                    ]
                    if self.courses and not self.selected_course_id:
                        self.selected_course_id = self.courses[0]["id"]

                self.load_valid_classes()
            except Exception as e:
                self.parse_error = f"加载课程失败: {e}"

        def load_valid_classes(self):
            try:
                with rx.session() as session:
                    classes = session.exec(
                        rx.select(Student.class_name).distinct()
                    ).all()
                    self.valid_classes = [c[0] for c in classes if c[0]]
            except Exception:
                self.valid_classes = []

        async def handle_upload(self, files: list[rx.UploadFile]):
            self.parse_error = ""
            self.parsed_rows = []
            self.uploaded_file = ""

            if not files:
                return

            file = files[0]
            self.uploaded_file = file.filename or ""
            self.is_parsing = True
            yield

            try:
                content = await file.read()
                rows, _ = _parse_csv(content)

                self.load_valid_classes()
                await self.validate_rows(rows)

            except ValueError as e:
                self.parse_error = str(e)
            except Exception as e:
                self.parse_error = f"文件解析失败: {e}"
            finally:
                self.is_parsing = False

        async def validate_rows(self, rows: List[Dict[str, str]]):
            existing_student_nos: set[str] = set()
            try:
                with rx.session() as session:
                    existing = session.exec(
                        rx.select(User.student_no).where(User.role == "student")
                    ).all()
                    existing_student_nos = {s for s in existing if s}
            except Exception:
                pass

            duplicate_nos: set[str] = set()
            seen_nos: set[str] = set()

            validated: List[Dict[str, Any]] = []
            for row in rows:
                errors: List[str] = []
                student_no = row.get("student_no", "").strip()
                full_name = row.get("full_name", "").strip()
                class_name = row.get("class_name", "").strip()
                course_code = row.get("course_code", "").strip()

                if not student_no:
                    errors.append("学号不能为空")
                elif not validate_student_no(student_no):
                    errors.append("学号格式不正确（应为10位数字）")

                if not full_name:
                    errors.append("姓名不能为空")

                if not class_name:
                    errors.append("班级不能为空")
                elif self.valid_classes and class_name not in self.valid_classes:
                    errors.append(f"班级 '{class_name}' 不存在")

                if not course_code:
                    errors.append("课程代码不能为空")

                if student_no and student_no in existing_student_nos:
                    errors.append("学号已存在")

                if student_no and student_no in seen_nos:
                    duplicate_nos.add(student_no)
                seen_nos.add(student_no)

                validated.append({
                    **row,
                    "_errors": errors,
                    "_valid": len(errors) == 0,
                })

            for row in validated:
                student_no = row.get("student_no", "").strip()
                if student_no in duplicate_nos and "学号重复" not in row["_errors"]:
                    row["_errors"].append("学号重复")
                    row["_valid"] = False

            self.parsed_rows = validated

        def update_row_field(self, row_idx: int, field: str, value: str):
            if 0 <= row_idx < len(self.parsed_rows):
                self.parsed_rows[row_idx][field] = value.strip()
                self.parsed_rows[row_idx]["_errors"] = []
                self.parsed_rows[row_idx]["_valid"] = True

        def set_import_mode(self, mode: str):
            self.import_mode = mode

        def set_selected_course(self, course_id: int):
            self.selected_course_id = course_id

        async def confirm_import(self):
            if not self.parsed_rows:
                self.import_error = "请先上传并解析文件"
                return

            if not self.selected_course_id:
                self.import_error = "请选择课程"
                return

            valid_rows = [r for r in self.parsed_rows if r.get("_valid")]
            if not valid_rows:
                self.import_error = "没有可导入的有效数据"
                return

            await self.execute_import(valid_rows)

        async def execute_import(self, valid_rows: List[Dict[str, Any]]):
            self.is_importing = True
            self.import_error = ""
            self.import_result = ""
            yield

            batch_no = str(uuid.uuid4())
            success_count = 0
            error_count = 0

            try:
                with rx.session() as session:
                    course = session.exec(
                        rx.select(Course).where(Course.id == self.selected_course_id)
                    ).first()
                    if not course:
                        raise ValueError("课程不存在")

                    if self.import_mode == "overwrite":
                        existing_enrollments = session.exec(
                            rx.select(Enrollment).where(
                                Enrollment.course_id == self.selected_course_id
                            )
                        ).all()
                        for enrollment in existing_enrollments:
                            student_user = session.exec(
                                rx.select(User).where(
                                    User.id == enrollment.student_user_id
                                )
                            ).first()
                            if student_user:
                                student_user.is_active = False
                                session.add(student_user)

                    existing_student_nos = set()
                    existing_users = session.exec(
                        rx.select(User.student_no, User.id).where(
                            User.role == "student"
                        )
                    ).all()
                    for s_no, u_id in existing_users:
                        if s_no:
                            existing_student_nos.add(s_no)

                    for row in valid_rows:
                        try:
                            student_no = row["student_no"]
                            full_name = row["full_name"]
                            class_name = row["class_name"]

                            if student_no in existing_student_nos:
                                user = session.exec(
                                    rx.select(User).where(
                                        User.student_no == student_no
                                    )
                                ).first()
                                if user:
                                    user.is_active = True
                                    user.full_name = full_name
                                    session.add(user)

                                    student = session.exec(
                                        rx.select(Student).where(
                                            Student.user_id == user.id
                                        )
                                    ).first()
                                    if student:
                                        student.class_name = class_name
                                        session.add(student)

                                    existing_enrollment = session.exec(
                                        rx.select(Enrollment).where(
                                            Enrollment.course_id == self.selected_course_id,
                                            Enrollment.student_user_id == user.id,
                                        )
                                    ).first()
                                    if not existing_enrollment:
                                        session.add(Enrollment(
                                            course_id=self.selected_course_id,
                                            student_user_id=user.id,
                                        ))
                                    success_count += 1
                                continue

                            password_hash = _hash_password(student_no)

                            user = User(
                                role="student",
                                student_no=student_no,
                                full_name=full_name,
                                password_hash=password_hash,
                                is_active=True,
                            )
                            session.add(user)
                            session.flush()

                            student = Student(
                                user_id=user.id,
                                class_name=class_name,
                            )
                            session.add(student)

                            enrollment = Enrollment(
                                course_id=self.selected_course_id,
                                student_user_id=user.id,
                            )
                            session.add(enrollment)

                            session.add(Notification(
                                user_id=user.id,
                                title="账号激活通知",
                                body=f"您的账号已创建，初始密码为您的学号：{student_no}。请登录后及时修改密码。",
                                category="system",
                            ))

                            success_count += 1
                        except Exception:
                            error_count += 1

                    session.exec(
                        """
                        INSERT INTO import_logs (batch_no, operator_user_id, import_mode, course_id, 
                        total_rows, success_rows, error_rows, file_name, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (batch_no, 1, self.import_mode, self.selected_course_id,
                         len(valid_rows), success_count, error_count,
                         self.uploaded_file, datetime.now())
                    )

                    session.commit()

                self.import_result = (
                    f"导入完成！成功: {success_count} 条, 失败: {error_count} 条, "
                    f"批次号: {batch_no[:8]}..."
                )
                self.parsed_rows = []
                self.uploaded_file = ""

            except Exception as e:
                self.import_error = f"导入失败: {e}"
            finally:
                self.is_importing = False
                self.load_import_logs()

        def load_import_logs(self):
            self.logs_loading = True
            try:
                with rx.session() as session:
                    logs = session.exec(
                        """
                        SELECT il.id, il.batch_no, il.import_mode, il.course_id, 
                               il.total_rows, il.success_rows, il.error_rows, 
                               il.file_name, il.created_at, c.code
                        FROM import_logs il
                        LEFT JOIN courses c ON il.course_id = c.id
                        ORDER BY il.created_at DESC
                        LIMIT 20
                        """
                    ).all()

                    self.logs = []
                    for log in logs:
                        self.logs.append({
                            "id": log.id,
                            "batch_no": log.batch_no[:8] + "...",
                            "import_mode": "增量导入" if log.import_mode == "incremental" else "全量覆盖",
                            "course_code": log.code or "",
                            "total_rows": log.total_rows,
                            "success_rows": log.success_rows,
                            "error_rows": log.error_rows,
                            "file_name": log.file_name,
                            "created_at": str(log.created_at) if log.created_at else "",
                        })
            except Exception:
                self.logs = []
            finally:
                self.logs_loading = False