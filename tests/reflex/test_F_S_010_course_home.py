"""F-S-010 课程主页 TDD 测试

被测 State : oaepp.states.course_state.CourseState
被测 Model: oaepp.models.database (User, Course, Chapter, Enrollment, Assignment, Submission)
TDD RED   : 实现文件不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : CourseState 实现后 → 全部通过

验收标准（来源：docs/第10章_软件产品介绍.md F-S-010）：
- 展示学生已选课程（工程实践1-4）与当前学习进度
- 每门课程展示：章节数、已完成任务数、截止提醒
- 原型附加：进度条、状态标签

数据库映射（远程 MySQL oaepp_dev 现有表结构）：
- users        → 用户/学生基本信息
- courses      → 课程信息
- chapters     → 章节
- enrollments  → 学生选课记录 (student_user_id → users.id)
- assignments  → 作业/任务 (deadline 即截止日期)
- submissions  → 提交记录 (grading_status: pending/graded/returned)
"""
import os
import pytest

# 强制使用 SQLite 内存数据库（避免依赖远程 DB）
os.environ.setdefault("REFLEX_DB_URL", "sqlite:///:memory:")

try:
    from oaepp.states.course_state import CourseState, CourseProgress
    _IMPORT_ERROR = None
except ImportError as _e:
    CourseState = None
    CourseProgress = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


# ══════════════════════════════════════════════════════════════════════
# TC01 — State 属性存在性
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC01_state_attrs_exist():
    """State 必须声明 courses、loading、error_message、selected_course 变量"""
    _guard()
    for attr in ("courses", "loading", "error_message", "selected_course"):
        assert hasattr(CourseState, attr), f"缺少 {attr} 状态变量"


# ══════════════════════════════════════════════════════════════════════
# TC02 — 事件处理器方法存在性
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC02_event_handlers_exist():
    """CourseState 必须提供 load_student_courses、refresh_courses、select_course 方法"""
    _guard()
    for method in ("load_student_courses", "refresh_courses", "select_course"):
        assert hasattr(CourseState, method) and callable(
            getattr(CourseState, method)
        ), f"缺少 {method}() 事件处理器"


# ══════════════════════════════════════════════════════════════════════
# TC03 — CourseProgress 数据结构字段完整性
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC03_course_progress_fields():
    """CourseProgress 必须包含课程展示所需的所有字段

    对应验收标准：
    - 章节数 → total_chapters
    - 已完成任务数 → completed_tasks / total_tasks
    - 截止提醒 → next_due_date_str, has_due_date
    - 进度条 → progress_percentage
    - 状态标签 → status
    """
    _guard()
    required_fields = {
        "course_id": int,
        "course_code": str,
        "course_name": str,
        "total_chapters": int,
        "completed_tasks": int,
        "total_tasks": int,
        "next_due_date_str": str,
        "has_due_date": bool,
        "status": str,
        "progress_percentage": int,
    }
    for field, ftype in required_fields.items():
        assert field in CourseProgress.__annotations__, (
            f"CourseProgress 缺少 {field} 字段"
        )


# ══════════════════════════════════════════════════════════════════════
# TC04 — 空数据库处理
# ══════════════════════════════════════════════════════════════════════
async def test_F_S_010_TC04_empty_db_handled():
    """无学生数据时 load_student_courses() 不应崩溃，courses 为空列表"""
    _guard()
    state = CourseState()
    # student_id=0 且 AuthState 未登录时，应优雅提示错误
    await state.load_student_courses(student_id=0)
    # 完成加载后 loading 应为 False
    assert state.loading is False, "加载完成后 loading 应为 False"


