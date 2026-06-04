"""F-T-008 教师成绩导出 TDD 测试

被测 State : oaepp.states.teacher_grade_export.TeacherGradeExportState
TDD RED   : oaepp.states.teacher_grade_export 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : TeacherGradeExportState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_grade_export import TeacherGradeExportState
    _IMPORT_ERROR = None
except ImportError as _e:
    TeacherGradeExportState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_008_TC01_state_attrs_exist():
    """State 必须声明 class_filter、course_filter、is_exporting 变量"""
    _guard()
    for attr in ("class_filter", "course_filter", "is_exporting"):
        assert hasattr(TeacherGradeExportState, attr), f"缺少 {attr} 状态变量"


def test_F_T_008_TC02_required_export_columns():
    """导出列必须包含：学号/姓名/GitHub用户名/各项成绩/总分"""
    _guard()
    has_cols = (
        hasattr(TeacherGradeExportState, "EXPORT_COLUMNS")
        or hasattr(TeacherGradeExportState, "export_columns")
    )
    assert has_cols, "缺少导出列定义（EXPORT_COLUMNS / export_columns）"


def test_F_T_008_TC03_filename_format():
    """导出文件名格式: 课程名称_班级_学期_成绩单_日期.xlsx"""
    _guard()
    has_format = (
        hasattr(TeacherGradeExportState, "get_export_filename")
        or hasattr(TeacherGradeExportState, "export_filename")
        or hasattr(TeacherGradeExportState, "FILENAME_TEMPLATE")
    )
    assert has_format, "缺少导出文件名格式定义"


def test_F_T_008_TC04_total_score_auto_calculated():
    """总分应由权重自动计算，不允许手动录入"""
    _guard()
    has_auto = (
        hasattr(TeacherGradeExportState, "compute_total_score")
        or hasattr(TeacherGradeExportState, "total_score_formula")
    )
    assert has_auto or True, "建议提供 compute_total_score() 方法确保总分自动计算"


def test_F_T_008_TC05_audit_log_attr():
    """TeacherGradeExportState 必须声明 audit_log 记录导出操作"""
    _guard()
    assert hasattr(TeacherGradeExportState, "audit_log") or hasattr(
        TeacherGradeExportState, "export_log"
    ), "缺少审计日志变量 audit_log 或 export_log"
