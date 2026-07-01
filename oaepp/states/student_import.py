"""F-T-005 学生名单导入 — StudentImportState

对应原型：prototype/admin_students.html（学生名单导入功能）
对应页面：oaepp/pages/student_import.py
对应需求：§5.9 F-T-005 学生名单导入

验收要点：
- 支持CSV格式导入，错误行高亮提示并可修正重导
- 自动校验学号唯一性/字段完整性/班级合法性
- 导入后自动创建账号（默认密码为学号）
- 发送激活邀请（邮件或首页公告）
- 支持增量导入和全量覆盖两种模式
- 日志导入记录时间/批次/操作人/记录数

协作规范：
- 独立 rx.State，不继承 GlobalState，不修改全局状态
- 通过 oaepp.database.db_sync() 使用公共数据库连接池
- 通过 AuthState 只读获取当前登录用户
"""

import csv
import datetime
import io
import json
from typing import Any, Dict, List, Optional, Tuple

try:
    import reflex as rx
except Exception:
    rx = None


def _hash_password(password: str) -> str:
    """使用 bcrypt 对密码进行哈希。"""
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _parse_csv(file_content: str) -> Tuple[List[Dict], List[str]]:
    """解析CSV文件内容。

    Args:
        file_content: CSV文件的文本内容

    Returns:
        (rows, errors): 解析出的行数据列表和错误信息列表
    """
    rows = []
    errors = []
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        required_fields = {"学号", "姓名", "班级", "课程"}

        if not required_fields.issubset(set(reader.fieldnames or [])):
            errors.append(f"CSV文件缺少必需字段，必需字段：{', '.join(required_fields)}")
            return rows, errors

        for row_num, row in enumerate(reader, start=2):
            student_no = row.get("学号", "").strip()
            full_name = row.get("姓名", "").strip()
            class_name = row.get("班级", "").strip()
            course = row.get("课程", "").strip()

            rows.append({
                "row_num": row_num,
                "student_no": student_no,
                "full_name": full_name,
                "class_name": class_name,
                "course": course,
                "errors": "",
                "valid": True,
            })
    except csv.Error as e:
        errors.append(f"CSV解析错误: {e}")
    except Exception as e:
        errors.append(f"文件读取错误: {e}")

    return rows, errors


def _validate_rows(rows: List[Dict], existing_student_nos: set, valid_classes: set) -> Tuple[List[Dict], int, int]:
    """校验所有行数据。

    Args:
        rows: 待校验的行数据列表
        existing_student_nos: 已存在的学号集合（用于唯一性校验）
        valid_classes: 合法班级集合（用于班级合法性校验）

    Returns:
        (rows, valid_count, invalid_count): 校验后的行数据、有效行数、无效行数
    """
    valid_count = 0
    invalid_count = 0
    seen_student_nos = set()

    for row in rows:
        row_errors = []

        student_no = row["student_no"]
        full_name = row["full_name"]
        class_name = row["class_name"]
        course = row["course"]

        if not student_no:
            row_errors.append("学号不能为空")
        elif not student_no.isdigit():
            row_errors.append("学号必须为数字")
        elif len(student_no) != 10:
            row_errors.append("学号必须为10位数字")

        if not full_name:
            row_errors.append("姓名不能为空")

        if not class_name:
            row_errors.append("班级不能为空")
        elif valid_classes and class_name not in valid_classes:
            row_errors.append(f"班级 '{class_name}' 不存在或不合法")

        if not course:
            row_errors.append("课程不能为空")

        if student_no and student_no in existing_student_nos:
            row_errors.append("学号已存在（重复）")

        if student_no and student_no in seen_student_nos:
            row_errors.append("学号在本次导入中重复")
        seen_student_nos.add(student_no)

        row["errors"] = ", ".join(row_errors) if row_errors else ""
        row["valid"] = len(row_errors) == 0

        if row["valid"]:
            valid_count += 1
        else:
            invalid_count += 1

    return rows, valid_count, invalid_count


def _get_existing_student_nos() -> set:
    """获取已存在的学号集合。"""
    try:
        from database import db_sync
    except ImportError:
        from oaepp.database import db_sync

    student_nos = set()
    with db_sync() as cur:
        cur.execute("SELECT student_no FROM users WHERE role = 'student'")
        for row in cur.fetchall():
            sno = row.get("student_no")
            if sno:
                student_nos.add(sno)
    return student_nos


def _get_valid_classes() -> set:
    """获取所有合法的班级名称集合。"""
    try:
        from database import db_sync
    except ImportError:
        from oaepp.database import db_sync

    classes = set()
    with db_sync() as cur:
        cur.execute("SELECT DISTINCT class_name FROM students WHERE class_name != ''")
        for row in cur.fetchall():
            class_name = row.get("class_name")
            if class_name:
                classes.add(class_name)
    return classes


