"""F-S-021 提交版本记录 TDD 测试

被测 State : oaepp.states.submission.SubmissionState（版本相关逻辑）
TDD RED   : oaepp.states.submission 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : SubmissionState 实现版本功能后 → 全部通过
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


def _seed_test_data(session, assignment_id: int = 1, submission_count: int = 3):
    """向 mem_db 插入测试用的作业和提交记录。

    Args:
        session: sqlmodel.Session（由 mem_db fixture 提供）
        assignment_id: 作业 ID
        submission_count: 要插入的提交记录数量（版本 1..N）
    """
    from sqlmodel import text as sql_text
    from datetime import datetime, timedelta

    # 插入测试作业
    # 注意：created_by / created_at / deadline 无 SQL 默认值，需显式提供
    session.execute(
        sql_text(
            "INSERT INTO assignments "
            "(id, title, course_id, allow_resubmit, late_policy, "
            "deadline, created_by, created_at) "
            "VALUES (:id, :title, 1, 1, 'deny', :deadline, 1, :now)"
        ),
        {
            "id": assignment_id,
            "title": "测试作业",
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "now": datetime.now().isoformat(),
        },
    )
    session.commit()

    # 插入多条测试提交记录
    for vno in range(1, submission_count + 1):
        session.execute(
            sql_text(
                "INSERT INTO submissions "
                "(assignment_id, student_user_id, version_no, file_url, "
                "text_content, is_late, grading_status, submitted_at) "
                "VALUES (:aid, 1, :vno, '', :text, 0, 'pending', :ts)"
            ),
            {
                "aid": assignment_id,
                "vno": vno,
                "text": f"版本 v{vno} 的内容",
                "ts": (datetime.now() - timedelta(hours=submission_count - vno)).isoformat(),
            },
        )
    session.commit()


def test_F_S_021_TC01_version_tracking_attrs():
    """State 必须声明 submission_history 或 versions 变量以跟踪版本"""
    _guard()
    has_history = hasattr(SubmissionState, "submission_history")
    has_versions = hasattr(SubmissionState, "versions")
    assert has_history or has_versions, "缺少版本历史变量 submission_history 或 versions"


def test_F_S_021_TC02_load_history_method_exists():
    """SubmissionState 必须提供 load_submission_history() 方法"""
    _guard()
    assert hasattr(SubmissionState, "load_submission_history") and callable(
        getattr(SubmissionState, "load_submission_history")
    ), "缺少 load_submission_history() 方法"


async def test_F_S_021_TC03_history_sorted_desc(mem_db):
    """历史记录应按版本号降序排列（最新在前）。

    正确的测试：通过 _db_session 注入 mem_db，验证历史按 version_no DESC 排序。
    """
    _guard()

    # 插入测试数据
    _seed_test_data(mem_db, assignment_id=1, submission_count=3)

    # 注入测试 Session 并加载历史
    state = SubmissionState()
    state._db_session = mem_db
    await state.load_submission_history(assignment_id=1)

    # 验证：submission_history 和 versions 都已填充
    history_attr = getattr(state, "submission_history", None) or getattr(state, "versions", [])
    assert isinstance(history_attr, list), "版本历史应为列表类型"
    assert len(history_attr) == 3, f"应返回 3 条记录，实际 {len(history_attr)}"

    # 验证：按 version_no 降序（最新 v3 在前）
    assert history_attr[0]["version_no"] == 3, f"第一条应为 v3，实际 v{history_attr[0]['version_no']}"
    assert history_attr[2]["version_no"] == 1, f"最后一条应为 v1，实际 v{history_attr[2]['version_no']}"

    # 验证：最新版本标记为评阅版本
    assert history_attr[0]["is_latest"] is True, "最新版本应标记 is_latest=True"
    assert "评阅版本" in history_attr[0]["grading_label"], "最新版本应有评阅标签"

    # 验证：历史版本有非"评阅"标签
    assert history_attr[1]["grading_label"] != history_attr[0]["grading_label"]


def test_F_S_021_TC04_allow_resubmit_attr():
    """State 必须声明 allow_resubmit 变量，控制是否可重新提交"""
    _guard()
    assert hasattr(SubmissionState, "allow_resubmit"), "缺少 allow_resubmit 状态变量"


def test_F_S_021_TC05_version_count_var():
    """State 应提供 version_count_text 计算属性供页面动态展示"""
    _guard()
    assert hasattr(SubmissionState, "version_count_text"), "缺少 version_count_text 计算属性"


async def test_F_S_021_TC06_load_history_populates_assignment_info(mem_db):
    """加载历史时应同时填充作业标题和 allow_resubmit 状态"""
    _guard()

    _seed_test_data(mem_db, assignment_id=2, submission_count=1)

    state = SubmissionState()
    state._db_session = mem_db
    await state.load_submission_history(assignment_id=2)

    assert state.current_assignment_title == "测试作业", (
        f"作业标题应为 '测试作业'，实际 '{state.current_assignment_title}'"
    )
    assert state.allow_resubmit is True, "allow_resubmit 应为 True"
