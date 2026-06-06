"""F-T-012 成绩权重配置 — GradeWeightState

教师可通过滑块与数字输入框可视化调整四维度评分权重，
实时热力图预览对全班总评分的影响，支持历史方案回滚与审计日志。

维度: attendance(出勤) / exam(考试) / code(代码提交) / pr(PR贡献)
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from oaepp.models.database import WeightScheme, WeightAuditLog


class WeightSnapshot:
    """权重快照，用于审计历史记录。"""

    attendance_weight: float
    exam_weight: float
    code_weight: float
    pr_weight: float

    def __init__(self, attendance: float, exam: float, code: float, pr: float):
        self.attendance_weight = attendance
        self.exam_weight = exam
        self.code_weight = code
        self.pr_weight = pr


class GradeWeightState:
    """成绩权重配置状态，支持权重保存、热力图预览、历史审计与回滚。"""

    # ── 四维度权重 (默认 25% 各，总和 100%) ──
    attendance_weight: float = 25.0
    exam_weight: float = 25.0
    code_weight: float = 25.0
    pr_weight: float = 25.0

    # ── 当前课程 / 方案元信息 ──
    course_id: str = "default"
    current_scheme_id: Optional[int] = None
    scheme_name: str = "默认方案"

    # ── 历史与审计 ──
    weight_history: List[WeightSnapshot] = []
    audit_log: List[Dict[str, Any]] = []

    # ── 热力图预览数据 ──
    heatmap_data: List[Dict[str, Any]] = []

    # ── 归一化内部状态 ──
    _anchor_index: int = 0  # 0=attendance, 1=exam, 2=code, 3=pr
    _normalizing: bool = False

    # ──────────── 归一化 ────────────

    def _enforce_sum(self):
        """确保四项权重之和为 100%（以 _anchor_index 为锚定维度，缩放其余三个）。"""
        if self._normalizing:
            return
        self._normalizing = True
        try:
            w = [self.attendance_weight, self.exam_weight,
                 self.code_weight, self.pr_weight]
            total = sum(w)
            if abs(total - 100.0) < 0.001:
                return
            if total <= 0:
                self.attendance_weight = self.exam_weight = self.code_weight = self.pr_weight = 25.0
                return
            anchor = max(0, min(3, self._anchor_index))
            anchor_val = w[anchor]
            others = [w[i] for i in range(4) if i != anchor]
            others_sum = sum(others)
            scale = (100.0 - anchor_val) / others_sum if others_sum > 0.001 else 0.0
            new_w = [0.0, 0.0, 0.0, 0.0]
            new_w[anchor] = anchor_val
            for i, idx in enumerate([j for j in range(4) if j != anchor]):
                new_w[idx] = round(others[i] * scale, 2)
            leftover = 100.0 - sum(new_w)
            non_anchor = [j for j in range(4) if j != anchor]
            if non_anchor:
                new_w[non_anchor[-1]] = round(new_w[non_anchor[-1]] + leftover, 2)
            self.attendance_weight = new_w[0]
            self.exam_weight = new_w[1]
            self.code_weight = new_w[2]
            self.pr_weight = new_w[3]
        finally:
            self._normalizing = False

    # ──────────── 滑块联动 setter ────────────

    def set_attendance_weight(self, v: float):
        self._anchor_index = 0
        self.attendance_weight = max(0.0, min(100.0, float(v)))
        self._enforce_sum()

    def set_exam_weight(self, v: float):
        self._anchor_index = 1
        self.exam_weight = max(0.0, min(100.0, float(v)))
        self._enforce_sum()

    def set_code_weight(self, v: float):
        self._anchor_index = 2
        self.code_weight = max(0.0, min(100.0, float(v)))
        self._enforce_sum()

    def set_pr_weight(self, v: float):
        self._anchor_index = 3
        self.pr_weight = max(0.0, min(100.0, float(v)))
        self._enforce_sum()

    # ──────────── 加权总分计算 ────────────

    @staticmethod
    def compute_weighted_total(
        attendance_score: float, exam_score: float,
        code_score: float, pr_score: float,
        weights: Tuple[float, float, float, float],
    ) -> float:
        """根据四维度原始得分与权重百分比计算加权总分。"""
        return round(
            attendance_score * weights[0] / 100.0
            + exam_score * weights[1] / 100.0
            + code_score * weights[2] / 100.0
            + pr_score * weights[3] / 100.0,
            2,
        )

    def current_weights(self) -> Tuple[float, float, float, float]:
        return (self.attendance_weight, self.exam_weight,
                self.code_weight, self.pr_weight)

    def heatmap_summary(self) -> Dict[str, int]:
        """返回热力图差异统计：green(涨分), red(降分), gray(不变)。"""
        counts = {"green": 0, "red": 0, "gray": 0}
        for item in self.heatmap_data:
            c = item.get("color", "gray")
            if c in counts:
                counts[c] += 1
        return counts

    # ──────────── 热力图预览 ────────────

    async def preview_heatmap(self, scores: Optional[List[Dict[str, Any]]] = None):
        """对照当前权重方案，计算新旧总分的差异热力图数据。

        颜色含义: green(↑涨分), red(↓降分), gray(不变)。
        """
        if not scores:
            self.heatmap_data = []
            return
        nw = (self.attendance_weight / 100.0, self.exam_weight / 100.0,
              self.code_weight / 100.0, self.pr_weight / 100.0)
        result = []
        for s in scores:
            a = float(s.get("attendance_score", 0) or 0)
            e = float(s.get("exam_score", 0) or 0)
            c = float(s.get("code_score", 0) or 0)
            p = float(s.get("pr_score", 0) or 0)
            total_new = round(a * nw[0] + e * nw[1] + c * nw[2] + p * nw[3], 2)
            total_old = float(s.get("old_total", total_new))
            delta = round(total_new - total_old, 2)
            color = "green" if delta > 0.01 else ("red" if delta < -0.01 else "gray")
            result.append({
                "student_id": s.get("student_id", ""),
                "name": s.get("name", ""),
                "old_total": total_old,
                "new_total": total_new,
                "delta": delta,
                "color": color,
            })
        self.heatmap_data = result

    # ──────────── 保存 & 审计 ────────────

    async def save_weights(self, session=None, modified_by: str = "teacher") -> None:
        """保存当前权重配置，记录审计快照并触发学生总分重算。"""
        old = await self._load_active_scheme(session)
        old_w = old.weights_tuple if old else (25.0, 25.0, 25.0, 25.0)

        # 内存快照
        snapshot = WeightSnapshot(
            attendance=self.attendance_weight, exam=self.exam_weight,
            code=self.code_weight, pr=self.pr_weight,
        )
        self.weight_history.append(snapshot)

        # 持久化 WeightScheme
        scheme = WeightScheme(
            course_id=self.course_id, name=self.scheme_name,
            attendance_weight=self.attendance_weight,
            exam_weight=self.exam_weight,
            code_weight=self.code_weight,
            pr_weight=self.pr_weight,
            created_by=modified_by, created_at=datetime.now(),
        )
        if session is not None:
            session.add(scheme)
            session.commit()
            session.refresh(scheme)
        self.current_scheme_id = scheme.id

        # 审计日志（不可删除）
        audit = WeightAuditLog(
            scheme_id=scheme.id, modified_by=modified_by,
            modified_at=datetime.now(),
            old_attendance=old_w[0], old_exam=old_w[1],
            old_code=old_w[2], old_pr=old_w[3],
            new_attendance=self.attendance_weight,
            new_exam=self.exam_weight,
            new_code=self.code_weight,
            new_pr=self.pr_weight,
        )
        audit_dict = {
            "id": audit.id, "scheme_id": audit.scheme_id,
            "modified_by": modified_by,
            "modified_at": audit.modified_at.isoformat(),
            "old_attendance": audit.old_attendance,
            "old_exam": audit.old_exam,
            "old_code": audit.old_code,
            "old_pr": audit.old_pr,
            "new_attendance": audit.new_attendance,
            "new_exam": audit.new_exam,
            "new_code": audit.new_code,
            "new_pr": audit.new_pr,
        }
        if session is not None:
            session.add(audit)
            session.commit()
            audit_dict["id"] = audit.id
        self.audit_log.append(audit_dict)

    async def _load_active_scheme(self, session=None) -> Optional[WeightScheme]:
        if session is not None:
            from sqlmodel import select
            stmt = (select(WeightScheme)
                    .where(WeightScheme.course_id == self.course_id)
                    .order_by(WeightScheme.created_at.desc())
                    .limit(1))
            return session.exec(stmt).first()
        return None

    # ──────────── 历史回滚 ────────────

    def rollback_to(self, index: int, session=None, modified_by: str = "teacher") -> None:
        """回滚到指定历史版本的权重配置。

        Args:
            index: 历史快照索引（0 = 最早版本）。
            session: SQLModel session，传入则同时持久化回滚。
        """
        if 0 <= index < len(self.weight_history):
            snapshot = self.weight_history[index]
            self.attendance_weight = snapshot.attendance_weight
            self.exam_weight = snapshot.exam_weight
            self.code_weight = snapshot.code_weight
            self.pr_weight = snapshot.pr_weight
            self.scheme_name = "回滚方案"
            # 触发异步保存（不在同步方法内 await，由调用者处理）
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        self.save_weights(session=session, modified_by=modified_by)
                    )
            except RuntimeError:
                pass

    # ──────────── 历史查询 ────────────

    async def load_history(self, session=None) -> List[Dict[str, Any]]:
        """获取当前课程的全部历史权重方案（含修改时间、修改人）。"""
        if session is not None:
            from sqlmodel import select
            stmt = (select(WeightScheme)
                    .where(WeightScheme.course_id == self.course_id)
                    .order_by(WeightScheme.created_at.desc()))
            rows = session.exec(stmt).all()
            return [{
                "scheme_id": r.id, "name": r.name,
                "attendance_weight": r.attendance_weight,
                "exam_weight": r.exam_weight,
                "code_weight": r.code_weight,
                "pr_weight": r.pr_weight,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat(),
            } for r in rows]
        return [{"index": i, "attendance_weight": s.attendance_weight,
                 "exam_weight": s.exam_weight, "code_weight": s.code_weight,
                 "pr_weight": s.pr_weight}
                for i, s in enumerate(self.weight_history)]

    async def load_audit_log(self, session=None) -> List[Dict[str, Any]]:
        """获取当前课程的全部审计日志（不可删除）。"""
        if session is not None:
            from sqlmodel import select
            stmt = (select(WeightAuditLog)
                    .join(WeightScheme, WeightAuditLog.scheme_id == WeightScheme.id)
                    .where(WeightScheme.course_id == self.course_id)
                    .order_by(WeightAuditLog.modified_at.desc()))
            return [{
                "id": r.id, "scheme_id": r.scheme_id,
                "modified_by": r.modified_by,
                "modified_at": r.modified_at.isoformat(),
                "old_attendance": r.old_attendance,
                "old_exam": r.old_exam,
                "old_code": r.old_code,
                "old_pr": r.old_pr,
                "new_attendance": r.new_attendance,
                "new_exam": r.new_exam,
                "new_code": r.new_code,
                "new_pr": r.new_pr,
            } for r in session.exec(stmt).all()]
        return list(self.audit_log)
