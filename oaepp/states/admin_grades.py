"""F-T-012 教师权重调整 — TeacherGradeWeightState

提供四维度评分权重（出勤/考试/代码提交/PR贡献）的可视化调整：
- 滑块与数字输入联动，自动归一化至 100%
- 实时热力图预览差异
- 按课程保存权重方案，支持历史回滚
- 审计日志不可删除
"""

import datetime
import json
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

GradeWeightState = None

if rx is not None:

    class GradeWeightState(rx.State):
        """教师权重调整状态管理

        对齐原型 prototype/admin_grades.html 中的权重调整区域。
        """

        # ── 四维度权重（原始值，编辑中） ──
        attendance_weight: int = 25
        exam_weight: int = 25
        code_weight: int = 25
        pr_weight: int = 25

        # ── 归一化后的百分比（自动计算，合计 100） ──
        attendance_pct: int = 25
        exam_pct: int = 25
        code_pct: int = 25
        pr_pct: int = 25

        # ── 课程 ──
        courses: List[Dict[str, Any]] = []
        selected_course_id: int = 0
        selected_course_name: str = ""

        # ── 热力图 ──
        heatmap_data: List[Dict[str, Any]] = []
        show_heatmap: bool = False
        heatmap_summary: Dict[str, int] = {"up": 0, "down": 0, "unchanged": 0}

        # ── 历史方案 ──
        weight_history: List[Dict[str, Any]] = []

        # ── 审计日志 ──
        audit_log: List[Dict[str, Any]] = []

        # ── UI 状态 ──
        is_saving: bool = False
        is_loading: bool = False
        status_message: str = ""
        status_type: str = "info"  # info | success | error
        active_tab: str = "weights"  # weights | history | audit

        # ── 计算属性 ──

        @rx.var
        def total_pct(self) -> int:
            """四个维度的百分比之和（应恒为 100）"""
            return self.attendance_pct + self.exam_pct + self.code_pct + self.pr_pct

        @rx.var
        def is_balanced(self) -> bool:
            """检查权重是否已平衡（合计 100%）"""
            return self.total_pct == 100

        @rx.var
        def course_options(self) -> List[str]:
            """课程下拉选项列表（响应式）"""
            return [
                f"{c.get('code', '')} {c.get('name', '')} ({c.get('term', '')})"
                for c in (self.courses or [])
            ]

        @rx.var
        def selected_course_label(self) -> str:
            """当前选中课程的显示标签"""
            if self.selected_course_id == 0:
                return ""
            for c in (self.courses or []):
                if c.get("id") == self.selected_course_id:
                    return f"{c.get('code', '')} {c.get('name', '')} ({c.get('term', '')})"
            return ""

        @rx.var
        def heatmap_up_count(self) -> int:
            return self.heatmap_summary.get("up", 0)

        @rx.var
        def heatmap_down_count(self) -> int:
            return self.heatmap_summary.get("down", 0)

        @rx.var
        def heatmap_unchanged_count(self) -> int:
            return self.heatmap_summary.get("unchanged", 0)

        # ── 权重编辑处理器 ──

        async def set_attendance_weight(self, val: int):
            """设置出勤权重，触发自动归一化"""
            self.attendance_weight = self._clamp(val)
            self._normalize_from("attendance")
            await self._refresh_heatmap()

        async def set_exam_weight(self, val: int):
            """设置考试权重，触发自动归一化"""
            self.exam_weight = self._clamp(val)
            self._normalize_from("exam")
            await self._refresh_heatmap()

        async def set_code_weight(self, val: int):
            """设置代码提交权重，触发自动归一化"""
            self.code_weight = self._clamp(val)
            self._normalize_from("code")
            await self._refresh_heatmap()

        async def set_pr_weight(self, val: int):
            """设置 PR 贡献权重，触发自动归一化"""
            self.pr_weight = self._clamp(val)
            self._normalize_from("pr")
            await self._refresh_heatmap()

        async def set_attendance_pct(self, pct: int):
            """直接设置出勤百分比滑块"""
            pct = self._clamp(pct)
            old_total_others = self.exam_pct + self.code_pct + self.pr_pct
            self.attendance_pct = pct
            remaining = 100 - pct
            if old_total_others > 0:
                self.exam_pct = round(remaining * self.exam_pct / old_total_others)
                self.code_pct = round(remaining * self.code_pct / old_total_others)
                self.pr_pct = remaining - self.exam_pct - self.code_pct
            else:
                self.exam_pct = remaining // 3
                self.code_pct = remaining // 3
                self.pr_pct = remaining - self.exam_pct - self.code_pct
            self._sync_weights_from_pct()
            await self._refresh_heatmap()

        async def set_exam_pct(self, pct: int):
            """直接设置考试百分比滑块"""
            pct = self._clamp(pct)
            old_total_others = self.attendance_pct + self.code_pct + self.pr_pct
            self.exam_pct = pct
            remaining = 100 - pct
            if old_total_others > 0:
                self.attendance_pct = round(remaining * self.attendance_pct / old_total_others)
                self.code_pct = round(remaining * self.code_pct / old_total_others)
                self.pr_pct = remaining - self.attendance_pct - self.code_pct
            else:
                self.attendance_pct = remaining // 3
                self.code_pct = remaining // 3
                self.pr_pct = remaining - self.attendance_pct - self.code_pct
            self._sync_weights_from_pct()
            await self._refresh_heatmap()

        async def set_code_pct(self, pct: int):
            """直接设置代码百分比滑块"""
            pct = self._clamp(pct)
            old_total_others = self.attendance_pct + self.exam_pct + self.pr_pct
            self.code_pct = pct
            remaining = 100 - pct
            if old_total_others > 0:
                self.attendance_pct = round(remaining * self.attendance_pct / old_total_others)
                self.exam_pct = round(remaining * self.exam_pct / old_total_others)
                self.pr_pct = remaining - self.attendance_pct - self.exam_pct
            else:
                self.attendance_pct = remaining // 3
                self.exam_pct = remaining // 3
                self.pr_pct = remaining - self.attendance_pct - self.exam_pct
            self._sync_weights_from_pct()
            await self._refresh_heatmap()

        async def set_pr_pct(self, pct: int):
            """直接设置 PR 百分比滑块"""
            pct = self._clamp(pct)
            old_total_others = self.attendance_pct + self.exam_pct + self.code_pct
            self.pr_pct = pct
            remaining = 100 - pct
            if old_total_others > 0:
                self.attendance_pct = round(remaining * self.attendance_pct / old_total_others)
                self.exam_pct = round(remaining * self.exam_pct / old_total_others)
                self.code_pct = remaining - self.attendance_pct - self.exam_pct
            else:
                self.attendance_pct = remaining // 3
                self.exam_pct = remaining // 3
                self.code_pct = remaining - self.attendance_pct - self.exam_pct
            self._sync_weights_from_pct()
            await self._refresh_heatmap()

        async def set_active_tab(self, tab: str):
            """切换标签页"""
            self.active_tab = tab
            if tab == "history":
                await self.load_history()
            elif tab == "audit":
                await self.load_audit_log()

        async def set_attendance_pct_raw(self, val: str):
            await self.set_attendance_pct(int(float(val or 0)))

        async def set_exam_pct_raw(self, val: str):
            await self.set_exam_pct(int(float(val or 0)))

        async def set_code_pct_raw(self, val: str):
            await self.set_code_pct(int(float(val or 0)))

        async def set_pr_pct_raw(self, val: str):
            await self.set_pr_pct(int(float(val or 0)))

        async def reset_to_default(self):
            """一键重置四维度权重为默认值 25/25/25/25"""
            self.attendance_pct = 25
            self.exam_pct = 25
            self.code_pct = 25
            self.pr_pct = 25
            self._sync_weights_from_pct()
            await self._refresh_heatmap()
            self.status_message = "已重置为默认权重 25/25/25/25"
            self.status_type = "success"

        async def set_selected_course(self, course_id: int):
            """选择课程后加载该课程的权重方案"""
            self.selected_course_id = course_id
            for c in self.courses:
                if c.get("id") == course_id:
                    self.selected_course_name = c.get("name", "")
                    break
            await self._load_current_weights()

        async def set_selected_course_by_label(self, label: str):
            """通过课程显示标签选择课程（Reflex 0.9.4 rx.select 兼容接口）"""
            if not label:
                return
            for c in (self.courses or []):
                if f"{c.get('code', '')} {c.get('name', '')} ({c.get('term', '')})" == label:
                    await self.set_selected_course(c.get("id", 0))
                    return

        # ── 核心操作 ──

        async def load_courses(self):
            """加载教师可管理的课程列表"""
            try:
                from database import db as async_db
            except ImportError:
                from oaepp.database import db as async_db

            try:
                async with async_db() as cur:
                    await cur.execute(
                        "SELECT id, code, name, term FROM courses ORDER BY term DESC, code ASC"
                    )
                    rows = await cur.fetchall()
                self.courses = [
                    {
                        "id": r["id"],
                        "code": r.get("code", ""),
                        "name": r.get("name", ""),
                        "term": r.get("term", ""),
                    }
                    for r in rows
                ]
            except Exception:
                self.courses = []

        async def save_weights(self):
            """保存当前权重方案，生成历史记录与审计日志"""
            self.is_saving = True
            try:
                from database import transaction
            except ImportError:
                from oaepp.database import transaction

            if self.selected_course_id == 0:
                self.status_message = "请先选择课程"
                self.status_type = "error"
                self.is_saving = False
                return

            old_weights = await self._get_current_db_weights()
            new_weights = {
                "attendance": self.attendance_pct,
                "exam": self.exam_pct,
                "code": self.code_pct,
                "pr": self.pr_pct,
            }

            current_user = await self._get_current_user()
            now = datetime.datetime.now().isoformat()

            try:
                async with transaction() as cur:
                    # 1. 更新或插入当前权重方案
                    await cur.execute(
                        """INSERT INTO grade_weight_configs
                           (course_id, attendance_weight, exam_weight, code_weight, pr_weight, updated_by, updated_at)
                           VALUES (%s, %s, %s, %s, %s, %s, NOW())
                           ON DUPLICATE KEY UPDATE
                           attendance_weight = VALUES(attendance_weight),
                           exam_weight = VALUES(exam_weight),
                           code_weight = VALUES(code_weight),
                           pr_weight = VALUES(pr_weight),
                           updated_by = VALUES(updated_by),
                           updated_at = NOW()""",
                        (
                            self.selected_course_id,
                            self.attendance_pct,
                            self.exam_pct,
                            self.code_pct,
                            self.pr_pct,
                            current_user["id"],
                        ),
                    )

                    # 2. 写入历史方案快照
                    await cur.execute(
                        """INSERT INTO grade_weight_history
                           (course_id, weights_json, modified_by, modified_at)
                           VALUES (%s, %s, %s, NOW())""",
                        (self.selected_course_id, json.dumps(new_weights), current_user["id"]),
                    )

                    # 3. 写入审计日志
                    log_entry = {
                        "course_id": self.selected_course_id,
                        "course_name": self.selected_course_name,
                        "modified_by_id": current_user["id"],
                        "modified_by_name": current_user["display"],
                        "modified_at": now,
                        "old_weights": old_weights,
                        "new_weights": new_weights,
                    }
                    await cur.execute(
                        """INSERT INTO grade_weight_audit_log
                           (course_id, log_json, created_at)
                           VALUES (%s, %s, NOW())""",
                        (self.selected_course_id, json.dumps(log_entry)),
                    )

                self.status_message = "权重方案保存成功，全班总评分已自动重算"
                self.status_type = "success"
                self._sync_weights_from_pct()

            except Exception as e:
                self.status_message = f"保存失败: {e}"
                self.status_type = "error"

            self.is_saving = False

        async def load_history(self):
            """加载当前课程的历史权重方案列表"""
            if self.selected_course_id == 0:
                self.weight_history = []
                return

            try:
                from database import db as async_db
            except ImportError:
                from oaepp.database import db as async_db

            try:
                async with async_db() as cur:
                    await cur.execute(
                        """SELECT id, weights_json, modified_by, modified_at
                           FROM grade_weight_history
                           WHERE course_id = %s
                           ORDER BY modified_at DESC
                           LIMIT 50""",
                        (self.selected_course_id,),
                    )
                    rows = await cur.fetchall()
                self.weight_history = []
                for r in rows:
                    weights = json.loads(r["weights_json"]) if isinstance(r["weights_json"], str) else r["weights_json"]
                    self.weight_history.append({
                        "id": r["id"],
                        "attendance": weights.get("attendance", 25),
                        "exam": weights.get("exam", 25),
                        "code": weights.get("code", 25),
                        "pr": weights.get("pr", 25),
                        "modified_by": r.get("modified_by", ""),
                        "modified_at": r["modified_at"].isoformat() if hasattr(r["modified_at"], "isoformat") else str(r["modified_at"]),
                    })
            except Exception:
                self.weight_history = []

        async def rollback_to(self, history_id: int):
            """一键回滚至指定历史版本"""
            target = None
            for h in self.weight_history:
                if h["id"] == history_id:
                    target = h
                    break
            if target is None:
                self.status_message = "未找到该历史方案"
                self.status_type = "error"
                return

            self.attendance_pct = target["attendance"]
            self.exam_pct = target["exam"]
            self.code_pct = target["code"]
            self.pr_pct = target["pr"]
            self._sync_weights_from_pct()
            await self._refresh_heatmap()
            await self.save_weights()
            self.status_message = f"已回滚至 {target['modified_at']} 的方案"
            self.status_type = "success"

        async def load_audit_log(self):
            """加载审计日志"""
            try:
                from database import db as async_db
            except ImportError:
                from oaepp.database import db as async_db

            try:
                async with async_db() as cur:
                    if self.selected_course_id > 0:
                        await cur.execute(
                            """SELECT id, course_id, log_json, created_at
                               FROM grade_weight_audit_log
                               WHERE course_id = %s
                               ORDER BY created_at DESC
                               LIMIT 100""",
                            (self.selected_course_id,),
                        )
                    else:
                        await cur.execute(
                            """SELECT id, course_id, log_json, created_at
                               FROM grade_weight_audit_log
                               ORDER BY created_at DESC
                               LIMIT 100"""
                        )
                    rows = await cur.fetchall()
                self.audit_log = []
                for r in rows:
                    log_data = json.loads(r["log_json"]) if isinstance(r["log_json"], str) else r["log_json"]
                    old_w = log_data.get("old_weights", {}) or {}
                    new_w = log_data.get("new_weights", {}) or {}
                    self.audit_log.append({
                        "id": r["id"],
                        "course_name": log_data.get("course_name", ""),
                        "modified_by": log_data.get("modified_by_name", log_data.get("modified_by", "")),
                        "modified_at": log_data.get("modified_at", ""),
                        "old_attendance": old_w.get("attendance", 0),
                        "old_exam": old_w.get("exam", 0),
                        "old_code": old_w.get("code", 0),
                        "old_pr": old_w.get("pr", 0),
                        "new_attendance": new_w.get("attendance", 0),
                        "new_exam": new_w.get("exam", 0),
                        "new_code": new_w.get("code", 0),
                        "new_pr": new_w.get("pr", 0),
                    })
            except Exception:
                self.audit_log = []

        # ── 内部方法 ──

        @staticmethod
        def _clamp(val: int) -> int:
            return max(0, min(100, int(val or 0)))

        def _normalize_from(self, changed: str):
            """当某个维度原始值变化时，重新归一化百分比。

            规则：以当前四个原始值的比例分配 100%。
            """
            total = self.attendance_weight + self.exam_weight + self.code_weight + self.pr_weight
            if total == 0:
                self.attendance_pct = self.exam_pct = self.code_pct = self.pr_pct = 25
                return
            self.attendance_pct = round(100 * self.attendance_weight / total)
            self.exam_pct = round(100 * self.exam_weight / total)
            self.code_pct = round(100 * self.code_weight / total)
            self.pr_pct = 100 - self.attendance_pct - self.exam_pct - self.code_pct

        def _sync_weights_from_pct(self):
            """将百分比同步回原始权重值"""
            self.attendance_weight = self.attendance_pct
            self.exam_weight = self.exam_pct
            self.code_weight = self.code_pct
            self.pr_weight = self.pr_pct

        async def _refresh_heatmap(self):
            """根据当前权重与数据库中学生各维度得分，计算热力图差异数据。

            从 student_scores 表加载学生四维度得分，用新旧权重分别计算总评分，
            比较差异：绿色↑（涨分）、红色↓（降分）、灰色—（不变）。
            """
            if self.selected_course_id == 0:
                self.heatmap_data = []
                self.show_heatmap = False
                return

            # 获取数据库中的当前权重作为"旧权重"
            old = await self._get_current_db_weights()

            try:
                from database import db as async_db
            except ImportError:
                from oaepp.database import db as async_db

            try:
                async with async_db() as cur:
                    await cur.execute(
                        """SELECT student_no, full_name, attendance_score, exam_score,
                                  code_score, pr_score
                           FROM student_scores
                           WHERE course_id = %s
                           ORDER BY student_no""",
                        (self.selected_course_id,),
                    )
                    rows = await cur.fetchall()
            except Exception:
                self.heatmap_data = []
                self.show_heatmap = False
                return

            new_weights = {
                "attendance": self.attendance_pct,
                "exam": self.exam_pct,
                "code": self.code_pct,
                "pr": self.pr_pct,
            }

            up_count = down_count = unchanged_count = 0
            heatmap = []

            for r in rows:
                scores = {
                    "attendance": float(r.get("attendance_score", 0) or 0),
                    "exam": float(r.get("exam_score", 0) or 0),
                    "code": float(r.get("code_score", 0) or 0),
                    "pr": float(r.get("pr_score", 0) or 0),
                }
                old_total = sum(scores[k] * old[k] / 100.0 for k in old)
                new_total = sum(scores[k] * new_weights[k] / 100.0 for k in new_weights)

                diff = new_total - old_total
                if diff > 0.01:
                    direction = "up"
                    up_count += 1
                elif diff < -0.01:
                    direction = "down"
                    down_count += 1
                else:
                    direction = "unchanged"
                    unchanged_count += 1

                heatmap.append({
                    "student_no": r.get("student_no", ""),
                    "full_name": r.get("full_name", ""),
                    "old_total": round(old_total, 2),
                    "new_total": round(new_total, 2),
                    "diff": round(diff, 2),
                    "direction": direction,
                })

            self.heatmap_data = heatmap
            self.heatmap_summary = {"up": up_count, "down": down_count, "unchanged": unchanged_count}
            self.show_heatmap = True

        async def _get_current_db_weights(self) -> Dict[str, int]:
            """从数据库获取当前课程的权重，若无记录则返回默认 25/25/25/25"""
            if self.selected_course_id == 0:
                return {"attendance": 25, "exam": 25, "code": 25, "pr": 25}

            try:
                from database import db as async_db
            except ImportError:
                from oaepp.database import db as async_db

            try:
                async with async_db() as cur:
                    await cur.execute(
                        """SELECT attendance_weight, exam_weight, code_weight, pr_weight
                           FROM grade_weight_configs
                           WHERE course_id = %s""",
                        (self.selected_course_id,),
                    )
                    row = await cur.fetchone()
                if row:
                    return {
                        "attendance": int(row.get("attendance_weight", 25)),
                        "exam": int(row.get("exam_weight", 25)),
                        "code": int(row.get("code_weight", 25)),
                        "pr": int(row.get("pr_weight", 25)),
                    }
            except Exception:
                pass
            return {"attendance": 25, "exam": 25, "code": 25, "pr": 25}

        async def _load_current_weights(self):
            """从数据库加载当前课程的权重，更新 UI 状态"""
            w = await self._get_current_db_weights()
            self.attendance_pct = w["attendance"]
            self.exam_pct = w["exam"]
            self.code_pct = w["code"]
            self.pr_pct = w["pr"]
            self._sync_weights_from_pct()
            await self._refresh_heatmap()

        async def _get_current_user(self) -> Dict[str, Any]:
            """获取当前操作用户信息，返回 {"id": int, "display": "姓名(学号)"}"""
            try:
                from states.auth import AuthState
            except ImportError:
                try:
                    from oaepp.states.auth import AuthState
                except ImportError:
                    return {"id": 0, "display": "unknown"}
            try:
                auth = await self.get_state(AuthState)
                uid = auth.current_user_id or 0
                name = auth.current_full_name or ""
                sno = auth.current_student_no or ""
                display = f"{name}({sno})" if name or sno else "unknown"
                return {"id": uid, "display": display}
            except Exception:
                return {"id": 0, "display": "unknown"}

    # 向后兼容别名
    TeacherGradeWeightState = GradeWeightState

else:
    TeacherGradeWeightState = None
