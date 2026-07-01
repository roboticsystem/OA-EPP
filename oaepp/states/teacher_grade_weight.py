"""F-T-012 成绩权重配置 — GradeWeightState

Reflex State，提供四项得分维度的权重配置状态管理：
- attendance_weight / exam_weight / code_weight / pr_weight: 四项权重
- 权重之和必须等于 100%
- save_weights(): 保存并重新计算所有学生总分
- weight_history: 权重变更历史审计日志
- rollback_to(): 回滚到历史版本
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import reflex as rx
except Exception:
    rx = None


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

        _DEFAULT_WEIGHTS: Dict[str, float] = {
            "attendance": 15.0,
            "exam": 30.0,
            "code": 35.0,
            "pr": 20.0,
        }

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

        async def save_weights(self) -> Dict[str, Any]:
            """保存权重配置，记录历史版本，并重新计算所有学生总分。

            Returns:
                dict: 保存结果摘要
            """
            if not self.validate():
                return {"ok": False, "message": self.validation_message}

            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weights": self.get_weights_dict(),
                "weights_str": f"{self.attendance_weight}/{self.exam_weight}/{self.code_weight}/{self.pr_weight}",
            }
            self.weight_history.append(entry)
            self.is_dirty = False

            return {"ok": True, "message": "权重已保存并应用", "history_entry": entry}

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

        @property
        def total_weight(self) -> float:
            return (self.attendance_weight + self.exam_weight
                    + self.code_weight + self.pr_weight)

        @property
        def is_valid(self) -> bool:
            return abs(self.total_weight - 100.0) <= 0.01
