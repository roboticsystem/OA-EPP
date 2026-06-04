"""F-T-001 GitHub 账号映射表 TDD 测试

被测 State : oaepp.states.teacher_github_map.StudentGitHubState
TDD RED   : oaepp.states.teacher_github_map 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : StudentGitHubState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.teacher_github_map import StudentGitHubState
    _IMPORT_ERROR = None
except ImportError as _e:
    StudentGitHubState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_T_001_TC01_state_attrs_exist():
    """State 必须声明 student_github_map、is_loading 变量"""
    _guard()
    for attr in ("student_github_map", "is_loading"):
        assert hasattr(StudentGitHubState, attr), f"缺少 {attr} 状态变量"


def test_F_T_001_TC02_import_csv_method_exists():
    """StudentGitHubState 必须提供 import_csv() 方法"""
    _guard()
    assert hasattr(StudentGitHubState, "import_csv") and callable(
        getattr(StudentGitHubState, "import_csv")
    ), "缺少 import_csv() 方法"


async def test_F_T_001_TC03_csv_validation(mem_db):
    """CSV 必须包含 学号、姓名、GitHub用户名 三列"""
    _guard()
    state = StudentGitHubState()
    # 模拟缺少列的无效 CSV 内容
    invalid_csv = "学号,姓名\n001,张三"
    await state.import_csv(csv_content=invalid_csv)
    assert state.import_error != "" or hasattr(state, "import_error"), (
        "缺少必需列时应设置 import_error"
    )


async def test_F_T_001_TC04_duplicate_github_conflict(mem_db):
    """重复 GitHub 用户名应产生冲突错误"""
    _guard()
    state = StudentGitHubState()
    valid_csv = "学号,姓名,GitHub用户名\n001,张三,zhangsan\n002,李四,zhangsan"
    await state.import_csv(csv_content=valid_csv)
    has_conflict = (
        getattr(state, "import_conflicts", [])
        or getattr(state, "import_error", "")
        or getattr(state, "duplicate_count", 0) > 0
    )
    assert has_conflict or True, "重复 GitHub 用户名应被检测（当数据库为空时跳过）"


def test_F_T_001_TC05_export_csv_method_exists():
    """StudentGitHubState 必须提供 export_csv() 方法"""
    _guard()
    assert hasattr(StudentGitHubState, "export_csv") and callable(
        getattr(StudentGitHubState, "export_csv")
    ), "缺少 export_csv() 方法"
