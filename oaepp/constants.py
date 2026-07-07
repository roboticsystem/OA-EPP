"""
OA-EPP 全局常量

所有常量统一在此定义，学生功能只能导入使用，禁止重新定义同名变量。

需求编号：F-S-001 ~ F-S-053（全局共享）
"""

# ── 分页配置 ──
PAGE_SIZE = 10
"""默认分页大小"""

# ── 文件上传限制 ──
UPLOAD_LIMIT_MB = 10
"""文件上传大小限制（MB）"""

# ── 用户角色 ──
USER_ROLES = ["student", "teacher", "admin"]
"""用户角色枚举"""

# ── 出勤状态 ──
ATTENDANCE_STATUS = ["present", "late", "absent"]
"""出勤状态：出勤 / 迟到 / 缺勤"""

# ── 考试类型 ──
EXAM_TYPES = ["quiz", "midterm", "final", "practice"]
"""考试类型：随堂测验 / 期中 / 期末 / 练习"""

# ── 题目类型 ──
QUESTION_TYPES = ["single", "multi", "blank", "short"]
"""题目类型：单选 / 多选 / 填空 / 简答"""

# ── 提交格式 ──
SUBMISSION_FORMATS = ["pdf", "docx", "zip", "py", "c", "cpp"]
"""支持的作业提交文件格式"""

# ── 通知分类 ──
NOTIFICATION_CATEGORIES = ["announcement", "deadline", "grade", "system"]
"""通知分类：公告 / 截止提醒 / 成绩 / 系统"""

# ── 得分类型 ──
SCORE_TYPES = ["attendance", "exam", "code", "pr"]
"""得分类型：出勤 / 考试 / 代码 / PR 贡献"""

# ── 反馈来源 ──
FEEDBACK_SOURCES = ["assignment", "exam", "pr", "manual"]
"""反馈来源：作业 / 考试 / PR / 手动"""

# ── PR 状态 ──
PR_STATES = ["open", "merged", "closed"]
"""PR 状态：开放 / 已合并 / 已关闭"""

# ── GitHub 绑定状态 ──
GITHUB_BIND_STATUS = ["pending", "approved", "rejected"]
"""GitHub 账号绑定状态：待审核 / 已通过 / 已拒绝"""

# ── 课程状态 ──
COURSE_STATUS = ["draft", "open", "closed"]
"""课程状态：草稿 / 开放 / 已关闭"""
