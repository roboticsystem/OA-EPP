"""F-T-006 需求文档编辑器 TDD 测试

被测 State : oaepp.states.req_editor.ReqEditorState
TDD RED   : oaepp.states.req_editor 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ReqEditorState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.req_editor import ReqEditorState
    _IMPORT_ERROR = None
except ImportError as _e:
    ReqEditorState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_006_TC01_state_attrs_exist():
    """State 必须声明 content、is_sealed、preview_html 变量"""
    _guard()
    for attr in ("content", "is_sealed", "preview_html"):
        assert hasattr(ReqEditorState, attr), f"缺少 {attr} 状态变量"


def test_F_T_006_TC02_save_and_commit_method_exists():
    """ReqEditorState 必须提供 save_and_commit() 方法"""
    _guard()
    assert hasattr(ReqEditorState, "save_and_commit") and callable(
        getattr(ReqEditorState, "save_and_commit")
    ), "缺少 save_and_commit() 方法"


async def test_F_T_006_TC03_seal_document(mem_db):
    """seal_document() 设置 is_sealed=True 后不允许修改"""
    _guard()
    state = ReqEditorState()
    await state.seal_document()
    assert state.is_sealed is True, "seal_document() 后 is_sealed 应为 True"


def test_F_T_006_TC04_format_validation():
    """ReqEditorState 必须支持 F-xxx 格式需求点的合法性验证"""
    _guard()
    has_validate = (
        hasattr(ReqEditorState, "validate_format")
        or hasattr(ReqEditorState, "validate_req_format")
        or hasattr(ReqEditorState, "REQ_PATTERN")
    )
    assert has_validate, "缺少需求格式校验方法或正则模式"