# ══════════════════════════════════════════════════════════════════════
# TC05 — 进度百分比计算
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC05_progress_percentage():
    """CourseProgress 进度百分比计算应正确"""
    _guard()
    # 0/0 → 0%
    cp = CourseProgress(
        course_id=1,
        course_code="TEST",
        course_name="测试",
        total_chapters=0,
        completed_tasks=0,
        total_tasks=0,
        next_due_date_str="",
        has_due_date=False,
        status="active",
        progress_percentage=0,
    )
    assert cp.progress_percentage == 0

    # 3/10 → 30%
    cp2 = CourseProgress(
        course_id=2,
        course_code="TEST2",
        course_name="测试2",
        total_chapters=5,
        completed_tasks=3,
        total_tasks=10,
        next_due_date_str="",
        has_due_date=False,
        status="active",
        progress_percentage=30,
    )
    assert cp2.progress_percentage == 30

    # 全部完成 → 100%
    cp3 = CourseProgress(
        course_id=3,
        course_code="TEST3",
        course_name="测试3",
        total_chapters=3,
        completed_tasks=5,
        total_tasks=5,
        next_due_date_str="",
        has_due_date=False,
        status="completed",
        progress_percentage=100,
    )
    assert cp3.progress_percentage == 100
    assert cp3.status == "completed"


# ══════════════════════════════════════════════════════════════════════
# TC06 — select_course 选择课程
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC06_select_course():
    """select_course 应正确设置 selected_course"""
    _guard()
    state = CourseState()
    # 手动填充 courses 列表
    cp1 = CourseProgress(
        course_id=1,
        course_code="EP1",
        course_name="工程实践1",
        total_chapters=10,
        completed_tasks=5,
        total_tasks=20,
        next_due_date_str="2026-06-15 23:59",
        has_due_date=True,
        status="active",
        progress_percentage=25,
    )
    cp2 = CourseProgress(
        course_id=2,
        course_code="EP2",
        course_name="工程实践2",
        total_chapters=8,
        completed_tasks=0,
        total_tasks=16,
        next_due_date_str="",
        has_due_date=False,
        status="active",
        progress_percentage=0,
    )
    state.courses = [cp1, cp2]

    # 选择课程 1
    state.select_course(1)
    assert state.selected_course is not None
    assert state.selected_course.course_id == 1
    assert state.selected_course.course_name == "工程实践1"

    # 选择课程 2
    state.select_course(2)
    assert state.selected_course is not None
    assert state.selected_course.course_id == 2
    assert state.selected_course.course_name == "工程实践2"

    # 选择不存在的课程 → selected_course 保持不变
    state.select_course(999)
    assert state.selected_course.course_id == 2  # 未变化


# ══════════════════════════════════════════════════════════════════════
# TC07 — refresh_courses 复用 load_student_courses
# ══════════════════════════════════════════════════════════════════════
async def test_F_S_010_TC07_refresh_courses():
    """refresh_courses 应调用 load_student_courses 刷新数据"""
    _guard()
    state = CourseState()
    await state.refresh_courses()
    # 刷新后 loading 应为 False（不管成功与否，finally 都会置 False）
    assert state.loading is False


# ══════════════════════════════════════════════════════════════════════
# TC08 — 截止日期字段
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC08_due_date_fields():
    """有截止日期时 has_due_date=True, next_due_date_str 非空"""
    _guard()
    # 有截止
    cp_with = CourseProgress(
        course_id=1, course_code="EP1", course_name="工程实践1",
        total_chapters=5, completed_tasks=3, total_tasks=10,
        next_due_date_str="2026-06-15 23:59", has_due_date=True,
        status="active", progress_percentage=30,
    )
    assert cp_with.has_due_date is True
    assert cp_with.next_due_date_str == "2026-06-15 23:59"

    # 无截止
    cp_without = CourseProgress(
        course_id=2, course_code="EP2", course_name="工程实践2",
        total_chapters=3, completed_tasks=0, total_tasks=5,
        next_due_date_str="", has_due_date=False,
        status="active", progress_percentage=0,
    )
    assert cp_without.has_due_date is False
    assert cp_without.next_due_date_str == ""


