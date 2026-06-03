import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.database import db
from app.models.report_models import (
    ReportData, StudentInfo, BranchRecord, CommitRecord, CodeQualityStats,
    PRRecord, PRAnalysis, TeacherComment, ExamScoreRecord, AttendanceRecord,
    AttendanceSummary, CourseSummary, GitHubInfo, CourseSettings, AuditLogEntry, AuditLogResponse
)
from app.services.github_service import GitHubService


class ReportService:

    @staticmethod
    def get_student_info(student_id: str) -> Optional[StudentInfo]:
        with db() as conn:
            row = conn.execute(
                "SELECT name, student_id, class_name, pinyin, pinyin_abbr FROM students WHERE student_id=?",
                (student_id,)
            ).fetchone()
            if row:
                return StudentInfo(
                    name=row["name"],
                    student_id=row["student_id"],
                    class_name=row["class_name"],
                    pinyin=row["pinyin"] or "",
                    pinyin_abbr=row["pinyin_abbr"] or ""
                )
        return None

    @staticmethod
    def get_course_settings() -> CourseSettings:
        with db() as conn:
            rows = conn.execute("SELECT key, value FROM course_settings").fetchall()
            settings = {row["key"]: row["value"] for row in rows}
            return CourseSettings(
                course_name=settings.get("course_name", "研究生课程《机器人系统》"),
                semester=settings.get("semester", "2024-2025学年第一学期"),
                github_token=settings.get("github_token", "")
            )

    @staticmethod
    def update_course_settings(settings: CourseSettings) -> bool:
        with db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO course_settings (key, value, updated_at) VALUES (?, ?, datetime('now','localtime'))",
                ("course_name", settings.course_name)
            )
            conn.execute(
                "INSERT OR REPLACE INTO course_settings (key, value, updated_at) VALUES (?, ?, datetime('now','localtime'))",
                ("semester", settings.semester)
            )
            if settings.github_token:
                conn.execute(
                    "INSERT OR REPLACE INTO course_settings (key, value, updated_at) VALUES (?, ?, datetime('now','localtime'))",
                    ("github_token", settings.github_token)
                )
        return True

    @staticmethod
    def get_github_info(student_id: str) -> Optional[GitHubInfo]:
        with db() as conn:
            row = conn.execute(
                "SELECT id, student_id, github_username, repo_name, github_token FROM student_github_info WHERE student_id=?",
                (student_id,)
            ).fetchone()
            if row:
                return GitHubInfo(
                    id=row["id"],
                    student_id=row["student_id"],
                    github_username=row["github_username"] or "",
                    repo_name=row["repo_name"] or "",
                    github_token=row["github_token"] or ""
                )
        return None

    @staticmethod
    def save_github_info(info: GitHubInfo) -> bool:
        with db() as conn:
            existing = conn.execute(
                "SELECT id FROM student_github_info WHERE student_id=?",
                (info.student_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE student_github_info SET github_username=?, repo_name=?, github_token=?, updated_at=datetime('now','localtime')
                       WHERE student_id=?""",
                    (info.github_username, info.repo_name, info.github_token, info.student_id)
                )
            else:
                conn.execute(
                    """INSERT INTO student_github_info (student_id, github_username, repo_name, github_token)
                       VALUES (?, ?, ?, ?)""",
                    (info.student_id, info.github_username, info.repo_name, info.github_token)
                )
        return True

    @staticmethod
    def get_teacher_comments(student_id: str) -> List[TeacherComment]:
        with db() as conn:
            rows = conn.execute(
                "SELECT id, student_id, comment, teacher, created_at, updated_at FROM teacher_comments WHERE student_id=? ORDER BY created_at DESC",
                (student_id,)
            ).fetchall()
            return [
                TeacherComment(
                    id=row["id"],
                    student_id=row["student_id"],
                    comment=row["comment"],
                    teacher=row["teacher"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]

    @staticmethod
    def save_teacher_comment(student_id: str, comment: str) -> bool:
        with db() as conn:
            existing = conn.execute(
                "SELECT id FROM teacher_comments WHERE student_id=?",
                (student_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE teacher_comments SET comment=?, updated_at=datetime('now','localtime')
                       WHERE student_id=?""",
                    (comment, student_id)
                )
            else:
                conn.execute(
                    """INSERT INTO teacher_comments (student_id, comment) VALUES (?, ?)""",
                    (student_id, comment)
                )
        return True

    @staticmethod
    def delete_teacher_comment(student_id: str) -> bool:
        with db() as conn:
            conn.execute("DELETE FROM teacher_comments WHERE student_id=?", (student_id,))
        return True

    @staticmethod
    def get_attendance_records(student_id: str) -> List[AttendanceRecord]:
        with db() as conn:
            rows = conn.execute(
                "SELECT id, student_id, date, status, note FROM attendance WHERE student_id=? ORDER BY date DESC",
                (student_id,)
            ).fetchall()
            return [
                AttendanceRecord(
                    id=row["id"],
                    student_id=row["student_id"],
                    date=row["date"],
                    status=row["status"],
                    note=row["note"] or ""
                )
                for row in rows
            ]

    @staticmethod
    def get_attendance_summary(student_id: str) -> AttendanceSummary:
        records = ReportService.get_attendance_records(student_id)
        summary = AttendanceSummary()
        if not records:
            return summary

        summary.total_days = len(records)
        for record in records:
            if record.status == "present":
                summary.present_days += 1
            elif record.status == "absent":
                summary.absent_days += 1
            elif record.status == "late":
                summary.late_days += 1
            elif record.status == "leave":
                summary.leave_days += 1

        if summary.total_days > 0:
            summary.attendance_rate = round((summary.present_days + summary.late_days) / summary.total_days * 100, 1)
        return summary

    @staticmethod
    def save_attendance_records(student_id: str, records: List[AttendanceRecord]) -> bool:
        with db() as conn:
            for record in records:
                conn.execute(
                    """INSERT OR REPLACE INTO attendance (student_id, date, status, note) VALUES (?, ?, ?, ?)""",
                    (student_id, record.date, record.status, record.note or "")
                )
        return True

    @staticmethod
    def get_exam_scores(student_id: str) -> List[ExamScoreRecord]:
        with db() as conn:
            rows = conn.execute(
                """SELECT s.exam_id, e.title as exam_title, s.score, s.total, s.submitted_at
                   FROM scores s JOIN exams e ON s.exam_id = e.id
                   WHERE s.student_id=?
                   ORDER BY s.submitted_at DESC""",
                (student_id,)
            ).fetchall()
            return [
                ExamScoreRecord(
                    exam_id=row["exam_id"],
                    exam_title=row["exam_title"],
                    score=row["score"],
                    total=row["total"],
                    submitted_at=row["submitted_at"]
                )
                for row in rows
            ]

    @staticmethod
    def get_course_summary(student_id: str) -> CourseSummary:
        exam_scores = ReportService.get_exam_scores(student_id)
        attendance_summary = ReportService.get_attendance_summary(student_id)

        summary = CourseSummary()
        summary.exam_scores = exam_scores
        summary.attendance_summary = attendance_summary
        summary.total_exams = len(exam_scores)
        summary.completed_exams = len([e for e in exam_scores if e.score is not None])

        if exam_scores:
            total = sum(e.score for e in exam_scores)
            summary.total_score = round(total, 1)
            summary.avg_score = round(total / len(exam_scores), 1)

        return summary

    @staticmethod
    async def get_full_report(student_id: str, refresh: bool = False) -> Optional[ReportData]:
        student_info = ReportService.get_student_info(student_id)
        if not student_info:
            return None

        course_settings = ReportService.get_course_settings()
        github_info = ReportService.get_github_info(student_id)

        branches = []
        commits = []
        code_quality = CodeQualityStats()
        pull_requests = []
        pr_analysis = PRAnalysis()
        has_github_data = False
        github_error = None

        if github_info and github_info.github_username and github_info.repo_name:
            token = github_info.github_token or course_settings.github_token
            github_service = GitHubService(token=token)
            try:
                github_data = await github_service.get_full_data(
                    github_info.github_username,
                    github_info.repo_name
                )
                has_github_data = True

                branches = [
                    BranchRecord(
                        name=b.get("name", ""),
                        protected=b.get("protected", False),
                        last_commit_sha=b.get("last_commit_sha", ""),
                        last_commit_date=b.get("last_commit_date", "")
                    )
                    for b in github_data.get("branches", [])
                ]

                commits = [
                    CommitRecord(
                        sha=c.get("sha", ""),
                        message=c.get("message", ""),
                        author_name=c.get("author_name", ""),
                        author_email=c.get("author_email", ""),
                        date=c.get("date", ""),
                        additions=c.get("additions", 0),
                        deletions=c.get("deletions", 0)
                    )
                    for c in github_data.get("commits", [])
                ]

                languages = github_data.get("languages", {})
                total_bytes = sum(languages.values()) if languages else 1
                top_languages = [
                    {"name": lang, "bytes": size, "percentage": round(size / total_bytes * 100, 1)}
                    for lang, size in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                ]

                code_quality = CodeQualityStats(
                    total_lines=github_data.get("total_lines", 0),
                    file_count=0,
                    languages=languages,
                    top_languages=top_languages
                )

                pull_requests = [
                    PRRecord(
                        number=pr.get("number", 0),
                        title=pr.get("title", ""),
                        state=pr.get("state", ""),
                        user_login=pr.get("user_login", ""),
                        created_at=pr.get("created_at", ""),
                        updated_at=pr.get("updated_at"),
                        merged_at=pr.get("merged_at"),
                        additions=pr.get("additions", 0),
                        deletions=pr.get("deletions", 0),
                        review_comments=pr.get("review_comments", 0),
                        url=pr.get("url", "")
                    )
                    for pr in github_data.get("pull_requests", [])
                ]

                pr_stats = github_data.get("pr_analysis", {})
                pr_analysis = PRAnalysis(
                    total_prs=pr_stats.get("total_prs", 0),
                    merged_prs=pr_stats.get("merged_prs", 0),
                    open_prs=pr_stats.get("open_prs", 0),
                    closed_prs=pr_stats.get("closed_prs", 0),
                    merge_rate=pr_stats.get("merge_rate", 0.0),
                    avg_review_time_hours=0.0,
                    avg_pr_size=pr_stats.get("avg_pr_size", 0.0),
                    total_additions=pr_stats.get("total_additions", 0),
                    total_deletions=pr_stats.get("total_deletions", 0)
                )

            except Exception as e:
                github_error = str(e)

        teacher_comments = ReportService.get_teacher_comments(student_id)
        exam_scores = ReportService.get_exam_scores(student_id)
        attendance_records = ReportService.get_attendance_records(student_id)
        attendance_summary = ReportService.get_attendance_summary(student_id)
        course_summary = ReportService.get_course_summary(student_id)

        return ReportData(
            student_info=student_info,
            course_name=course_settings.course_name,
            semester=course_settings.semester,
            branches=branches,
            commits=commits,
            code_quality=code_quality,
            pull_requests=pull_requests,
            pr_analysis=pr_analysis,
            teacher_comments=teacher_comments,
            exam_scores=exam_scores,
            attendance_records=attendance_records,
            attendance_summary=attendance_summary,
            course_summary=course_summary,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            has_github_data=has_github_data,
            github_error=github_error
        )

    @staticmethod
    def log_audit(
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        format: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: str = ""
    ) -> bool:
        with db() as conn:
            conn.execute(
                """INSERT INTO audit_logs (action, operator, target_type, target_id, format, ip_address, user_agent, details)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (action, "teacher", target_type, target_id, format, ip_address, user_agent, details)
            )
        return True

    @staticmethod
    def get_audit_logs(
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AuditLogResponse:
        conditions = []
        params = []

        if student_id:
            conditions.append("target_id = ?")
            params.append(student_id)

        if action:
            conditions.append("action = ?")
            params.append(action)

        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with db() as conn:
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM audit_logs WHERE {where_clause}",
                params
            ).fetchone()
            total = count_row["cnt"]

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"""SELECT id, action, operator, target_type, target_id, format, ip_address, user_agent, details, created_at
                    FROM audit_logs WHERE {where_clause}
                    ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                params + [page_size, offset]
            ).fetchall()

            logs = [
                AuditLogEntry(
                    id=row["id"],
                    action=row["action"],
                    operator=row["operator"],
                    target_type=row["target_type"],
                    target_id=row["target_id"],
                    format=row["format"],
                    ip_address=row["ip_address"],
                    user_agent=row["user_agent"],
                    details=row["details"] or "",
                    created_at=row["created_at"]
                )
                for row in rows
            ]

        return AuditLogResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=logs
        )

    @staticmethod
    def get_classes() -> List[str]:
        with db() as conn:
            rows = conn.execute(
                "SELECT DISTINCT class_name FROM students WHERE class_name != '' ORDER BY class_name"
            ).fetchall()
            return [row["class_name"] for row in rows]

    @staticmethod
    def get_students_by_class(class_name: str) -> List[StudentInfo]:
        with db() as conn:
            rows = conn.execute(
                "SELECT name, student_id, class_name, pinyin, pinyin_abbr FROM students WHERE class_name=? ORDER BY name",
                (class_name,)
            ).fetchall()
            return [
                StudentInfo(
                    name=row["name"],
                    student_id=row["student_id"],
                    class_name=row["class_name"],
                    pinyin=row["pinyin"] or "",
                    pinyin_abbr=row["pinyin_abbr"] or ""
                )
                for row in rows
            ]
