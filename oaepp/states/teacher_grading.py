"""F-T-014 在线批改 — GradingState

Reflex State，提供教师端在线批改队列的状态管理：
- grading_queue: 待批改提交队列
- current_submission: 当前正在批改的提交详情
- 按维度打分（attendance / exam / code / pr）
- 评语与改进建议（Markdown 格式）
- copy_last_comment() 快捷复制上一份评语
- allow_resubmit 控制二次提交
- 批改审计日志（audit_log），不可删除
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

logger = logging.getLogger("teacher_grading")


# ═══════════════════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def _load_filter_options() -> dict:
    """从数据库加载筛选选项（班级/课程）"""
    try:
        from oaepp.database import db_sync
    except ImportError:
        try:
            from database import db_sync
        except ImportError:
            logger.warning("db_sync not available, returning empty filters")
            return {"classes": [], "courses": []}
    try:
        with db_sync() as cur:
            cur.execute(
                "SELECT DISTINCT s.class_name FROM students s "
                "JOIN users u ON u.id = s.user_id "
                "WHERE u.role='student' AND s.class_name!='' ORDER BY s.class_name"
            )
            classes = [r["class_name"] for r in cur.fetchall()]

            cur.execute("SELECT id, name FROM courses ORDER BY id")
            courses = [{"id": r["id"], "title": r["name"]} for r in cur.fetchall()]
        return {"classes": classes, "courses": courses}
    except Exception as e:
        logger.error("Failed to load filter options: %s", e)
        return {"classes": [], "courses": []}


def _load_grading_queue(course_id: int = 0, class_name: str = "") -> List[dict]:
    """从数据库加载待批改提交队列，默认按截止时间升序排列"""
    try:
        from oaepp.database import db_sync
    except ImportError:
        try:
            from database import db_sync
        except ImportError:
            return []
    try:
        with db_sync() as cur:
            params = []
            where_clauses = ["s.grading_status = 'pending'"]
            if course_id:
                where_clauses.append("a.course_id = %s")
                params.append(course_id)
            if class_name:
                where_clauses.append("st.class_name = %s")
                params.append(class_name)
            where_sql = " AND ".join(where_clauses)

            sql = f"""
                SELECT
                    s.id AS submission_id,
                    s.assignment_id,
                    s.student_user_id,
                    s.version_no,
                    s.file_url,
                    s.text_content,
                    s.is_late,
                    s.grading_status,
                    s.submitted_at,
                    u.student_no,
                    u.full_name,
                    st.class_name,
                    a.title AS assignment_title,
                    a.deadline,
                    a.allow_resubmit AS assignment_allow_resubmit,
                    c.id AS course_id,
                    c.name AS course_name
                FROM submissions s
                JOIN users u ON u.id = s.student_user_id
                JOIN students st ON st.user_id = u.id
                JOIN assignments a ON a.id = s.assignment_id
                JOIN courses c ON c.id = a.course_id
                WHERE {where_sql}
                ORDER BY a.deadline ASC
            """
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
        return rows
    except Exception as e:
        logger.error("Failed to load grading queue: %s", e)
        return []


def _load_submission_detail(submission_id: int) -> Optional[dict]:
    """加载单个提交的详细信息"""
    try:
        from oaepp.database import db_sync
    except ImportError:
        try:
            from database import db_sync
        except ImportError:
            return None
    try:
        with db_sync() as cur:
            cur.execute(
                """SELECT
                    s.id AS submission_id,
                    s.assignment_id,
                    s.student_user_id,
                    s.version_no,
                    s.file_url,
                    s.text_content,
                    s.is_late,
                    s.grading_status,
                    s.submitted_at,
                    u.student_no,
                    u.full_name,
                    st.class_name,
                    a.title AS assignment_title,
                    a.description_md,
                    a.deadline,
                    a.allow_resubmit AS assignment_allow_resubmit,
                    c.id AS course_id,
                    c.name AS course_name
                FROM submissions s
                JOIN users u ON u.id = s.student_user_id
                JOIN students st ON st.user_id = u.id
                JOIN assignments a ON a.id = s.assignment_id
                JOIN courses c ON c.id = a.course_id
                WHERE s.id = %s""",
                (submission_id,)
            )
            row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to load submission detail: %s", e)
        return None


def _load_existing_grading(submission_id: int) -> Optional[dict]:
    """加载已有的批改记录（若存在）"""
    try:
        from oaepp.database import db_sync
    except ImportError:
        try:
            from database import db_sync
        except ImportError:
            return None
    try:
        with db_sync() as cur:
            cur.execute(
                "SELECT * FROM grading_records WHERE submission_id = %s LIMIT 1",
                (submission_id,)
            )
            row = cur.fetchone()
        if row:
            r = dict(row)
            for key in ("attendance_score", "exam_score", "code_score", "pr_score", "total_score"):
                if r.get(key) is not None:
                    r[key] = float(r[key])
            return r
        return None
    except Exception as e:
        logger.error("Failed to load existing grading: %s", e)
        return None


def _load_audit_logs_from_db() -> List[dict]:
    """从 grading_audit_logs 表加载审计日志"""
    try:
        from oaepp.database import db_sync
    except ImportError:
        try:
            from database import db_sync
        except ImportError:
            return []
    try:
        with db_sync() as cur:
            cur.execute(
                "SELECT * FROM grading_audit_logs ORDER BY id DESC LIMIT 200"
            )
            rows = [dict(r) for r in cur.fetchall()]
        return rows
    except Exception as e:
        logger.warning("Audit log table may not exist yet: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════
#  GradingState
# ═══════════════════════════════════════════════════════════════════════════

GradingState = None
if rx is not None:

    class GradingState(rx.State):
        """教师端在线批改状态管理

        对齐需求 F-S-030 / F-S-031 / F-T-014：
        - 批改队列：待批改提交列表，支持筛选
        - 逐份批改：按维度打分、评语与改进建议
        - copy_last_comment() 快捷操作
        - allow_resubmit 二次提交开关
        - 审计日志完整记录，不可删除
        """

        # ── TDD 测试要求的核心变量 ──
        grading_queue: List[Dict[str, Any]] = []
        current_submission: Dict[str, Any] = {}
        is_submitting: bool = False
        allow_resubmit: bool = False
        audit_log: List[Dict[str, Any]] = []

        # ── 加载状态 ──
        is_loading: bool = False
        error_message: str = ""
        success_message: str = ""

        # ── 筛选 ──
        course_filter: str = ""
        class_filter: str = ""
        filter_options: Dict[str, Any] = {}

        # ── 批改输入 ──
        attendance_score: str = ""
        exam_score: str = ""
        code_score: str = ""
        pr_score: str = ""
        comment_md: str = ""
        improvement_md: str = ""

        # ── 导航 ──
        current_index: int = 0
        last_comment: str = ""

        # ── 审计日志展示 ──
        show_audit_log: bool = False

        # ── 队列筛选与加载 ─────────────────────────────────────────────

        async def load_filters(self):
            """加载筛选下拉选项"""
            self.filter_options = _load_filter_options()

        async def load_queue(self):
            """加载待批改提交队列"""
            self.is_loading = True
            self.error_message = ""

            cid = 0
            if self.course_filter:
                try:
                    cid = int(self.course_filter)
                except ValueError:
                    for c in self.filter_options.get("courses", []):
                        if str(c.get("id")) == self.course_filter:
                            cid = int(c["id"])
                            break

            self.grading_queue = _load_grading_queue(course_id=cid, class_name=self.class_filter)
            self.is_loading = False

        async def set_course(self, val):
            """设置课程筛选"""
            if isinstance(val, list):
                self.course_filter = val[0] if val else ""
            else:
                self.course_filter = str(val) if val else ""
            self.current_index = 0
            self.current_submission = {}
            await self.load_queue()

        async def set_class(self, val):
            """设置班级筛选"""
            if isinstance(val, list):
                self.class_filter = val[0] if val else ""
            else:
                self.class_filter = str(val) if val else ""
            self.current_index = 0
            self.current_submission = {}
            await self.load_queue()

        # ── 逐份批改 ─────────────────────────────────────────────────

        async def load_submission(self, submission_id: int = 0):
            """加载指定提交的详细内容进入批改界面"""
            self.is_loading = True
            self.error_message = ""
            self.success_message = ""

            sid = submission_id
            if not sid and self.grading_queue:
                idx = self.current_index
                if 0 <= idx < len(self.grading_queue):
                    sid = self.grading_queue[idx].get("submission_id", 0)

            if not sid:
                self.error_message = "未找到提交记录"
                self.is_loading = False
                return

            detail = _load_submission_detail(sid)
            if not detail:
                self.error_message = f"提交 #{sid} 不存在"
                self.is_loading = False
                return

            self.current_submission = detail

            # 尝试加载已有批改记录
            existing = _load_existing_grading(sid)
            if existing:
                self.attendance_score = str(existing.get("attendance_score") or "")
                self.exam_score = str(existing.get("exam_score") or "")
                self.code_score = str(existing.get("code_score") or "")
                self.pr_score = str(existing.get("pr_score") or "")
                self.comment_md = existing.get("comment_md") or ""
                self.allow_resubmit = bool(existing.get("allow_resubmit", False))
            else:
                self._reset_grading_form()

            self.is_loading = False

        def _reset_grading_form(self):
            """重置批改表单到初始状态"""
            self.attendance_score = ""
            self.exam_score = ""
            self.code_score = ""
            self.pr_score = ""
            self.comment_md = ""
            self.improvement_md = ""
            self.allow_resubmit = False

        def set_attendance_score(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.attendance_score = str(val)

        def set_exam_score(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.exam_score = str(val)

        def set_code_score(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.code_score = str(val)

        def set_pr_score(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.pr_score = str(val)

        def set_comment(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.comment_md = str(val)

        def set_improvement(self, val):
            if isinstance(val, list):
                val = val[0] if val else ""
            self.improvement_md = str(val)

        def toggle_resubmit(self, val):
            """切换二次提交开关"""
            if isinstance(val, list):
                val = val[0] if val else val
            self.allow_resubmit = bool(val)

        # ── 快捷操作 ─────────────────────────────────────────────────

        def copy_last_comment(self):
            """复制上一份评语内容到当前评语框"""
            if self.last_comment:
                self.comment_md = self.last_comment
                self.success_message = "已复制上一份评语"
            else:
                self.error_message = "没有可复制的评语（尚未保存过任何评语）"

        # ── 导航 ─────────────────────────────────────────────────────

        async def next_submission(self):
            """跳转到队列中下一份提交"""
            if not self.grading_queue:
                return
            if self.current_index < len(self.grading_queue) - 1:
                self.current_index += 1
                await self.load_submission()

        async def prev_submission(self):
            """跳转到队列中上一份提交"""
            if self.current_index < 1:
                return
            self.current_index -= 1
            await self.load_submission()

        async def goto_submission(self, index: int):
            """跳转到队列中指定索引的提交"""
            if 0 <= index < len(self.grading_queue):
                self.current_index = index
                await self.load_submission()

        # ── 提交批改 ─────────────────────────────────────────────────

        async def submit_grade(self):
            """保存批改结果，发送通知，写入审计日志"""
            self.is_submitting = True
            self.error_message = ""
            self.success_message = ""

            sid = self.current_submission.get("submission_id", 0)
            if not sid:
                self.error_message = "未选中任何提交"
                self.is_submitting = False
                return

            # 解析分数
            def _parse_score(val: str) -> Optional[float]:
                if not val or not str(val).strip():
                    return None
                try:
                    return round(float(val), 2)
                except (ValueError, TypeError):
                    return None

            att_score = _parse_score(self.attendance_score)
            exm_score = _parse_score(self.exam_score)
            cod_score = _parse_score(self.code_score)
            pr_s = _parse_score(self.pr_score)

            # 计算总分
            scores_non_none = [s for s in (att_score, exm_score, cod_score, pr_s) if s is not None]
            total = round(sum(scores_non_none), 2) if scores_non_none else None

            # 合并评语与改进建议
            full_comment = self.comment_md or ""
            if self.improvement_md:
                if full_comment:
                    full_comment += "\n\n## 改进建议\n\n" + self.improvement_md
                else:
                    full_comment = "## 改进建议\n\n" + self.improvement_md

            student_user_id = self.current_submission.get("student_user_id", 0)
            student_name = self.current_submission.get("full_name", "")
            assignment_title = self.current_submission.get("assignment_title", "")
            course_name = self.current_submission.get("course_name", "")

            try:
                from oaepp.database import transaction_sync, db_sync
            except ImportError:
                try:
                    from database import transaction_sync, db_sync
                except ImportError:
                    self.error_message = "数据库连接不可用"
                    self.is_submitting = False
                    return

            try:
                graded_by = 1  # teacher user_id

                with transaction_sync() as cur:
                    # 1. 写入/更新 grading_records
                    cur.execute(
                        "SELECT id FROM grading_records WHERE submission_id = %s LIMIT 1",
                        (sid,)
                    )
                    existing_gr = cur.fetchone()

                    if existing_gr:
                        cur.execute(
                            """UPDATE grading_records
                               SET attendance_score=%s, exam_score=%s, code_score=%s, pr_score=%s,
                                   total_score=%s, comment_md=%s, allow_resubmit=%s, graded_at=NOW()
                               WHERE submission_id=%s""",
                            (att_score, exm_score, cod_score, pr_s, total, full_comment,
                             self.allow_resubmit, sid)
                        )
                    else:
                        cur.execute(
                            """INSERT INTO grading_records
                               (submission_id, graded_by, attendance_score, exam_score, code_score,
                                pr_score, total_score, comment_md, allow_resubmit, graded_at)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                            (sid, graded_by, att_score, exm_score, cod_score, pr_s, total,
                             full_comment, self.allow_resubmit)
                        )

                    # 2. 更新 submission 状态
                    cur.execute(
                        "UPDATE submissions SET grading_status = 'graded' WHERE id = %s",
                        (sid,)
                    )

                # 3. 写入 score_items（按维度分别记录）
                with db_sync() as cur:
                    assignment_id = self.current_submission.get("assignment_id", 0)
                    course_id = self.current_submission.get("course_id", 0)
                    score_type_map = {
                        "attendance": att_score,
                        "exam": exm_score,
                        "code": cod_score,
                        "pr": pr_s,
                    }
                    for s_type, s_val in score_type_map.items():
                        if s_val is not None:
                            cur.execute(
                                "SELECT id FROM score_items WHERE course_id=%s AND student_user_id=%s AND score_type=%s AND ref_id=%s LIMIT 1",
                                (course_id, student_user_id, s_type, sid)
                            )
                            existing_si = cur.fetchone()
                            if existing_si:
                                cur.execute(
                                    "UPDATE score_items SET score=%s, scored_by=%s, scored_at=NOW() WHERE id=%s",
                                    (s_val, graded_by, existing_si["id"])
                                )
                            else:
                                cur.execute(
                                    """INSERT INTO score_items
                                       (course_id, student_user_id, score_type, ref_id, score, scored_by, scored_at)
                                       VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                                    (course_id, student_user_id, s_type, sid, s_val, graded_by)
                                )

                # 4. 发送站内通知给学生
                with db_sync() as cur:
                    notification_title = f"作业已批改：{assignment_title}"
                    notification_body = f"您在课程「{course_name}」中的作业「{assignment_title}」已批改完成，请查看评语。"
                    cur.execute(
                        """INSERT INTO notifications
                           (user_id, title, body, category, source_ref, is_read, created_at)
                           VALUES (%s, %s, %s, 'grade', %s, 0, NOW())""",
                        (student_user_id, notification_title, notification_body, f"submission:{sid}")
                    )

                # 5. 写入审计日志
                self._write_audit_log(sid, att_score, exm_score, cod_score, pr_s, total)

                # 6. 更新队列中当前项状态
                if 0 <= self.current_index < len(self.grading_queue):
                    self.grading_queue[self.current_index]["grading_status"] = "graded"
                    self.grading_queue[self.current_index]["allow_resubmit"] = self.allow_resubmit

                # 7. 保存当前评语为 "上一份"，供下次复制
                self.last_comment = self.comment_md

                self.success_message = f"批改已保存 — {student_name} 的「{assignment_title}」已批改完成，已通知学生"

            except Exception as e:
                logger.error("submit_grade failed: %s", e)
                self.error_message = f"批改保存失败：{e}"
            finally:
                self.is_submitting = False

        def _write_audit_log(self, submission_id: int, att_score, exm_score, cod_score, pr_s, total):
            """写入不可变审计日志"""
            from datetime import datetime
            try:
                from oaepp.database import db_sync
            except ImportError:
                try:
                    from database import db_sync
                except ImportError:
                    self.audit_log.append({
                        "submission_id": submission_id,
                        "graded_by": "teacher",
                        "attendance_score": att_score,
                        "exam_score": exm_score,
                        "code_score": cod_score,
                        "pr_score": pr_s,
                        "total_score": total,
                        "allow_resubmit": self.allow_resubmit,
                        "graded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "comment_md": self.comment_md,
                    })
                    return

            try:
                import json
                with db_sync() as cur:
                    audit_data = json.dumps({
                        "attendance_score": att_score,
                        "exam_score": exm_score,
                        "code_score": cod_score,
                        "pr_score": pr_s,
                        "total_score": total,
                        "allow_resubmit": self.allow_resubmit,
                        "comment_md": self.comment_md[:500] if self.comment_md else "",
                    }, ensure_ascii=False)
                    cur.execute(
                        """INSERT INTO grading_audit_logs
                           (submission_id, graded_by, scores_json, created_at)
                           VALUES (%s, %s, %s, NOW())""",
                        (submission_id, "teacher", audit_data)
                    )
            except Exception as e:
                logger.warning("Failed to write audit log to DB: %s, falling back to in-memory", e)
                self.audit_log.append({
                    "submission_id": submission_id,
                    "graded_by": "teacher",
                    "attendance_score": att_score,
                    "exam_score": exm_score,
                    "code_score": cod_score,
                    "pr_score": pr_s,
                    "total_score": total,
                    "allow_resubmit": self.allow_resubmit,
                    "graded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "comment_md": self.comment_md,
                })

        # ── 审计日志查询 ──────────────────────────────────────────────

        async def load_audit_logs(self):
            """从数据库加载批改审计日志"""
            self.error_message = ""
            try:
                self.audit_log = _load_audit_logs_from_db()
                self.show_audit_log = True
            except Exception as e:
                logger.error("Failed to load audit logs: %s", e)
                self.error_message = f"加载审计日志失败：{e}"

        def toggle_audit_log(self):
            """切换审计日志面板显示"""
            self.show_audit_log = not self.show_audit_log

        # ── 计算属性 ─────────────────────────────────────────────────

        @rx.var
        def queue_total(self) -> int:
            """队列中提交总数"""
            return len(self.grading_queue)

        @rx.var
        def queue_pending_count(self) -> int:
            """队列中待批改数量"""
            return sum(1 for r in self.grading_queue if r.get("grading_status") == "pending")

        @rx.var
        def has_next(self) -> bool:
            """是否有下一份"""
            return self.current_index < len(self.grading_queue) - 1

        @rx.var
        def has_prev(self) -> bool:
            """是否有上一份"""
            return self.current_index > 0

        @rx.var
        def total_score(self) -> str:
            """当前份总分（显示用）"""
            scores = []
            for s in (self.attendance_score, self.exam_score, self.code_score, self.pr_score):
                if s and str(s).strip():
                    try:
                        scores.append(float(s))
                    except ValueError:
                        pass
            return f"{sum(scores):.1f}" if scores else "-"

        @rx.var
        def submission_preview(self) -> str:
            """当前提交内容的文本预览（截断 500 字符）"""
            text = self.current_submission.get("text_content") or ""
            if not text:
                return "（无文本内容，可通过附件链接下载查看）"
            return text[:500] + ("..." if len(text) > 500 else "")