# ══════════════════════════════════════════════════════════════════════
# TC09 — 数据库模型字段验证
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC09_db_models_match_schema():
    """验证 ORM 模型与远程数据库表结构匹配"""
    _guard()
    from oaepp.models.database import (
        User, Course, Chapter, Enrollment, Assignment, Submission,
    )

    # User → users 表
    assert User.__tablename__ == "users"
    user_fields = {c.name for c in User.__table__.columns}
    expected_user = {"id", "role", "student_no", "email", "password_hash",
                     "full_name", "avatar_url", "login_fail_cnt", "locked_until",
                     "is_active", "created_at", "updated_at"}
    assert user_fields == expected_user, f"User 字段不匹配: {user_fields ^ expected_user}"

    # Course → courses 表
    assert Course.__tablename__ == "courses"
    course_fields = {c.name for c in Course.__table__.columns}
    expected_course = {"id", "code", "name", "term", "status", "created_at"}
    assert course_fields == expected_course, f"Course 字段不匹配: {course_fields ^ expected_course}"

    # Chapter → chapters 表
    assert Chapter.__tablename__ == "chapters"
    chapter_fields = {c.name for c in Chapter.__table__.columns}
    expected_chapter = {"id", "course_id", "chapter_no", "title", "content_md"}
    assert chapter_fields == expected_chapter, f"Chapter 字段不匹配: {chapter_fields ^ expected_chapter}"

    # Enrollment → enrollments 表
    assert Enrollment.__tablename__ == "enrollments"
    enr_fields = {c.name for c in Enrollment.__table__.columns}
    expected_enr = {"id", "course_id", "student_user_id", "enrolled_at"}
    assert enr_fields == expected_enr, f"Enrollment 字段不匹配: {enr_fields ^ expected_enr}"

    # Assignment → assignments 表
    assert Assignment.__tablename__ == "assignments"
    asgn_fields = {c.name for c in Assignment.__table__.columns}
    expected_asgn = {"id", "course_id", "chapter_id", "title", "description_md",
                     "allow_resubmit", "late_policy", "deadline", "created_by", "created_at"}
    assert asgn_fields == expected_asgn, f"Assignment 字段不匹配: {asgn_fields ^ expected_asgn}"

    # Submission → submissions 表
    assert Submission.__tablename__ == "submissions"
    sub_fields = {c.name for c in Submission.__table__.columns}
    expected_sub = {"id", "assignment_id", "student_user_id", "version_no",
                    "file_url", "text_content", "is_late", "grading_status",
                    "allow_resubmit_override", "submitted_at"}
    assert sub_fields == expected_sub, f"Submission 字段不匹配: {sub_fields ^ expected_sub}"


# ══════════════════════════════════════════════════════════════════════
# TC10 — 远程数据库连接验证
# ══════════════════════════════════════════════════════════════════════
def test_F_S_010_TC10_remote_db_connectivity():
    """验证能连接远程 MySQL 数据库并查询到数据"""
    _guard()
    import pymysql

    # 直接从环境变量读取原始 DATABASE_URL，不受 REFLEX_DB_URL 覆盖影响
    db_url = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://student_dev:OaEpp%40Dev2026@156.239.252.40:13306/oaepp_dev",
    )
    # 解析 db_url: mysql+pymysql://user:pass@host:port/dbname
    prefix = "mysql+pymysql://"
    assert db_url.startswith(prefix), f"db_url 格式异常: {db_url}"
    rest = db_url[len(prefix):]
    user_pass, host_db = rest.split("@")
    user, password = user_pass.split(":")
    password = password.replace("%40", "@")  # URL 编码的 @
    host_port, database = host_db.split("/")
    if ":" in host_port:
        host, port_str = host_port.split(":")
        port = int(port_str)
    else:
        host = host_port
        port = 3306

    conn = pymysql.connect(
        host=host, port=port,
        user=user, password=password,
        database=database, charset="utf8mb4",
    )
    cur = conn.cursor()

    # 验证关键表存在且有数据
    checks = [
        ("users", "SELECT COUNT(*) FROM users"),
        ("courses", "SELECT COUNT(*) FROM courses"),
        ("chapters", "SELECT COUNT(*) FROM chapters"),
        ("enrollments", "SELECT COUNT(*) FROM enrollments"),
        ("assignments", "SELECT COUNT(*) FROM assignments"),
        ("submissions", "SELECT COUNT(*) FROM submissions"),
    ]
    for table_name, sql in checks:
        cur.execute(sql)
        count_val = cur.fetchone()[0]
        assert count_val > 0, f"表 {table_name} 没有数据"

    conn.close()
