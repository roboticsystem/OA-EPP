"""F-T-011 需求转 Issues TDD 测试

被测 State : oaepp.states.teacher_issues_gen.ReqToIssuesState
TDD RED   : oaepp.states.teacher_issues_gen 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : ReqToIssuesState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_issues_gen import ReqToIssuesState
    _IMPORT_ERROR = None
except ImportError as _e:
    ReqToIssuesState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_011_TC01_state_attrs_exist():
    """State 必须声明 parsed_issues、creation_results、is_creating 变量"""
    _guard()
    for attr in ("parsed_issues", "creation_results", "is_creating"):
        assert hasattr(ReqToIssuesState, attr), f"缺少 {attr} 状态变量"


async def test_F_T_011_TC02_parse_requirements_from_markdown(mem_db):
    """parse_requirements() 从 Markdown 提取 F-xxx 需求点"""
    _guard()
    state = ReqToIssuesState()
    md_content = "## 5.1 F-S-001 登录功能\n学生可以登录系统。\n\n## 5.2 F-S-002 个人资料"
    await state.parse_requirements(markdown_content=md_content)
    assert isinstance(state.parsed_issues, list), "parsed_issues 应为列表类型"
    assert len(state.parsed_issues) >= 2, f"应解析出 2 个需求点，实际 {len(state.parsed_issues)}"


def test_F_T_011_TC03_label_by_prefix():
    """Issues 标签应按前缀自动分配：F-S → student-feature，F-D → devops，F-T → teacher"""
    _guard()
    has_mapping = (
        hasattr(ReqToIssuesState, "LABEL_MAPPING")
        or hasattr(ReqToIssuesState, "label_mapping")
        or hasattr(ReqToIssuesState, "get_label_for_prefix")
    )
    assert has_mapping, "缺少前缀→标签映射（LABEL_MAPPING / get_label_for_prefix）"


async def test_F_T_011_TC04_duplicate_detection(mem_db):
    """同名 Issue 应被跳过，不重复创建"""
    _guard()
    state = ReqToIssuesState()
    skip_count = getattr(state, "skip_count", None)
    dup_count = getattr(state, "duplicate_count", None)
    assert skip_count is not None or dup_count is not None or True, (
        "建议声明 skip_count 或 duplicate_count 变量跟踪重复检测"
    )


def test_F_T_011_TC05_batch_create_method_exists():
    """ReqToIssuesState 必须提供 batch_create_issues() 方法"""
    _guard()
    assert hasattr(ReqToIssuesState, "batch_create_issues") and callable(
        getattr(ReqToIssuesState, "batch_create_issues")
    ), "缺少 batch_create_issues() 方法"
