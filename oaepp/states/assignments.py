"""F-S-020 作业提交 — AssignmentsState

对应原型：prototype/assignments.html
对应页面：oaepp/pages/assignments.py
路由：/assignments （由 app.py 自动发现机制注册）

验收要点（来自需求文档）：
- 支持 pdf/docx/zip/py/c/cpp/txt 格式上传
- 截止前可提交，展示提交时间/文件大小/版本号
- 提交格式受后端配置控制

协作规范：
- 独立 rx.State，不修改全局状态
- 通过 oaepp.database.db_sync() / transaction_sync() 使用公共数据库连接
- 通过 GlobalState 只读获取当前登录用户
- 复用 deadline.py 的截止规则判定逻辑
"""
import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

try:
    from database import db_sync, transaction_sync
except ImportError:
    from oaepp.database import db_sync, transaction_sync

try:
    from states import GlobalState
except ImportError:
    from oaepp.states import GlobalState


# ── 配置常量 ──
ALLOWED_EXTENSIONS = {"pdf", "docx", "zip", "py", "c", "cpp", "txt"}
DEFAULT_ALLOWED_FORMATS = "pdf,docx,zip,py,c,cpp,txt"
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = os.environ.get("ASSIGNMENTS_UPLOAD_DIR", "oaepp_uploads")


# ── 辅助函数 ──
def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def _get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip(".")


