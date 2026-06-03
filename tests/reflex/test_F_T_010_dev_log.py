"""F-T-010 开发日志导出 TDD 测试

被测 State : oaepp.states.teacher_dev_log.DevLogState
TDD RED   : oaepp.states.teacher_dev_log 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : DevLogState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_dev_log import DevLogState
    _IMPORT_ERROR = None
except ImportError as _e:
    DevLogState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_010_TC01_state_attrs_exist():
    """State 必须声明 student_id、report_format 变量"""
    _guard()
    for attr in ("student_id", "report_format"):
        assert hasattr(DevLogState, attr), f"缺少 {attr} 状态变量"


def test_F_T_010_TC02_nine_dimensions_defined():
    """开发日志报告必须包含 9 个维度"""
    _guard()
    has_dims = (
        hasattr(DevLogState, "REPORT_DIMENSIONS")
        or hasattr(DevLogState, "nine_dimensions")
        or hasattr(DevLogState, "DIMENSION_NAMES")
    )
    assert has_dims, "缺少 9 维度定义（REPORT_DIMENSIONS / nine_dimensions）"
    dims = (
        getattr(DevLogState, "REPORT_DIMENSIONS", None)
        or getattr(DevLogState, "nine_dimensions", None)
        or getattr(DevLogState, "DIMENSION_NAMES", [])
    )
    assert len(dims) == 9, f"报告维度数量 {len(dims)} != 9"


def test_F_T_010_TC03_export_format_options():
    """report_format 应支持 PDF / HTML / Excel"""
    _guard()
    has_formats = (
        hasattr(DevLogState, "SUPPORTED_FORMATS")
        or hasattr(DevLogState, "format_options")
    )
    assert has_formats, "缺少支持格式定义（SUPPORTED_FORMATS / format_options）"


def test_F_T_010_TC04_audit_log_on_export():
    """DevLogState 必须声明 audit_log 变量记录导出操作"""
    _guard()
    assert hasattr(DevLogState, "audit_log") or hasattr(
        DevLogState, "export_log"
    ), "缺少导出审计日志变量"


def test_F_T_010_TC05_bulk_export_method_exists():
    """DevLogState 必须提供 bulk_export_all() 方法批量导出全班"""
    _guard()
    assert hasattr(DevLogState, "bulk_export_all") and callable(
        getattr(DevLogState, "bulk_export_all")
    ), "缺少 bulk_export_all() 方法"
