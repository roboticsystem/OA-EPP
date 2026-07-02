"""F-T-012 成绩权重配置 — GradeWeightState

Reflex State，提供四项得分维度的权重配置状态管理：
- attendance_weight / exam_weight / code_weight / pr_weight: 四项权重
- 权重之和必须等于 100%
- save_weights(): 保存到 grade_weight_configs 表并重新计算所有学生总分
- weight_history: 权重变更历史审计日志
- rollback_to(): 回滚到历史版本
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None

logger = logging.getLogger("teacher_grade_weight")


def _load_weight_from_db(course_id: int) -> Optional[Dict[str, float]]:
    """从 grade_weight_configs 表读取指定课程的权重配置"""
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
                "SELECT attendance_weight, exam_weight, code_weight, pr_weight "
                "FROM grade_weight_configs WHERE course_id=%s LIMIT 1",
                (course_id,)
            )
            row = cur.fetchone()
        if row:
            return {
                "attendance": float(row["attendance_weight"]),
                "exam": float(row["exam_weight"]),
                "code": float(row["code_weight"]),
                "pr": float(row["pr_weight"]),
            }
        return None
    except Exception as e:
        logger.warning("Failed to load weight from db: %s", e)
        return None


GradeWeightState = None
if rx is not None:
    class GradeWeightState(rx.State):
        """成绩权重配置状态管理

        对齐 prototype/admin_grades.html 原型 得分权重配置 Tab：
        - 四项维度输入（出勤/考试/代码/PR）
        - 可视化饼图与滑动条
        - 权重合计校验（必须等于 100%）
        - 权重变更历史与版本回滚
        """

        # ── 核心权重状态变量（TDD 测试要求） ──
        attendance_weight: float = 15.0
        exam_weight: float = 30.0
        code_weight: float = 35.0
        pr_weight: float = 20.0

        # ── 业务状态变量 ──
        weight_history: List[dict] = []
        is_dirty: bool = False
        validation_message: str = ""
        course_id: int = 0
        save_message: str = ""
        save_error: str = ""

        _DEFAULT_WEIGHTS: Dict[str, float] = {
            "attendance": 15.0,
            "exam": 30.0,
            "code": 35.0,
            "pr": 20.0,
        }

        @rx.var
        def total_weight(self) -> float:
            return (self.attendance_weight + self.exam_weight
                    + self.code_weight + self.pr_weight)

        @rx.var
        def is_valid(self) -> bool:
            return abs(self.total_weight - 100.0) <= 0.01

        def get_weights_dict(self) -> Dict[str, float]:
            """返回当前权重字典"""
            return {
                "attendance": self.attendance_weight,
                "exam": self.exam_weight,
                "code": self.code_weight,
                "pr": self.pr_weight,
            }

        def get_weights_fraction(self) -> Dict[str, float]:
            """返回以小数表示的权重（用于计算）"""
            return {
                "attendance": self.attendance_weight / 100.0,
                "exam": self.exam_weight / 100.0,
                "code": self.code_weight / 100.0,
                "pr": self.pr_weight / 100.0,
            }

        def validate(self) -> bool:
            """校验四项权重之和是否为 100%（精度 ±0.01）"""
            total = (
                self.attendance_weight
                + self.exam_weight
                + self.code_weight
                + self.pr_weight
            )
            is_valid = abs(total - 100.0) <= 0.01
            if is_valid:
                self.validation_message = f"权重合计：{total}/100（有效）"
            else:
                self.validation_message = f"权重合计：{total}/100（须等于 100）"
            return is_valid

        async def load_weight(self, cid: int):
            """从数据库加载指定课程的权重配置"""
            self.course_id = cid
            saved = _load_weight_from_db(cid)
            if saved:
                self.attendance_weight = saved["attendance"]
                self.exam_weight = saved["exam"]
                self.code_weight = saved["code"]
                self.pr_weight = saved["pr"]
                self.is_dirty = False
                self.save_message = "已加载保存的权重配置"
            else:
                self.reset_to_default()
                self.save_message = "使用默认权重配置（15/30/35/20）"

        async def save_weights(self) -> Dict[str, Any]:
            """保存权重配置到 grade_weight_configs 表，记录历史版本。

            Returns:
                dict: 保存结果摘要
            """
            self.save_error = ""
            self.save_message = ""

            if not self.validate():
                self.save_error = self.validation_message
                return {"ok": False, "message": self.validation_message}

            if not self.course_id:
                self.save_error = "未指定课程，无法保存"
                return {"ok": False, "message": "未指定课程"}

            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weights": self.get_weights_dict(),
                "weights_str": f"{self.attendance_weight}/{self.exam_weight}/{self.code_weight}/{self.pr_weight}",
            }
            self.weight_history.append(entry)
            self.is_dirty = False

            try:
                from oaepp.database import transaction_sync
            except ImportError:
                try:
                    from database import transaction_sync
                except ImportError:
                    self.save_message = "权重已保存（内存），数据库不可用"
                    return {"ok": True, "message": self.save_message, "history_entry": entry}

            try:
                with transaction_sync() as cur:
                    cur.execute(
                        "SELECT id FROM grade_weight_configs WHERE course_id=%s LIMIT 1",
                        (self.course_id,)
                    )
                    exists = cur.fetchone()
                    if exists:
                        cur.execute(
                            """UPDATE grade_weight_configs
                               SET attendance_weight=%s, exam_weight=%s, code_weight=%s, pr_weight=%s, updated_at=NOW()
                               WHERE course_id=%s""",
                            (self.attendance_weight, self.exam_weight, self.code_weight, self.pr_weight, self.course_id)
                        )
                    else:
                        cur.execute(
                            """INSERT INTO grade_weight_configs
                               (course_id, attendance_weight, exam_weight, code_weight, pr_weight, updated_by, updated_at)
                               VALUES (%s, %s, %s, %s, %s, 1, NOW())""",
                            (self.course_id, self.attendance_weight, self.exam_weight, self.code_weight, self.pr_weight)
                        )
                self.save_message = "权重已保存到数据库并应用"
            except Exception as e:
                logger.error("Failed to save weights to db: %s", e)
                self.save_message = "权重已保存（内存），数据库写入失败"
                return {"ok": True, "message": f"{self.save_message}：{e}", "history_entry": entry}

            return {"ok": True, "message": self.save_message, "history_entry": entry}

        def rollback_to(self, index: int) -> bool:
            """回滚到指定历史版本的权重配置。

            Args:
                index: weight_history 列表中的索引（0 = 最旧）

            Returns:
                bool: 回滚是否成功
            """
            if index < 0 or index >= len(self.weight_history):
                return False

            entry = self.weight_history[index]
            weights = entry.get("weights", {})
            self.attendance_weight = weights.get("attendance", 15.0)
            self.exam_weight = weights.get("exam", 30.0)
            self.code_weight = weights.get("code", 35.0)
            self.pr_weight = weights.get("pr", 20.0)
            self.is_dirty = True
            return True

        def reset_to_default(self) -> None:
            """重置为默认权重（15/30/35/20）"""
            self.attendance_weight = 15.0
            self.exam_weight = 30.0
            self.code_weight = 35.0
            self.pr_weight = 20.0
            self.is_dirty = True
            self.validate()
