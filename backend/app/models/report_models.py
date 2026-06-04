from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StudentInfo(BaseModel):
    name: str
    student_id: str
    class_name: str
    pinyin: str = ""
    pinyin_abbr: str = ""


class BranchRecord(BaseModel):
    name: str
    protected: bool = False
    created_at: Optional[str] = None
    last_commit_sha: Optional[str] = None
    last_commit_date: Optional[str] = None
    commit_count: int = 0


class CommitRecord(BaseModel):
    sha: str
    message: str
    author_name: str
    author_email: str
    date: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0


class CodeQualityStats(BaseModel):
    total_lines: int = 0
    file_count: int = 0
    languages: dict = {}
    top_languages: List[dict] = []


class PRRecord(BaseModel):
    number: int
    title: str
    state: str
    user_login: str
    created_at: str
    updated_at: Optional[str] = None
    merged_at: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    review_comments: int = 0
    url: str = ""


class PRAnalysis(BaseModel):
    total_prs: int = 0
    merged_prs: int = 0
    open_prs: int = 0
    closed_prs: int = 0
    merge_rate: float = 0.0
    avg_review_time_hours: float = 0.0
    avg_pr_size: float = 0.0
    total_additions: int = 0
    total_deletions: int = 0


class TeacherComment(BaseModel):
    id: Optional[int] = None
    student_id: str
    comment: str
    teacher: str = "teacher"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ExamScoreRecord(BaseModel):
    exam_id: str
    exam_title: str
    score: float
    total: float
    submitted_at: Optional[str] = None


class AttendanceRecord(BaseModel):
    id: Optional[int] = None
    student_id: str
    date: str
    status: str
    note: str = ""


class AttendanceSummary(BaseModel):
    total_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    leave_days: int = 0
    attendance_rate: float = 0.0


class CourseSummary(BaseModel):
    total_exams: int = 0
    completed_exams: int = 0
    total_score: float = 0.0
    avg_score: float = 0.0
    exam_scores: List[ExamScoreRecord] = []
    attendance_summary: AttendanceSummary = AttendanceSummary()


class ReportData(BaseModel):
    student_info: StudentInfo
    course_name: str
    semester: str
    branches: List[BranchRecord] = []
    commits: List[CommitRecord] = []
    code_quality: CodeQualityStats = CodeQualityStats()
    pull_requests: List[PRRecord] = []
    pr_analysis: PRAnalysis = PRAnalysis()
    teacher_comments: List[TeacherComment] = []
    exam_scores: List[ExamScoreRecord] = []
    attendance_records: List[AttendanceRecord] = []
    attendance_summary: AttendanceSummary = AttendanceSummary()
    course_summary: CourseSummary = CourseSummary()
    generated_at: str
    has_github_data: bool = False
    github_error: Optional[str] = None


class GitHubInfo(BaseModel):
    id: Optional[int] = None
    student_id: str
    github_username: str = ""
    repo_name: str = ""
    github_token: str = ""


class CourseSettings(BaseModel):
    course_name: str
    semester: str
    github_token: str = ""


class AuditLogEntry(BaseModel):
    id: int
    action: str
    operator: str
    target_type: str
    target_id: Optional[str] = None
    format: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: str = ""
    created_at: str


class AuditLogQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    student_id: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AuditLogResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: List[AuditLogEntry] = []


class BatchExportRequest(BaseModel):
    class_name: Optional[str] = None
    student_ids: Optional[List[str]] = None
    format: str = "pdf"


class ExportFormat(str):
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"


# ---------------------------------------------------------------------------
# F-T-003-AI: AI 自动审查相关模型
# ---------------------------------------------------------------------------

class CommitAnalysisResult(BaseModel):
    """提交行为分析结果"""
    total_commits: int = 0
    avg_per_week: float = 0.0
    max_per_day: int = 0
    message_quality_score: float = 0.0
    message_quality: dict = {}
    consistency_score: float = 0.0
    coding_days: int = 0
    active_period_days: int = 0
    weekend_commit_pct: float = 0.0
    late_night_commit_pct: float = 0.0
    avg_message_length: float = 0.0
    suggestions: List[str] = []


class BranchAnalysisResult(BaseModel):
    """分支策略分析结果"""
    total_branches: int = 0
    protected_branches: int = 0
    naming_score: float = 0.0
    strategy_score: float = 0.0
    strategy_type: str = ""
    strategy_desc: str = ""
    has_default_branch: bool = False
    naming_issues: List[str] = []
    suggestions: List[str] = []


class PRAnalysisResult(BaseModel):
    """PR 质量分析结果"""
    total_prs: int = 0
    open_prs: int = 0
    merged_prs: int = 0
    closed_prs: int = 0
    merge_rate: float = 0.0
    avg_description_length: float = 0.0
    description_quality_score: float = 0.0
    review_engagement_score: float = 0.0
    avg_review_comments: float = 0.0
    avg_pr_size: float = 0.0
    total_additions: int = 0
    total_deletions: int = 0
    overall_pr_score: float = 0.0
    suggestions: List[str] = []


class ActivityAnalysisResult(BaseModel):
    """代码活跃度分析结果"""
    activity_score: float = 0.0
    activity_level: str = "inactive"
    total_actions: int = 0
    active_hours_distribution: dict = {}
    peak_day_of_week: str = ""
    project_duration_days: int = 0
    suggestions: List[str] = []


class CodeScaleResult(BaseModel):
    """代码规模评估结果"""
    total_lines: int = 0
    language_count: int = 0
    languages: dict = {}
    scale_level: str = ""
    scale_score: float = 0.0


class AIDimensions(BaseModel):
    """AI 审查各维度分析结果"""
    commit_patterns: CommitAnalysisResult = CommitAnalysisResult()
    branch_strategy: BranchAnalysisResult = BranchAnalysisResult()
    pr_quality: PRAnalysisResult = PRAnalysisResult()
    code_activity: ActivityAnalysisResult = ActivityAnalysisResult()
    code_scale: CodeScaleResult = CodeScaleResult()


class AIReviewResult(BaseModel):
    """AI 自动审查完整结果"""
    student_name: str = ""
    student_id: str = ""
    overall_score: float = 0.0
    grade: str = ""
    grade_desc: str = ""
    dimensions: AIDimensions = AIDimensions()
    scores: dict = {}
    weights: dict = {}
    summary: str = ""
    highlights: List[str] = []
    risks: List[str] = []
    suggestions: List[str] = []
    reviewed_at: str = ""


class AIReviewRequest(BaseModel):
    """发起 AI 审查的请求参数"""
    student_id: str
    refresh: bool = False
    course_id: Optional[int] = None
