"""F-T-002 VSCode 配置下发 TDD 测试

被测 State : oaepp.states.teacher_vscode.VSCodeConfigState
TDD RED   : oaepp.states.teacher_vscode 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : VSCodeConfigState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_vscode import VSCodeConfigState
    _IMPORT_ERROR = None
except ImportError as _e:
    VSCodeConfigState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_002_TC01_state_attrs_exist():
    """State 必须声明 extensions、copilot_instructions 变量"""
    _guard()
    for attr in ("extensions", "copilot_instructions"):
        assert hasattr(VSCodeConfigState, attr), f"缺少 {attr} 状态变量"


def test_F_T_002_TC02_extension_type_enum():
    """插件类型应支持 required / recommended / banned"""
    _guard()
    has_type = (
        hasattr(VSCodeConfigState, "EXTENSION_TYPES")
        or hasattr(VSCodeConfigState, "extension_type_options")
    )
    assert has_type, "缺少插件类型枚举（EXTENSION_TYPES / extension_type_options）"


def test_F_T_002_TC03_generate_extensions_json():
    """VSCodeConfigState 必须提供 generate_extensions_json() 方法"""
    _guard()
    assert hasattr(VSCodeConfigState, "generate_extensions_json") and callable(
        getattr(VSCodeConfigState, "generate_extensions_json")
    ), "缺少 generate_extensions_json() 方法"


def test_F_T_002_TC04_save_copilot_instructions():
    """VSCodeConfigState 必须提供 save_copilot_instructions() 方法"""
    _guard()
    assert hasattr(VSCodeConfigState, "save_copilot_instructions") and callable(
        getattr(VSCodeConfigState, "save_copilot_instructions")
    ), "缺少 save_copilot_instructions() 方法"
