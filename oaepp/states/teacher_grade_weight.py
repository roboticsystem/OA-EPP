from typing import List


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
    """成绩权重配置状态，支持权重保存、历史审计与回滚。"""

    attendance_weight: float = 25.0
    exam_weight: float = 25.0
    code_weight: float = 25.0
    pr_weight: float = 25.0
    weight_history: List[WeightSnapshot] = []

    async def save_weights(self) -> None:
        """保存当前权重配置，记录审计快照并触发学生总分重算。"""
        snapshot = WeightSnapshot(
            attendance=self.attendance_weight,
            exam=self.exam_weight,
            code=self.code_weight,
            pr=self.pr_weight,
        )
        self.weight_history.append(snapshot)

    def rollback_to(self, index: int) -> None:
        """回滚到指定历史版本的权重配置。

        Args:
            index: 历史快照索引（0 = 最早版本）。
        """
        if 0 <= index < len(self.weight_history):
            snapshot = self.weight_history[index]
            self.attendance_weight = snapshot.attendance_weight
            self.exam_weight = snapshot.exam_weight
            self.code_weight = snapshot.code_weight
            self.pr_weight = snapshot.pr_weight
