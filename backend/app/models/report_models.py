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
