from typing import List, Dict, Optional, Any
from datetime import datetime


class TeacherGradeExportState:
    """教师成绩导出状态，提供导出列定义、文件名模板、总分计算与审计日志。

    最小实现用于 TDD 验证：
    - `class_filter`, `course_filter`, `is_exporting`
    - `EXPORT_COLUMNS`
    - `get_export_filename()` (文件名模板)
    - `compute_total_score()`
    - `audit_log`
    """

    # 过滤与导出状态
    class_filter: Optional[str] = None
    course_filter: Optional[str] = None
    is_exporting: bool = False

    # 导出列（符合教务系统要求的标准列顺序）
    EXPORT_COLUMNS: List[str] = [
        "学号",
        "姓名",
        "GitHub用户名",
        "班级",
        "课程名称",
        "平时成绩",
        "实验成绩",
        "期末成绩",
        "总评成绩",
        "等级",
        "备注",
    ]

    # 文件名模板
    FILENAME_TEMPLATE: str = "{course}_{clazz}_{semester}_成绩单_{date}.xlsx"

    # 审计日志
    audit_log: List[Dict[str, Any]] = []

    def __init__(self, teacher: Optional[str] = None):
        self.class_filter = None
        self.course_filter = None
        self.is_exporting = False
        self.audit_log = []
        self._preview_buffer: List[Dict[str, Any]] = []
        self._teacher = teacher or "unknown"

    def get_export_filename(self, course: str, clazz: str, semester: str, date: Optional[datetime] = None) -> str:
        d = (date or datetime.now()).strftime("%Y%m%d")
        safe_course = course.replace(" ", "_")
        safe_clazz = clazz.replace(" ", "_")
        return self.FILENAME_TEMPLATE.format(course=safe_course, clazz=safe_clazz, semester=semester, date=d)

    def compute_total_score(self, scores: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
        """根据各项权重计算总分。

        scores: 各维度得分，例如 {"平时": 85, "实验": 90, "期末": 80}
        weights: 各维度权重（0-100），如果未提供使用默认权重。
        返回值为保留两位小数的总分（0-100）。
        """
        default_weights = {"平时": 30.0, "实验": 20.0, "期末": 50.0}
        w = weights or default_weights
        total = 0.0
        for key, weight in w.items():
            val = float(scores.get(key, 0.0))
            total += val * (weight / 100.0)
        return round(total, 2)

    def preview_export(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """返回可编辑的预览缓冲区（前端可据此逐单元格修改）。"""
        self._preview_buffer = [dict(r) for r in records]
        return self._preview_buffer

    def apply_preview_edit(self, row_index: int, column: str, value: Any) -> bool:
        if 0 <= row_index < len(self._preview_buffer):
            self._preview_buffer[row_index][column] = value
            return True
        return False

    def export(self, exporter: str, course: str, clazz: str, semester: str, records: List[Dict[str, Any]], conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行导出（此处仅记录审计并返回导出元数据）。"""
        filename = self.get_export_filename(course, clazz, semester)
        self.is_exporting = True
        try:
            entry = {
                "exporter": exporter,
                "time": datetime.now().isoformat(),
                "conditions": conditions or {"class": clazz, "course": course, "semester": semester},
                "record_count": len(records),
                "filename": filename,
            }
            self.audit_log.append(entry)
            return {"filename": filename, "record_count": len(records), "audit_entry": entry}
        finally:
            self.is_exporting = False


__all__ = ["TeacherGradeExportState"]
