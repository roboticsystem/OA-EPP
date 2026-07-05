"""F-S-021 提交版本管理 — SubmissionState

职责：
- load_submission_history(assignment_id) — 加载历史版本列表（最新在前）
- handle_submit(assignment_id, text_content, file_url) — 提交新版本
- handle_download(file_url) — 设置下载链接
- set_assignment(assignment_id) — 设置当前作业

数据库：
- 生产环境：通过 oaepp.database（db_sync / transaction_sync）连接 MySQL
- 测试环境：通过 _db_session（SQLite）注入

使用全局 ORM 模型：oaepp.models（SQLModel 表定义）
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

SubmissionState = None

if rx is not None:
    class SubmissionState(rx.State):
        """提交版本管理状态

        对应验收标准：
        - 多次提交自动保留历史版本（version_no 自增）
        - 最新版本自动设为评阅版本（列表第一位，标记 grading_status）
        - 历史版本列表可查看并支持下载
        """

        # ── 版本历史（TDD 要求：submission_history 或 versions） ──
        versions: List[Dict[str, Any]] = []
        submission_history: List[Dict[str, Any]] = []

        # ── 作业上下文 ──
        current_assignment_id: Optional[int] = None
        current_assignment_title: str = ""
        allow_resubmit: bool = False

        # ── UI 状态 ──
        submit_message: str = ""
        download_url: str = ""
        is_loading: bool = False

        # ── 表单字段 ──
        form_text_content: str = ""
        form_file_url: str = ""

        # ── 测试注入（由 conftest.py 通过 mem_db fixture 设置） ──
        _db_session: Any = None

        # ═════════════════════════════════════════════════════════════════════
        #  计算属性
        # ═════════════════════════════════════════════════════════════════════

        @rx.var
        def version_count_text(self) -> str:
            """版本数量文本，供页面动态展示。"""
            return f"共 {len(self.versions)} 个版本"

        # ═════════════════════════════════════════════════════════════════════
        #  核心方法
        # ═════════════════════════════════════════════════════════════════════

        async def load_from_route(self) -> None:
            """从 URL 查询参数读取 assignment_id 并加载版本历史。

            作为页面 on_mount 事件处理器使用：
                /versions?assignment_id=42 → 加载作业 42 的版本历史
            """
            aid = 0
            try:
                params = self.router.page.params or {}
                raw = params.get("assignment_id", "")
                aid = int(raw) if raw else 0
            except Exception:
                aid = 0

            if aid:
                await self.load_submission_history(assignment_id=aid)

        async def load_submission_history(self, assignment_id: int = 0) -> None:
            """加载指定作业的提交历史版本（最新在前）。

            若提供了 _db_session（测试环境），使用 SQLite Session；
            否则通过 oaepp.database 连接生产 MySQL。

            Args:
                assignment_id: 作业 ID，为 0 时使用 current_assignment_id
            """
            aid = assignment_id or self.current_assignment_id
            if not aid:
                self.versions = []
                self.submission_history = []
                return

            self.current_assignment_id = aid
            self.is_loading = True

            try:
                if hasattr(self, "_db_session") and self._db_session is not None:
                    await self._load_history_from_session(self._db_session, aid)
                else:
                    await self._load_history_from_production(aid)
            except Exception:
                self.versions = []
                self.submission_history = []
            finally:
                self.is_loading = False

        async def handle_submit(
            self,
            assignment_id: int = 0,
            text_content: str = "",
            file_url: str = "",
        ) -> None:
            """提交新版本。

            逻辑：
            1. 检查作业是否存在且允许重交
            2. 计算下一个版本号 = MAX(version_no) + 1
            3. 插入新提交记录
            4. 刷新版本历史

            Args:
                assignment_id: 作业 ID，为 0 时使用 current_assignment_id 或表单
                text_content: 文本内容
                file_url: 文件链接
            """
            aid = assignment_id or self.current_assignment_id
            text = text_content or self.form_text_content
            f_url = file_url or self.form_file_url

            if not aid:
                self.submit_message = "请先选择作业"
                return

            try:
                if hasattr(self, "_db_session") and self._db_session is not None:
                    await self._submit_via_session(self._db_session, aid, text, f_url)
                else:
                    await self._submit_via_production(aid, text, f_url)
            except Exception as e:
                self.submit_message = f"提交失败: {e}"

        def handle_download(self, file_url: str) -> None:
            """设置下载链接（供 UI 触发下载）。

            Args:
                file_url: 要下载的文件 URL
            """
            self.download_url = file_url

        def set_form_text_content(self, val: str) -> None:
            """更新表单文本内容。"""
            self.form_text_content = val

        def set_form_file_url(self, val: str) -> None:
            """更新表单文件链接。"""
            self.form_file_url = val

        async def set_assignment(self, assignment_id: int) -> None:
            """设置当前作业并加载其版本历史。

            Args:
                assignment_id: 作业 ID
            """
            self.current_assignment_id = assignment_id
            self.submit_message = ""
            self.form_text_content = ""
            self.form_file_url = ""
            await self.load_submission_history(assignment_id)

        # ═════════════════════════════════════════════════════════════════════
        #  内部实现 — Session（测试环境，SQLite）
        # ═════════════════════════════════════════════════════════════════════

        async def _load_history_from_session(self, session, assignment_id: int) -> None:
            """从 SQLite 测试 Session 加载版本历史。"""
            from sqlmodel import text as sql_text

            # 查询作业信息
            result = session.execute(
                sql_text(
                    "SELECT id, title, allow_resubmit FROM assignments WHERE id = :aid"
                ),
                {"aid": assignment_id},
            )
            row = result.fetchone()
            if row:
                self.current_assignment_title = row[1] or ""
                self.allow_resubmit = bool(row[2]) if len(row) > 2 else False

            # 查询版本历史（最新在前）
            result = session.execute(
                sql_text(
                    "SELECT id, assignment_id, student_user_id, version_no, "
                    "file_url, text_content, is_late, grading_status, "
                    "allow_resubmit_override, submitted_at "
                    "FROM submissions "
                    "WHERE assignment_id = :aid "
                    "ORDER BY version_no DESC"
                ),
                {"aid": assignment_id},
            )
            rows = result.fetchall()

            history = _build_history_from_rows(rows)
            self.versions = history
            self.submission_history = history

        async def _submit_via_session(
            self, session, assignment_id: int, text_content: str, file_url: str
        ) -> None:
            """通过测试 Session 提交新版本。"""
            from sqlmodel import text as sql_text

            # 查作业
            result = session.execute(
                sql_text(
                    "SELECT id, title, allow_resubmit, deadline, late_policy "
                    "FROM assignments WHERE id = :aid"
                ),
                {"aid": assignment_id},
            )
            a = result.fetchone()
            if not a:
                self.submit_message = "作业不存在"
                return

            allow_resubmit = bool(a[2]) if len(a) > 2 else False
            if not allow_resubmit:
                self.submit_message = "该作业不允许重复提交"
                return

            # 查最大版本号
            result = session.execute(
                sql_text(
                    "SELECT COALESCE(MAX(version_no), 0) FROM submissions "
                    "WHERE assignment_id = :aid"
                ),
                {"aid": assignment_id},
            )
            max_v = result.fetchone()[0]
            version_no = max_v + 1

            # 插入新版本
            now = datetime.datetime.now().isoformat()
            session.execute(
                sql_text(
                    "INSERT INTO submissions "
                    "(assignment_id, student_user_id, version_no, file_url, "
                    "text_content, is_late, grading_status, submitted_at) "
                    "VALUES (:aid, 1, :vno, :furl, :text, 0, 'pending', :now)"
                ),
                {
                    "aid": assignment_id,
                    "vno": version_no,
                    "furl": file_url or "",
                    "text": text_content or "",
                    "now": now,
                },
            )
            session.commit()

            self.submit_message = f"版本 v{version_no} 提交成功"
            self.form_text_content = ""
            self.form_file_url = ""
            await self._load_history_from_session(session, assignment_id)

        # ═════════════════════════════════════════════════════════════════════
        #  内部实现 — 生产环境（MySQL，通过 oaepp.database）
        # ═════════════════════════════════════════════════════════════════════

        async def _load_history_from_production(self, assignment_id: int) -> None:
            """从生产 MySQL 数据库加载版本历史。

            使用全局 oaepp.database.db_sync() 连接池。
            """
            from oaepp.database import db_sync

            # 查询作业信息
            with db_sync() as cur:
                cur.execute(
                    "SELECT id, title, allow_resubmit FROM assignments WHERE id = %s",
                    (assignment_id,),
                )
                a = cur.fetchone()
                if a:
                    self.current_assignment_title = a["title"] or ""
                    self.allow_resubmit = bool(a.get("allow_resubmit", False))

            # 查询版本历史（最新在前）
            with db_sync() as cur:
                cur.execute(
                    "SELECT id, assignment_id, student_user_id, version_no, "
                    "file_url, text_content, is_late, grading_status, "
                    "allow_resubmit_override, submitted_at "
                    "FROM submissions "
                    "WHERE assignment_id = %s "
                    "ORDER BY version_no DESC",
                    (assignment_id,),
                )
                rows = cur.fetchall()

            history = _build_history_from_rows(rows)
            self.versions = history
            self.submission_history = history

        async def _submit_via_production(
            self, assignment_id: int, text_content: str, file_url: str
        ) -> None:
            """通过生产 MySQL 数据库提交新版本。

            使用全局 oaepp.database.transaction_sync() 确保事务安全。
            """
            from oaepp.database import transaction_sync

            with transaction_sync() as cur:
                # 查作业
                cur.execute(
                    "SELECT id, title, allow_resubmit, deadline, late_policy "
                    "FROM assignments WHERE id = %s",
                    (assignment_id,),
                )
                a = cur.fetchone()
                if not a:
                    self.submit_message = "作业不存在"
                    return

                if not a.get("allow_resubmit", False):
                    self.submit_message = "该作业不允许重复提交"
                    return

                # 获取当前用户 user_id
                student_user_id = self._resolve_student_user_id(cur)

                # 查最大版本号
                cur.execute(
                    "SELECT COALESCE(MAX(version_no), 0) FROM submissions "
                    "WHERE assignment_id = %s AND student_user_id = %s",
                    (assignment_id, student_user_id),
                )
                max_v = cur.fetchone()["COALESCE(MAX(version_no), 0)"]
                version_no = max_v + 1

                # 检查是否迟交
                now = datetime.datetime.now()
                deadline = a.get("deadline")
                is_late = 1 if (deadline and now > deadline) else 0

                # 插入新版本
                cur.execute(
                    "INSERT INTO submissions "
                    "(assignment_id, student_user_id, version_no, file_url, "
                    "text_content, is_late, grading_status, submitted_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())",
                    (
                        assignment_id,
                        student_user_id,
                        version_no,
                        file_url or "",
                        text_content or "",
                        is_late,
                    ),
                )
                # transaction_sync 会在退出时自动 commit

            self.submit_message = f"版本 v{version_no} 提交成功"
            self.form_text_content = ""
            self.form_file_url = ""
            await self._load_history_from_production(assignment_id)

        def _resolve_student_user_id(self, cur) -> int:
            """获取当前登录学生用户的 user_id。

            优先从 AuthState 读取，其次通过 _student_no 查询数据库，
            最后返回开发默认值 1。
            """
            # 尝试从 AuthState 获取
            try:
                from oaepp.states.auth import AuthState
                if hasattr(AuthState, "current_user_id") and AuthState.current_user_id:
                    return AuthState.current_user_id
            except Exception:
                pass

            # 回退：从 _student_no 查询
            if self._student_no:
                cur.execute(
                    "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                    (self._student_no,),
                )
                row = cur.fetchone()
                if row:
                    return row["id"]

            # 开发模式默认值
            return 1


# ═════════════════════════════════════════════════════════════════════
#  模块级辅助函数
# ═════════════════════════════════════════════════════════════════════

def _format_time(ts: str) -> str:
    """格式化时间戳为可读格式（YYYY-MM-DD HH:MM）。"""
    if not ts:
        return "—"
    try:
        if "T" in ts:
            dt_part = ts.split("T")[0]
            time_part = (
                ts.split("T")[1].split(".")[0][:5]
                if "." in ts.split("T")[1]
                else ts.split("T")[1][:5]
            )
            return f"{dt_part} {time_part}"
        if " " in ts:
            parts = ts.split(" ")
            return f"{parts[0]} {parts[1][:5]}" if len(parts) > 1 else ts[:16]
        return ts[:16]
    except Exception:
        return ts[:16]


def _truncate(text: str, max_len: int = 60) -> str:
    """截断文本，超出部分用省略号表示。"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _grading_label(status: str) -> str:
    """将 grading_status 映射为用户可读标签。"""
    _labels = {
        "pending": "待批改",
        "graded": "已批改",
        "returned": "已发回",
    }
    return _labels.get(status, status)