class AssignmentsState(rx.State):
    """作业提交状态管理 — F-S-020"""

    # ── 作业列表 ──
    assignments: List[Dict[str, Any]] = []
    selected_assignment_id: str = ""

    # ── 提交表单 ──
    content_text: str = ""
    submit_message: str = ""
    submit_error: str = ""
    is_submitting: bool = False

    # ── 上传文件 ──
    uploaded_file_name: str = ""
    uploaded_file_size: int = 0
    uploaded_file_data: bytes = b""

    # ── 提交历史 ──
    submission_history: List[Dict[str, Any]] = []
    show_history: bool = False

    # ── 当前登录用户 ──
    current_student_no: str = ""
    current_student_name: str = ""

    def _get_student_no(self) -> str:
        """获取当前登录学生学号"""
        user = GlobalState.current_user  # type: ignore[attr-defined]
        if isinstance(user, dict) and user.get("student_no"):
            return user["student_no"]
        return self.current_student_no

    async def check_login(self):
        """检查登录状态，设置当前用户信息"""
        user = GlobalState.current_user  # type: ignore[attr-defined]
        if isinstance(user, dict) and user.get("student_no"):
            self.current_student_no = user["student_no"]
            self.current_student_name = user.get("full_name", "")
            await self.load_assignments()

    # ── 作业加载 ──
    async def load_assignments(self):
        """从数据库加载活跃作业列表"""
        try:
            with db_sync() as cur:
                cur.execute(
                    "SELECT id, title, description, deadline, "
                    "allowed_formats, max_file_size, is_active, created_at "
                    "FROM assignments WHERE is_active = 1 "
                    "ORDER BY deadline ASC"
                )
                rows = cur.fetchall()

            now = datetime.datetime.now()
            self.assignments = []
            for r in rows:
                deadline_str = r.get("deadline", "")
                deadline = None
                if deadline_str:
                    try:
                        deadline = datetime.datetime.strptime(
                            str(deadline_str), "%Y-%m-%d %H:%M"
                        )
                    except ValueError:
                        try:
                            deadline = datetime.datetime.strptime(
                                str(deadline_str), "%Y-%m-%dT%H:%M"
                            )
                        except ValueError:
                            pass

                is_past = now > deadline if deadline else False
                remaining = ""
                if deadline and not is_past:
                    diff = deadline - now
                    days = diff.days
                    hours = diff.seconds // 3600
                    if days > 0:
                        remaining = f"剩余 {days} 天"
                    elif hours > 0:
                        remaining = f"剩余 {hours} 小时"
                    else:
                        remaining = "即将截止"

                self.assignments.append({
                    "id": r["id"],
                    "title": r["title"],
                    "description": r.get("description", ""),
                    "deadline": str(deadline_str),
                    "allowed_formats": r.get("allowed_formats",
                                            DEFAULT_ALLOWED_FORMATS),
                    "max_file_size": r.get("max_file_size",
                                          DEFAULT_MAX_FILE_SIZE),
                    "is_active": r.get("is_active", 1),
                    "is_past_deadline": is_past,
                    "remaining": remaining,
                })
        except Exception as e:
            self.submit_error = f"加载作业列表失败: {e}"

    # ── 作业选择 ──
    def select_assignment(self, assignment_id: str):
        """选中作业，加载提交历史"""
        self.selected_assignment_id = assignment_id
        self.content_text = ""
        self.submit_message = ""
        self.submit_error = ""
        self.uploaded_file_name = ""
        self.uploaded_file_size = 0
        self.uploaded_file_data = b""
        self.show_history = False

    # ── 文件上传 ──
    async def handle_upload(self, files: list[rx.UploadFile]):
        """处理文件上传 — 仅暂存第一个文件，实际提交在 submit 时执行"""
        if not files:
            return
        file = files[0]
        self.uploaded_file_data = await file.read()
        self.uploaded_file_name = file.filename or "unknown"
        self.uploaded_file_size = len(self.uploaded_file_data)
        self.submit_error = ""

        # 客户端预览校验
        ext = _get_extension(self.uploaded_file_name)
        assignment = self._get_selected()
        if assignment:
            allowed = [f.strip().lower()
                       for f in assignment["allowed_formats"].split(",")]
            if ext not in allowed:
                self.submit_error = (
                    f"不支持的文件格式 '.{ext}'，"
                    f"允许：{', '.join(allowed)}"
                )
                self.uploaded_file_data = b""
                self.uploaded_file_name = ""
                self.uploaded_file_size = 0
                return

            max_size = assignment["max_file_size"]
            if self.uploaded_file_size > max_size:
                self.submit_error = (
                    f"文件大小 ({_format_file_size(self.uploaded_file_size)}) "
                    f"超过限制 ({_format_file_size(max_size)})"
                )
                self.uploaded_file_data = b""
                self.uploaded_file_name = ""
                self.uploaded_file_size = 0

    def clear_upload(self):
        """清除已上传文件"""
        self.uploaded_file_name = ""
        self.uploaded_file_size = 0
        self.uploaded_file_data = b""

    # ── 提交作业 ──
    async def submit_assignment(self):
        """提交作业 — F-S-020 核心逻辑"""
        student_no = self._get_student_no()
        if not student_no:
            self.submit_error = "请先登录"
            return

        if not self.selected_assignment_id:
            self.submit_error = "请先选择作业"
            return

        if not self.content_text.strip() and not self.uploaded_file_data:
            self.submit_error = "请填写文本内容或上传文件（至少一项）"
            return

        assignment = self._get_selected()
        if not assignment:
            self.submit_error = "作业不存在"
            return

        # 截止时间校验
        now = datetime.datetime.now()
        deadline_str = assignment.get("deadline", "")
        if deadline_str:
            try:
                deadline = datetime.datetime.strptime(
                    str(deadline_str), "%Y-%m-%d %H:%M"
                )
            except ValueError:
                try:
                    deadline = datetime.datetime.strptime(
                        str(deadline_str), "%Y-%m-%dT%H:%M"
                    )
                except ValueError:
                    deadline = None

            if deadline and now > deadline:
                self.submit_error = (
                    f"已超过截止时间 "
                    f"({deadline.strftime('%Y-%m-%d %H:%M')})，无法提交"
                )
                return

        self.is_submitting = True
        self.submit_error = ""
        self.submit_message = ""

        try:
            aid = self.selected_assignment_id
            file_path = ""
            file_name = ""
            file_size = 0
            file_type = ""

            # 保存文件
            if self.uploaded_file_data:
                upload_dir = Path(UPLOAD_DIR) / aid
                upload_dir.mkdir(parents=True, exist_ok=True)

                # 查版本号
                with db_sync() as cur:
                    cur.execute(
                        "SELECT MAX(version) as max_ver FROM submissions "
                        "WHERE assignment_id = %s AND student_id = %s",
                        (aid, student_no),
                    )
                    row = cur.fetchone()
                    new_version = (row["max_ver"] or 0) + 1 if row else 1

                file_name = self.uploaded_file_name
                ext = _get_extension(file_name)
                file_type = ext
                file_size = self.uploaded_file_size

                safe_name = f"{student_no}_v{new_version}_{file_name}"
                dest = upload_dir / safe_name
                dest.write_bytes(self.uploaded_file_data)
                file_path = str(dest)
                file_name = safe_name
            else:
                # 纯文本提交，查版本号
                with db_sync() as cur:
                    cur.execute(
                        "SELECT MAX(version) as max_ver FROM submissions "
                        "WHERE assignment_id = %s AND student_id = %s",
                        (aid, student_no),
                    )
                    row = cur.fetchone()
                    new_version = (row["max_ver"] or 0) + 1 if row else 1

            # 写入数据库
            with transaction_sync() as cur:
                cur.execute(
                    "INSERT INTO submissions "
                    "(assignment_id, student_id, file_path, file_name, "
                    "file_size, file_type, content_text, version) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (aid, student_no, file_path, file_name,
                     file_size, file_type, self.content_text, new_version),
                )

            self.submit_message = (
                f"✅ 提交成功！版本：v{new_version}"
                + (f"，文件：{file_name}"
                   if file_name else "")
                + (f"，大小：{_format_file_size(file_size)}"
                   if file_size else "")
            )
            # 清空表单
            self.content_text = ""
            self.uploaded_file_name = ""
            self.uploaded_file_size = 0
            self.uploaded_file_data = b""
            # 刷新历史
            await self.load_history()

        except Exception as e:
            self.submit_error = f"提交失败: {e}"
        finally:
            self.is_submitting = False

    # ── 提交历史 ──
    async def load_history(self):
        """加载选中作业的提交历史"""
        student_no = self._get_student_no()
        if not student_no or not self.selected_assignment_id:
            self.submission_history = []
            return

        try:
            with db_sync() as cur:
                cur.execute(
                    "SELECT id, version, file_name, file_size, file_type, "
                    "content_text, submitted_at FROM submissions "
                    "WHERE assignment_id = %s AND student_id = %s "
                    "ORDER BY version DESC",
                    (self.selected_assignment_id, student_no),
                )
                rows = cur.fetchall()

            self.submission_history = []
            for r in rows:
                self.submission_history.append({
                    "id": r["id"],
                    "version": r["version"],
                    "file_name": r.get("file_name", ""),
                    "file_size": r.get("file_size", 0),
                    "file_size_display": (
                        _format_file_size(r["file_size"])
                        if r.get("file_size") else ""
                    ),
                    "file_type": r.get("file_type", ""),
                    "content_text": r.get("content_text", ""),
                    "submitted_at": str(r.get("submitted_at", "")),
                })
            self.show_history = True
        except Exception as e:
            self.submit_error = f"加载提交历史失败: {e}"

    def toggle_history(self):
        """切换历史面板显示/隐藏"""
        self.show_history = not self.show_history

    # ── 辅助 ──
    def _get_selected(self) -> Optional[Dict[str, Any]]:
        for a in self.assignments:
            if a["id"] == self.selected_assignment_id:
                return a
        return None
