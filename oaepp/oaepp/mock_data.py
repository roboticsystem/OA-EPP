"""Mock data for OA-EPP prototype pages.

All data is hardcoded — no database dependency.
Maps 1:1 to the prototype/ HTML specs in the design document.
"""


class MockData:
    """Static mock dataset that mirrors the prototype/ design spec."""

    # ── Student Info ──────────────────────────────────────────────
    STUDENT = {
        "name": "张三",
        "student_id": "2021001001",
        "class_name": "2021级软工1班",
        "avatar_char": "张",
    }

    # ── Score Cards (Dashboard) ───────────────────────────────────
    SCORE_CARDS = [
        {"label": "综合总分", "value": 87.5, "total": 100, "color": "blue", "sub": None},
        {"label": "出勤得分", "value": 18, "total": 20, "color": "green", "sub": "出勤率 90%"},
        {"label": "考试得分", "value": 24, "total": 30, "color": "purple", "sub": None},
        {"label": "代码 + PR", "value": 45.5, "total": 50, "color": "orange", "sub": None},
    ]

    # ── Pending Tasks (Dashboard) ─────────────────────────────────
    PENDING_TASKS = [
        {
            "title": "第7章 软件需求规格说明书",
            "deadline": "2025-05-27 23:59",
            "remaining": "2 天",
            "urgency": "urgent",  # red
            "status": "待提交",
        },
        {
            "title": "第8章 系统设计文档",
            "deadline": "2025-06-03 23:59",
            "remaining": "9 天",
            "urgency": "warning",  # yellow
            "status": "待提交",
        },
        {
            "title": "第6章 数据库设计",
            "deadline": None,
            "remaining": None,
            "urgency": "done",  # green
            "status": "已提交 · 待批改",
        },
    ]

    # ── Announcements (Dashboard) ─────────────────────────────────
    ANNOUNCEMENTS = [
        {
            "title": "第7章截止时间延至5月27日",
            "date": "2025-05-23",
            "author": "教师：李四",
            "unread": True,
        },
        {
            "title": "期末汇报安排（6月15日）已发布",
            "date": "2025-05-21",
            "author": "教师：李四",
            "unread": True,
        },
        {
            "title": "第6章批改成绩已发布，请查看反馈",
            "date": "2025-05-18",
            "author": "系统通知",
            "unread": False,
        },
    ]

    # ── Exam Scores History ───────────────────────────────────────
    EXAM_HISTORY = [
        {"name": "期中1", "score": 22, "total": 30, "height_pct": 73},
        {"name": "期中2", "score": 28, "total": 30, "height_pct": 93},
        {"name": "期末", "score": 24, "total": 30, "height_pct": 80},
        {"name": "补考", "score": 18, "total": 30, "height_pct": 60},
    ]

    TOTAL_SCORE_TREND = [
        72, 75, 78, 80, 82, 85, 87.5,
    ]
    TREND_LABELS = ["EP1", "EP2", "EP3", "期中1", "期中2", "期末", "当前"]

    # ── Course Cards ──────────────────────────────────────────────
    COURSES = [
        {
            "id": "ep1",
            "name": "工程实践 1",
            "semester": "2023 秋",
            "chapters": 8,
            "tasks": 8,
            "completed": 8,
            "total_score": 92,
            "status": "completed",
            "status_label": "已完成",
        },
        {
            "id": "ep2",
            "name": "工程实践 2",
            "semester": "2024 春",
            "chapters": 10,
            "tasks": 10,
            "completed": 10,
            "total_score": 88,
            "status": "completed",
            "status_label": "已完成",
        },
        {
            "id": "ep3",
            "name": "工程实践 3",
            "semester": "2024 秋",
            "chapters": 12,
            "tasks": 12,
            "completed": 12,
            "total_score": 85,
            "status": "completed",
            "status_label": "已完成",
        },
        {
            "id": "ep4",
            "name": "工程实践 4",
            "semester": "2025 春",
            "chapters": 15,
            "tasks": 15,
            "completed": 7,
            "total_score": 87.5,
            "status": "active",
            "status_label": "进行中",
            "is_current": True,
        },
    ]

    # ── Chapter List (Courses detail) ─────────────────────────────
    CHAPTERS = [
        {"ch": "Ch.01", "title": "需求分析方法", "deadline": "2025-03-14",
         "status": "graded", "score": "9.5/10", "status_label": "已批改", "status_color": "green"},
        {"ch": "Ch.02", "title": "用例建模", "deadline": "2025-03-21",
         "status": "graded", "score": "8/10", "status_label": "已批改", "status_color": "green"},
        {"ch": "Ch.06", "title": "数据库设计", "deadline": "2025-05-09",
         "status": "pending", "score": None, "status_label": "待批改", "status_color": "yellow"},
        {"ch": "Ch.07", "title": "软件需求规格说明书", "deadline": "2025-05-27 ⚠️",
         "status": "todo", "score": None, "status_label": "待提交", "status_color": "red"},
        {"ch": "Ch.08", "title": "系统设计文档", "deadline": "2025-06-03",
         "status": "upcoming", "score": None, "status_label": "未开始", "status_color": "gray"},
    ]

    # ── Assignments ───────────────────────────────────────────────
    ASSIGNMENTS = [
        {
            "title": "第7章 软件需求规格说明书",
            "status": "todo",
            "status_label": "待提交",
            "status_color": "red",
            "deadline": "2025-05-27 23:59",
            "remaining": "2 天",
            "notes": "支持：pdf、docx、zip · 最大 50MB",
            "icon_type": "warning",
        },
        {
            "title": "第6章 数据库设计",
            "status": "pending",
            "status_label": "待批改",
            "status_color": "yellow",
            "submitted_at": "2025-05-09 21:32",
            "version": "v1",
            "file_size": "1.2MB",
            "file_name": "2021001001_db_design.pdf",
            "icon_type": "clock",
        },
        {
            "title": "第5章 系统架构设计",
            "status": "graded",
            "status_label": "已批改",
            "status_color": "green",
            "score": "9/10",
            "graded_at": "2025-05-02",
            "version": "v2",
            "notes": "有改进建议",
            "icon_type": "check",
        },
        {
            "title": "第4章 用例分析",
            "status": "late",
            "status_label": "迟交",
            "status_color": "orange",
            "submitted_at": "2025-04-21 01:12",
            "deadline_original": "04-18 23:59",
            "notes": "迟交扣分适用，得分以批改结果为准",
            "icon_type": "warning",
        },
    ]

    # ── Active Assignment (for submit panel) ───────────────────────
    ACTIVE_ASSIGNMENT = {
        "title": "第7章 软件需求规格说明书",
        "deadline": "2025-05-27",
        "current_version": "v1（首次提交）",
        "allow_resubmit": True,
        "file_types": "pdf · docx · zip",
        "max_size": "50MB",
    }

    VERSION_HISTORY = [
        {"version": "v1", "file_name": "2021001001_db_design.pdf", "date": "05-09 21:32"},
    ]

    # ── Grade Overview Cards ───────────────────────────────────────
    GRADE_CARDS = [
        {"label": "出勤得分", "value": 18, "total": 20, "color": "green",
         "detail": "出勤 18/20 次 · 缺勤 2 次", "updated": True},
        {"label": "考试得分", "value": 24, "total": 30, "color": "purple",
         "detail": "3 次考试均已出分", "updated": True},
        {"label": "代码提交", "value": 32, "total": 40, "color": "orange",
         "detail": "5 已批 · 2 待批", "updated": False,
         "badge_text": "部分待批", "badge_color": "yellow"},
        {"label": "PR 贡献", "value": 13.5, "total": 10, "color": "blue",
         "detail": "超额加分 · 9 次 PR 审查", "updated": True},
    ]

    # ── Grade Detail Rows ──────────────────────────────────────────
    GRADE_DETAILS = [
        {
            "task": "第5章 系统架构设计",
            "score": "9 / 10",
            "score_color": "green",
            "reviewer": "李四（教师）",
            "review_time": "2025-05-02",
            "status_label": "已批改",
            "status_color": "green",
            "comment_expanded": True,
        },
        {
            "task": "第4章 用例分析",
            "score": "7 / 10",
            "score_color": "orange",
            "reviewer": "李四（教师）",
            "review_time": "2025-04-25",
            "status_label": "迟交扣分",
            "status_color": "orange",
            "comment_expanded": False,
        },
        {
            "task": "第6章 数据库设计",
            "score": "—",
            "score_color": "gray",
            "reviewer": "—",
            "review_time": "—",
            "status_label": "待批改",
            "status_color": "yellow",
            "comment_expanded": False,
        },
    ]

    # ── Expanded Comment ───────────────────────────────────────────
    EXPANDED_COMMENT = {
        "chapter": "第5章",
        "reviewer": "李四（教师）",
        "date": "2025-05-02",
        "score": "9/10",
        "score_color": "green",
        "text": (
            "整体架构清晰，分层合理，对 Reflex 全栈模式理解到位。"
            "建议补充服务层（Service Layer）职责划分说明，避免 State 类过重。"
            "组件命名规范性有待提升，参考团队命名规范统一风格。"
        ),
        "tags": [
            {"text": "扣分：-1 · 命名规范", "color": "red"},
            {"text": "建议：补充服务层说明", "color": "blue"},
        ],
        "allow_resubmit": True,
    }

    # ── Attendance ─────────────────────────────────────────────────
    CURRENT_CHECKIN = {
        "course": "工程实践4 · 第11周课堂",
        "teacher": "李老师",
        "location": "教学楼 B306",
        "date": "2025-05-25 08:00",
        "remaining_seconds": 42,
        "progress_pct": 70,
        "window_seconds": 60,
        "geo_enabled": True,
        "geo_hint": "系统将核验您当前位置是否在 B306 教室范围内（半径 50 米）。若定位失败，请允许浏览器访问位置权限。",
    }

    ATTENDANCE_STATS = {
        "total": 18,
        "present": 15,
        "late": 1,
        "absent": 2,
        "rate_pct": 83.3,
        "estimated_score": 12.5,
        "max_score": 15,
    }

    ATTENDANCE_RECORDS = [
        {"week": "第11周", "date": "2025-05-25", "course": "工程实践4",
         "time": "—", "status": "checking", "status_label": "签到中", "status_color": "blue"},
        {"week": "第10周", "date": "2025-05-18", "course": "工程实践4",
         "time": "08:02:15", "status": "present", "status_label": "出勤", "status_color": "green"},
        {"week": "第9周", "date": "2025-05-11", "course": "工程实践4",
         "time": "08:00:48", "status": "present", "status_label": "出勤", "status_color": "green"},
        {"week": "第8周", "date": "2025-05-04", "course": "工程实践4",
         "time": "08:05:33", "status": "late", "status_label": "迟到", "status_color": "yellow"},
        {"week": "第7周", "date": "2025-04-27", "course": "工程实践4",
         "time": "—", "status": "absent", "status_label": "缺勤", "status_color": "red"},
        {"week": "第6周", "date": "2025-04-20", "course": "工程实践4",
         "time": "08:01:20", "status": "present", "status_label": "出勤", "status_color": "green"},
        {"week": "第5周", "date": "2025-04-13", "course": "工程实践4",
         "time": "—", "status": "absent", "status_label": "缺勤", "status_color": "red"},
    ]

    ATTENDANCE_RULES = [
        {"text": "出勤：计为 1 次", "color": "green"},
        {"text": "迟到：计为 0.5 次", "color": "yellow"},
        {"text": "缺勤：计为 0 次，累计缺课超 1/3 取消考试资格", "color": "red"},
    ]

    # ── Exam ───────────────────────────────────────────────────────
    CURRENT_EXAM = {
        "name": "工程实践4 · 第11周随堂测验",
        "total_questions": 10,
        "total_score": 20,
        "time_limit_min": 20,
        "remaining_seconds": 863,
        "answered_count": 7,
        "current_question_index": 8,
    }

    EXAM_QUESTIONS = [
        {
            "id": 8,
            "type": "单选题",
            "score": 2,
            "text": "在 Reflex 框架中，下列哪种方式是触发 State 更新的正确方法？",
            "options": [
                {"key": "A", "text": "直接修改 State 类的实例变量"},
                {"key": "B", "text": "在事件处理函数中通过 yield 返回状态更新"},
                {"key": "C", "text": "定义事件处理函数（EventHandler），在其中 self.var = value 赋值", "selected": True},
                {"key": "D", "text": "通过 JavaScript 调用 Reflex 内置全局函数 setState()"},
            ],
        },
    ]

    EXAM_ANSWERED = {
        1: True, 2: True, 3: True, 4: True, 5: True,
        6: True, 7: True, 8: True, 9: False, 10: False,
    }

    EXAM_HISTORY_RECORDS = [
        {"name": "第10周随堂测验", "date": "2025-05-18", "total": 20, "score": 18,
         "score_color": "green", "status": "已批改", "status_color": "green"},
        {"name": "第8周随堂测验", "date": "2025-05-04", "total": 20, "score": 16,
         "score_color": "green", "status": "已批改", "status_color": "green"},
        {"name": "期中考试", "date": "2025-04-20", "total": 50, "score": 38,
         "score_color": "yellow", "status": "已批改", "status_color": "green"},
        {"name": "第5周随堂测验", "date": "2025-04-13", "total": 20, "score": None,
         "score_color": "gray", "status": "待批改", "status_color": "yellow"},
    ]

    # ── Profile ────────────────────────────────────────────────────
    PROFILE = {
        "name": "张三",
        "student_id": "2021001001",
        "class_name": "工程实践班A",
        "email": "zhangsan@example.edu.cn",
        "avatar_char": "张",
    }

    GITHUB_BINDING = {
        "username": "zhangsan-dev",
        "verified": True,
        "url": "https://github.com/zhangsan-dev",
    }

    # ── Sidebar Navigation ────────────────────────────────────────
    NAV_ITEMS = [
        {"name": "仪表盘", "icon": "home", "route": "/"},
        {"name": "课程列表", "icon": "book", "route": "/courses"},
        {"name": "作业提交", "icon": "clipboard", "route": "/assignments"},
        {"name": "成绩与反馈", "icon": "chart", "route": "/grades"},
        {"name": "课堂签到", "icon": "check", "route": "/attendance"},
        {"name": "在线考试", "icon": "edit", "route": "/exam"},
        {"name": "个人资料", "icon": "user", "route": "/profile"},
    ]
