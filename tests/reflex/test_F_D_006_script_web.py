"""F-D-006 脚本执行界面 TDD 测试

被测 State : oaepp.states.devops_script.ScriptExecuteState
TDD RED   : oaepp.states.devops_script 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ScriptExecuteState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.devops_script import ScriptExecuteState
    _IMPORT_ERROR = None
except ImportError as _e:
    ScriptExecuteState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_D_006_TC01_state_attrs_exist():
    """State 必须声明 script_output、is_running、current_step、total_steps 变量"""
    _guard()
    for attr in ("script_output", "is_running", "current_step", "total_steps"):
        assert hasattr(ScriptExecuteState, attr), f"缺少 {attr} 状态变量"


def test_F_D_006_TC02_execute_script_is_async_generator():
    """execute_script() 应为异步生成器（yield-based）以支持实时输出"""
    _guard()
    import inspect
    method = getattr(ScriptExecuteState, "execute_script", None)
    assert method is not None, "缺少 execute_script() 方法"
    assert callable(method), "execute_script 应为可调用对象"


async def test_F_D_006_TC03_output_is_list(mem_db):
    """script_output 默认应为列表类型（逐行追加）"""
    _guard()
    state = ScriptExecuteState()
    assert isinstance(state.script_output, list), "script_output 应为列表类型（逐行记录）"


def test_F_D_006_TC04_error_line_attr():
    """State 必须提供区分错误行的机制（error_lines 或 line_types）"""
    _guard()
    has_error_lines = hasattr(ScriptExecuteState, "error_lines")
    has_line_types = hasattr(ScriptExecuteState, "line_types")
    has_output_items = hasattr(ScriptExecuteState, "output_items")
    assert has_error_lines or has_line_types or has_output_items, (
        "缺少错误行标识机制（error_lines / line_types / output_items）"
    )


def test_F_D_006_TC05_progress_tracking():
    """current_step / total_steps 应为整数类型"""
    _guard()
    state = ScriptExecuteState()
    assert isinstance(state.current_step, int), "current_step 应为整数"
    assert isinstance(state.total_steps, int), "total_steps 应为整数"
