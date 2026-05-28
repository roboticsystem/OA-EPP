"""F-S-020 作业提交 TDD 测试

被测 State : oaepp.states.submission.SubmissionState
TDD RED   : oaepp.states.submission 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : SubmissionState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.submission import SubmissionState
    _IMPORT_ERROR = None
except ImportError as _e:
    SubmissionState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_020_TC01_state_attrs_exist():
    """State 必须声明 submission_success、error_message、current_file 变量"""
    _guard()
    for attr in ("submission_success", "error_message", "current_file"):
        assert hasattr(SubmissionState, attr), f"缺少 {attr} 状态变量"


def test_F_S_020_TC02_submit_method_exists():
    """SubmissionState 必须提供 submit_assignment() 事件处理器"""
    _guard()
    assert hasattr(SubmissionState, "submit_assignment") and callable(
        getattr(SubmissionState, "submit_assignment")
    ), "缺少 submit_assignment() 方法"


async def test_F_S_020_TC03_after_deadline_rejected(mem_db):
    """截止时间后提交 → error_message 包含截止相关提示"""
    _guard()
    import datetime
    state = SubmissionState()
    # 模拟截止时间已过
    past_deadline = datetime.datetime(2000, 1, 1)
    await state.submit_assignment(
        assignment_id=1,
        file_name="report.pdf",
        file_size=1024,
        deadline=past_deadline,
    )
    assert state.submission_success is False
    assert state.error_message != "", "截止后提交应设置 error_message"


async def test_F_S_020_TC04_oversized_file_rejected(mem_db):
    """文件超过限制大小 → 拒绝，error_message 非空"""
    _guard()
    import datetime
    state = SubmissionState()
    future_deadline = datetime.datetime(2099, 12, 31)
    big_size = 200 * 1024 * 1024  # 200 MB
    await state.submit_assignment(
        assignment_id=1,
        file_name="huge.zip",
        file_size=big_size,
        deadline=future_deadline,
    )
    assert state.submission_success is False
    assert state.error_message != "", "超大文件应设置 error_message"


async def test_F_S_020_TC05_invalid_format_rejected(mem_db):
    """不支持的文件格式 → 拒绝提交"""
    _guard()
    import datetime
    state = SubmissionState()
    future_deadline = datetime.datetime(2099, 12, 31)
    await state.submit_assignment(
        assignment_id=1,
        file_name="script.sh",
        file_size=512,
        deadline=future_deadline,
    )
    assert state.submission_success is False or state.error_message != "", (
        "不支持的文件格式应被拒绝"
    )


def test_F_S_020_TC06_submission_record_fields():
    """SubmissionState 必须声明 submission_time、file_size、version 相关变量"""
    _guard()
    # 至少有一种记录字段存在
    has_fields = any(
        hasattr(SubmissionState, attr)
        for attr in ("submission_time", "submitted_at", "version", "file_size")
    )
    assert has_fields, "缺少提交记录字段（time/version/size）"
