"""F-T-008 教师成绩导出 — TeacherGradeExportState

提供教师成绩导出的状态管理：
- class_filter / course_filter: 筛选条件
- is_exporting: 导出状态标志
- EXPORT_COLUMNS: 导出列定义（学号/姓名/GitHub用户名/各项成绩/总分）
- get_export_filename(): 文件名生成
- compute_total_score(): 总分自动计算
- audit_log: 审计日志记录
"""

from typing import Any, List, Optional


class TeacherGradeExportState:
    """教师成绩导出状态管理

    对齐 prototype/admin_grades.html 原型 成绩单导出 Tab：
    - 筛选导出范围（班级/课程/学期）
    - 数据预览与手动修正个别单元格
    - 总评成绩按权重自动计算
    - 导出文件名格式：课程名称_班级_学期_成绩单_日期.xlsx
    - 操作记录审计日志

    对齐后端 API：
    - POST /api/teacher/grades/preview
    - POST /api/teacher/grades/export
    - GET /api/teacher/grades/filters
    - GET /api/teacher/grades/audit-logs
    """

    # ── 核心状态变量（TDD 测试要求） ──
    class_filter: str = ""
    course_filter: str = ""
    is_exporting: bool = False

    # ── 导出列定义 ──
    EXPORT_COLUMNS: List[str] = [
        "学号", "姓名", "班级", "课程名称",
        "出勤得分", "考试得分", "代码提交得分", "PR贡献得分",
        "总评成绩", "等级", "备注",
    ]

    # ── 文件名模板 ──
    FILENAME_TEMPLATE: str = "{course_name}_{class_name}_{term}_成绩单_{date}.xlsx"

    # ── 业务状态变量 ──
    term_filter: str = ""
    preview_rows: List[dict] = []
    selected_weights: dict = {}
    audit_log: List[dict] = []

    # ── 私有属性 ──
    _db_session: Any = None

    def __init__(self):
        self.class_filter = ""
        self.course_filter = ""
        self.term_filter = ""
        self.is_exporting = False
        self.preview_rows = []
        self.selected_weights = {}
        self.audit_log = []

    # ── 事件处理器 ──

    def set_filters(self, class_name: str = "", course_name: str = "", term: str = "") -> None:
        """设置筛选条件"""
        self.class_filter = class_name
        self.course_filter = course_name
        self.term_filter = term

    def get_export_filename(self, course_name: str = "", class_name: str = "", term: str = "") -> str:
        """生成导出文件名：课程名称_班级_学期_成绩单_日期.xlsx"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        safe_course = (course_name or self.course_filter or "课程").replace("/", "-")
        safe_class = (class_name or self.class_filter or "全班").replace("/", "-")
        safe_term = (term or self.term_filter or "").replace("/", "-")
        return f"{safe_course}_{safe_class}_{safe_term}_成绩单_{date_str}.xlsx"

    def compute_total_score(self, row: dict, weights: Optional[dict] = None) -> float:
        """根据权重公式自动计算总评成绩"""
        if not weights:
            weights = {"attendance": 0.15, "exam": 0.30, "code": 0.35, "pr": 0.20}
        total = 0.0
        for k, w in weights.items():
            try:
                v = float(row.get(k, 0) or 0)
            except Exception:
                v = 0
            total += v * float(w)
        return round(total, 2)

    def compute_grade(self, score: float) -> str:
        """根据分数计算等级"""
        if score is None:
            return ""
        try:
            s = float(score)
        except Exception:
            return ""
        if s >= 90:
            return "A"
        if s >= 80:
            return "B"
        if s >= 70:
            return "C"
        if s >= 60:
            return "D"
        return "F"

    def add_audit_log(self, actor: str, filters: dict, record_count: int) -> None:
        """添加审计日志记录"""
        from datetime import datetime
        self.audit_log.append({
            "actor": actor,
            "filters": filters,
            "record_count": record_count,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def clear_preview(self) -> None:
        """清空预览数据"""
        self.preview_rows = []
        self.is_exporting = False