def _get_course_id(course_name: str) -> Optional[int]:
    """根据课程名称获取课程ID，不存在则返回None。"""
    try:
        from database import db_sync
    except ImportError:
        from oaepp.database import db_sync

    with db_sync() as cur:
        cur.execute("SELECT id FROM courses WHERE name = %s", (course_name,))
        row = cur.fetchone()
        return row["id"] if row else None


def _create_course_if_not_exists(course_name: str, operator_id: int) -> int:
    """如果课程不存在则创建，返回课程ID。"""
    try:
        from database import db_sync, transaction_sync
    except ImportError:
        from oaepp.database import db_sync, transaction_sync

    with db_sync() as cur:
        cur.execute("SELECT id FROM courses WHERE name = %s", (course_name,))
        row = cur.fetchone()
        if row:
            return row["id"]

    with transaction_sync() as cur:
        cur.execute(
            "INSERT INTO courses (name, code, term, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, 'open', NOW(), NOW())",
            (course_name, course_name[:20], datetime.datetime.now().strftime("%Y-%m"),)
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        row = cur.fetchone()
        return row["id"] if row else 0


def _create_student_user(student_no: str, full_name: str, email: str = "") -> int:
    """创建学生用户账号，默认密码为学号。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    password_hash = _hash_password(student_no)

    with transaction_sync() as cur:
        cur.execute(
            "INSERT INTO users (role, student_no, email, password_hash, full_name, is_active, created_at, updated_at) "
            "VALUES ('student', %s, %s, %s, %s, TRUE, NOW(), NOW())",
            (student_no, email, password_hash, full_name,)
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        row = cur.fetchone()
        return row["id"] if row else 0


def _create_student_profile(user_id: int, class_name: str) -> None:
    """创建学生扩展信息记录。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    with transaction_sync() as cur:
        cur.execute(
            "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
            (user_id, class_name,)
        )


def _create_enrollment(student_user_id: int, course_id: int) -> None:
    """创建选课记录。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    with transaction_sync() as cur:
        cur.execute(
            "INSERT INTO enrollments (course_id, student_user_id, enrolled_at) "
            "VALUES (%s, %s, NOW())",
            (course_id, student_user_id,)
        )


def _send_notification(user_id: int, student_no: str) -> None:
    """发送激活邀请通知（首页公告）。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    title = "账号激活邀请"
    body = f"您的账号已创建成功！学号：{student_no}，初始密码为学号，请登录后及时修改密码。"

    with transaction_sync() as cur:
        cur.execute(
            "INSERT INTO notifications (user_id, title, body, category, is_read, created_at) "
            "VALUES (%s, %s, %s, 'system', FALSE, NOW())",
            (user_id, title, body,)
        )


def _log_import_batch(operator_id: int, mode: str, total_rows: int, success_rows: int, failed_rows: int, course_id: int = 0) -> None:
    """记录导入审计日志到 audit_logs 表。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    detail = {
        "import_mode": mode,
        "total_rows": total_rows,
        "success_rows": success_rows,
        "failed_rows": failed_rows,
        "batch_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with transaction_sync() as cur:
        cur.execute(
            """INSERT INTO audit_logs 
               (actor_user_id, action, target_type, target_id, detail_json, action_at)
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (
                operator_id,
                "student_import",
                "course",
                course_id,
                json.dumps(detail, ensure_ascii=False),
            )
        )


def _delete_existing_students(course_id: int) -> int:
    """全量覆盖模式下，删除指定课程的所有学生选课记录。"""
    try:
        from database import transaction_sync
    except ImportError:
        from oaepp.database import transaction_sync

    deleted_count = 0
    with transaction_sync() as cur:
        cur.execute(
            """SELECT student_user_id FROM enrollments WHERE course_id = %s""",
            (course_id,)
        )
        user_ids = [row["student_user_id"] for row in cur.fetchall()]

        if user_ids:
            placeholders = ",".join(["%s"] * len(user_ids))
            cur.execute(f"""DELETE FROM enrollments WHERE student_user_id IN ({placeholders}) AND course_id = %s""",
                       tuple(user_ids) + (course_id,))
            deleted_count = len(user_ids)

    return deleted_count


