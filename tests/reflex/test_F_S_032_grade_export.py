"""F-S-032 成绩导出（学生端）TDD 测试

被测 State : oaepp.states.grade_export.GradeExportState
TDD RED   : oaepp.states.grade_export 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : GradeExportState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.grade_export import GradeExportState
    _IMPORT_ERROR = None
except ImportError as _e:
    GradeExportState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_032_TC01_state_attrs_exist():
    """State 必须声明 is_exporting、export_error 变量"""
    _guard()
    for attr in ("is_exporting", "export_error"):
        assert hasattr(GradeExportState, attr), f"缺少 {attr} 状态变量"


def test_F_S_032_TC02_export_method_exists():
    """GradeExportState 必须提供 export_my_grades() 方法"""
    _guard()
    assert hasattr(GradeExportState, "export_my_grades") and callable(
        getattr(GradeExportState, "export_my_grades")
    ), "缺少 export_my_grades() 方法"


def test_F_S_032_TC03_filename_format_attr():
    """State 必须提供 export_filename 属性，格式为 学号_姓名_成绩单_课程名称.xlsx"""
    _guard()
    has_attr = hasattr(GradeExportState, "export_filename")
    has_method = hasattr(GradeExportState, "get_export_filename")
    assert has_attr or has_method, "缺少导出文件名属性/方法"


def test_F_S_032_TC04_data_isolation_attr():
    """State 必须携带 current_user_id 确保只导出自身数据"""
    _guard()
    assert hasattr(GradeExportState, "current_user_id"), "缺少 current_user_id 隔离变量"