def _build_history_from_rows(rows) -> List[Dict[str, Any]]:
    """将数据库查询结果转换为版本历史列表。

    Args:
        rows: 数据库游标 fetchall() 返回的行列表（可为 dict-like 或 tuple-like）

    Returns:
        版本历史列表，最新版本标记 is_latest=True 和 grading_label
    """
    import datetime as dt

    history = []
    for r in rows:
        # 兼容 pymysql DictCursor（dict）和 sqlmodel CursorResult（tuple）
        if isinstance(r, dict):
            submitted_at = r.get("submitted_at")
            history.append({
                "id": r["id"],
                "assignment_id": r["assignment_id"],
                "student_user_id": r["student_user_id"],
                "version_no": r["version_no"],
                "file_url": r.get("file_url") or "",
                "text_content": r.get("text_content") or "",
                "text_preview": _truncate(r.get("text_content") or "", 60),
                "is_late": bool(r.get("is_late", False)),
                "grading_status": r.get("grading_status", "pending"),
                "allow_resubmit_override": r.get("allow_resubmit_override"),
                "submitted_at": (
                    submitted_at.isoformat()
                    if isinstance(submitted_at, dt.datetime)
                    else str(submitted_at or "")
                ),
                "is_latest": False,
            })
        else:
            # sqlmodel CursorResult → tuple-like，按索引访问
            submitted_at = r[9] if len(r) > 9 else ""
            history.append({
                "id": r[0],
                "assignment_id": r[1],
                "student_user_id": r[2],
                "version_no": r[3],
                "file_url": r[4] or "",
                "text_content": r[5] or "",
                "text_preview": _truncate(r[5] or "", 60),
                "is_late": bool(r[6]),
                "grading_status": r[7] or "pending",
                "allow_resubmit_override": r[8] if len(r) > 8 else None,
                "submitted_at": (
                    submitted_at.isoformat()
                    if isinstance(submitted_at, dt.datetime)
                    else str(submitted_at or "")
                ),
                "is_latest": False,
                "submitted_at_display": _format_time(
                    submitted_at.isoformat()
                    if isinstance(submitted_at, dt.datetime)
                    else str(submitted_at or "")
                ),
            })

    # 标记最新版本为评阅版本
    if history:
        history[0]["is_latest"] = True
        history[0]["grading_label"] = "评阅版本（最新）"
    for i in range(1, len(history)):
        history[i]["grading_label"] = _grading_label(history[i]["grading_status"])

    return history