StudentImportState = None
if rx is not None:
    class StudentImportState(rx.State):
        """学生名单导入状态管理

        独立 State，不修改全局 GlobalState；通过 AuthState 只读获取当前用户。
        """

        import_mode: str = "incremental"
        file_content: str = ""
        parsed_rows: List[dict] = []
        file_errors: List[str] = []
        valid_count: int = 0
        invalid_count: int = 0
        is_loading: bool = False
        import_result: str = ""
        import_success: bool = False
        import_batch_id: Optional[int] = None
        operator_id: Optional[int] = None
        operator_name: str = ""

        def set_import_mode(self, mode: str):
            """设置导入模式：incremental（增量）或 overwrite（全量覆盖）"""
            self.import_mode = mode

        async def handle_file_upload(self, files: List[rx.UploadFile]):
            """处理文件上传并解析CSV"""
            self.file_content = ""
            self.parsed_rows = []
            self.file_errors = []
            self.valid_count = 0
            self.invalid_count = 0
            self.import_result = ""

            if not files:
                self.file_errors.append("请选择文件")
                return

            file = files[0]
            if not file.filename or not file.filename.endswith(".csv"):
                self.file_errors.append("只支持CSV格式文件")
                return

            try:
                content = await file.read()
                self.file_content = content.decode("utf-8-sig")
                rows, errors = _parse_csv(self.file_content)
                self.file_errors = errors

                if rows:
                    existing_nos = _get_existing_student_nos()
                    valid_classes = _get_valid_classes()
                    self.parsed_rows, self.valid_count, self.invalid_count = _validate_rows(
                        rows, existing_nos, valid_classes
                    )

            except Exception as e:
                self.file_errors.append(f"文件读取失败: {e}")

        async def handle_import(self):
            """执行导入操作"""
            if not self.parsed_rows:
                self.import_result = "请先上传并解析CSV文件"
                return

            if self.invalid_count > 0:
                self.import_result = f"存在 {self.invalid_count} 条无效记录，请修正后重新导入"
                return

            self.is_loading = True
            self.import_result = ""

            try:
                try:
                    from states.auth import AuthState
                except ImportError:
                    from oaepp.states.auth import AuthState

                auth = await self.get_state(AuthState)
                self.operator_id = getattr(auth, "current_user_id", None)
                self.operator_name = getattr(auth, "current_full_name", "")

            except Exception:
                self.operator_id = None
                self.operator_name = "系统"

            if self.operator_id is None:
                self.import_result = "未检测到登录用户，请先登录"
                self.is_loading = False
                return

            success_count = 0
            failed_count = 0
            total_rows = len(self.parsed_rows)

            try:
                courses_seen = {}
                existing_nos = _get_existing_student_nos()

                for row in self.parsed_rows:
                    if not row["valid"]:
                        failed_count += 1
                        continue

                    student_no = row["student_no"]
                    full_name = row["full_name"]
                    class_name = row["class_name"]
                    course_name = row["course"]

                    try:
                        if course_name not in courses_seen:
                            course_id = _get_course_id(course_name)
                            if course_id is None:
                                course_id = _create_course_if_not_exists(course_name, self.operator_id)
                            courses_seen[course_name] = course_id
                            if self.import_mode == "overwrite":
                                _delete_existing_students(course_id)
                        course_id = courses_seen[course_name]

                        user_id = None
                        if student_no not in existing_nos:
                            user_id = _create_student_user(student_no, full_name)
                            _create_student_profile(user_id, class_name)
                            _send_notification(user_id, student_no)
                            existing_nos.add(student_no)
                        else:
                            try:
                                from database import db_sync
                            except ImportError:
                                from oaepp.database import db_sync
                            with db_sync() as cur:
                                cur.execute("SELECT id FROM users WHERE student_no = %s", (student_no,))
                                row_data = cur.fetchone()
                                user_id = row_data["id"] if row_data else None

                        if user_id:
                            _create_enrollment(user_id, course_id)

                        success_count += 1

                    except Exception as e:
                        error_msg = f"导入失败: {e}"
                        row["errors"] = row["errors"] + ", " + error_msg if row["errors"] else error_msg
                        row["valid"] = False
                        failed_count += 1

                _log_import_batch(
                    self.operator_id,
                    self.import_mode,
                    total_rows,
                    success_count,
                    failed_count,
                    list(courses_seen.values())[0] if courses_seen else 0
                )

                if failed_count == 0:
                    self.import_result = f"导入成功！共导入 {success_count} 条记录"
                    self.import_success = True
                else:
                    self.import_result = f"部分导入成功：成功 {success_count} 条，失败 {failed_count} 条"
                    self.import_success = False

            except Exception as e:
                self.import_result = f"导入失败: {e}"
                self.import_success = False

            finally:
                self.is_loading = False

        def get_template_csv(self) -> str:
            """生成模板CSV内容供下载"""
            template = "\ufeff学号,姓名,班级,课程\n"
            template += "2024000001,张三,软件工程2024级1班,工程实践\n"
            template += "2024000002,李四,软件工程2024级1班,工程实践\n"
            template += "2024000003,王五,软件工程2024级2班,工程实践\n"
            return template

        async def download_template(self):
            """下载CSV模板"""
            return rx.download(
                data=self.get_template_csv().encode("utf-8"),
                filename="学生名单导入模板.csv"
            )