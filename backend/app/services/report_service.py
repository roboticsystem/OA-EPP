"""
报告生成服务 (F-T-010) + AI 审查集成 (F-T-003-AI)

适配 MySQL 数据库实际 Schema：
- github_bindings (student_user_id, github_username, ...)
- users (id, student_no, full_name, role)
- students (user_id, class_name)
- teacher_comments / course_settings (需 DDL 迁移)
- attendance_records + attendance_sessions
- audit_logs (actor_user_id, action, target_type, target_id, detail_json, action_at)
- exam_attempts + exams
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.database import db
from app.models.report_models import (
    ReportData, StudentInfo, BranchRecord, CommitRecord, CodeQualityStats,
    PRRecord, PRAnalysis, TeacherComment, ExamScoreRecord, AttendanceRecord,
    AttendanceSummary, CourseSummary, GitHubInfo, CourseSettings,
    AuditLogEntry, AuditLogResponse
)
from app.services.github_service import GitHubService
from app.services.ai_review_service import analyze_name_match, run_full_ai_review


# 默认课程 ID（用户硬编码）
COURSE_ID = int(os.environ.get("COURSE_ID", "1"))
# 默认教师用户 ID（用于 teacher_comments / audit_logs）
DEFAULT_TEACHER_ID = int(os.environ.get("TEACHER_USER_ID", "1"))


class ReportService:
    """报告生成与 AI 审查服务，完全适配 MySQL Schema。"""

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    @staticmethod
    def _get_user_id(student_no: str):
        """通过学号字符串查找 users.id。"""
        with db() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE student_no = %s AND role = 'student'",
                (student_no,)
            ).fetchone()
            return row["id"] if row else None

    @staticmethod
    def _student_row_to_info(row: dict) -> StudentInfo:
        return StudentInfo(
            name=row.get("full_name", ""),
            student_id=row.get("student_no", ""),
            class_name=row.get("class_name", ""),
            pinyin="",
            pinyin_abbr="",
        )

    # ------------------------------------------------------------------
    # 学生信息
    # ------------------------------------------------------------------

    @staticmethod
    def get_student_info(student_id: str) -> Optional[StudentInfo]:
        with db() as conn:
            row = conn.execute(
                """SELECT u.full_name, u.student_no, s.class_name
                   FROM users u
                   LEFT JOIN students s ON s.user_id = u.id
                   WHERE u.student_no = %s AND u.role = 'student'""",
                (student_id,)
            ).fetchone()
            if row:
                return ReportService._student_row_to_info(row)
        return None

    # ------------------------------------------------------------------
    # 课程设置
    # ------------------------------------------------------------------

    @staticmethod
    def get_course_settings() -> CourseSettings:
        settings = {}
        try:
            with db() as conn:
                rows = conn.execute(
                    "SELECT setting_key, setting_value FROM course_settings"
                ).fetchall()
                settings = {r["setting_key"]: r["setting_value"] for r in rows}
        except Exception:
            pass  # 表可能还不存在

        return CourseSettings(
            course_name=settings.get("course_name", "研究生课程《机器人系统》"),
            semester=settings.get("semester", "2024-2025学年第一学期"),
            github_token=settings.get("github_token", os.environ.get("GITHUB_TOKEN", ""))
        )

    @staticmethod
    def update_course_settings(settings: CourseSettings) -> bool:
        try:
            with db() as conn:
                for key, val in [
                    ("course_name", settings.course_name),
                    ("semester", settings.semester),
                    ("github_token", settings.github_token),
                ]:
                    conn.execute(
                        """INSERT INTO course_settings (setting_key, setting_value)
                           VALUES (%s, %s)
                           ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)""",
                        (key, val)
                    )
            return True
        except Exception:
            return False  # 表可能还不存在

    # ------------------------------------------------------------------
    # GitHub 绑定
    # ------------------------------------------------------------------

    @staticmethod
    def get_github_info(student_id: str) -> Optional[GitHubInfo]:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return None
        with db() as conn:
            # 动态检测可用字段（DDL 可能未执行）
            try:
                row = conn.execute(
                    "SELECT id, student_user_id, github_username, github_name, "
                    "       repo_name, github_token "
                    "FROM github_bindings WHERE student_user_id = %s",
                    (user_id,)
                ).fetchone()
            except Exception:
                # repo_name / github_token 字段可能不存在
                row = conn.execute(
                    "SELECT id, student_user_id, github_username, github_name "
                    "FROM github_bindings WHERE student_user_id = %s",
                    (user_id,)
                ).fetchone()

            if row:
                return GitHubInfo(
                    id=row["id"],
                    student_id=student_id,
                    github_username=row.get("github_username") or "",
                    repo_name=row.get("repo_name") or "",
                    github_token=row.get("github_token") or "",
                )
        return None

    @staticmethod
    def save_github_info(info: GitHubInfo) -> bool:
        user_id = ReportService._get_user_id(info.student_id)
        if not user_id:
            return False

        with db() as conn:
            existing = conn.execute(
                "SELECT id FROM github_bindings WHERE student_user_id = %s",
                (user_id,)
            ).fetchone()

            try:
                if existing:
                    conn.execute(
                        """UPDATE github_bindings
                           SET github_username = %s,
                               github_name = %s,
                               repo_name = %s,
                               github_token = %s
                           WHERE student_user_id = %s""",
                        (info.github_username, info.github_username,
                         info.repo_name, info.github_token, user_id)
                    )
                else:
                    conn.execute(
                        """INSERT INTO github_bindings
                           (student_user_id, github_username, github_name, repo_name, github_token)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (user_id, info.github_username, info.github_username,
                         info.repo_name, info.github_token)
                    )
            except Exception:
                # repo_name / github_token 列可能不存在，仅更新基础字段
                if existing:
                    conn.execute(
                        """UPDATE github_bindings
                           SET github_username = %s, github_name = %s
                           WHERE student_user_id = %s""",
                        (info.github_username, info.github_username, user_id)
                    )
                else:
                    conn.execute(
                        """INSERT INTO github_bindings
                           (student_user_id, github_username, github_name)
                           VALUES (%s, %s, %s)""",
                        (user_id, info.github_username, info.github_username)
                    )
        return True

    # ------------------------------------------------------------------
    # 教师评语 (使用 teacher_comments 表; 若不存在则回退 feedbacks)
    # ------------------------------------------------------------------

    @staticmethod
    def get_teacher_comments(student_id: str) -> List[TeacherComment]:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return []

        results: List[TeacherComment] = []

        # 优先 teacher_comments 表
        try:
            with db() as conn:
                rows = conn.execute(
                    """SELECT id, student_user_id, comment, teacher_user_id, created_at, updated_at
                       FROM teacher_comments WHERE student_user_id = %s
                       ORDER BY created_at DESC""",
                    (user_id,)
                ).fetchall()
                for row in rows:
                    results.append(TeacherComment(
                        id=row["id"],
                        student_id=student_id,
                        comment=row["comment"],
                        teacher="teacher",
                        created_at=str(row.get("created_at") or ""),
                        updated_at=str(row.get("updated_at") or ""),
                    ))
                if results:
                    return results
        except Exception:
            pass

        # 回退：feedbacks 表
        try:
            with db() as conn:
                rows = conn.execute(
                    """SELECT id, student_user_id, content, teacher_user_id, created_at
                       FROM feedbacks WHERE student_user_id = %s AND source_type = 'manual'
                       ORDER BY created_at DESC""",
                    (user_id,)
                ).fetchall()
                for row in rows:
                    results.append(TeacherComment(
                        id=row["id"],
                        student_id=student_id,
                        comment=row["content"],
                        teacher="teacher",
                        created_at=str(row.get("created_at") or ""),
                    ))
        except Exception:
            pass

        return results

    @staticmethod
    def save_teacher_comment(student_id: str, comment: str) -> bool:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return False

        try:
            with db() as conn:
                existing = conn.execute(
                    "SELECT id FROM teacher_comments WHERE student_user_id = %s",
                    (user_id,)
                ).fetchone()
                if existing:
                    conn.execute(
                        """UPDATE teacher_comments SET comment = %s
                           WHERE student_user_id = %s""",
                        (comment, user_id)
                    )
                else:
                    conn.execute(
                        """INSERT INTO teacher_comments (student_user_id, comment, teacher_user_id)
                           VALUES (%s, %s, %s)""",
                        (user_id, comment, DEFAULT_TEACHER_ID)
                    )
        except Exception:
            # 回退到 feedbacks
            try:
                with db() as conn:
                    conn.execute(
                        """INSERT INTO feedbacks (student_user_id, teacher_user_id, source_type, content)
                           VALUES (%s, %s, 'manual', %s)""",
                        (user_id, DEFAULT_TEACHER_ID, comment)
                    )
            except Exception:
                return False
        return True

    @staticmethod
    def delete_teacher_comment(student_id: str) -> bool:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return False
        try:
            with db() as conn:
                conn.execute("DELETE FROM teacher_comments WHERE student_user_id = %s", (user_id,))
        except Exception:
            try:
                with db() as conn:
                    conn.execute(
                        "DELETE FROM feedbacks WHERE student_user_id = %s AND source_type = 'manual'",
                        (user_id,)
                    )
            except Exception:
                return False
        return True

    # ------------------------------------------------------------------
    # 考勤
    # ------------------------------------------------------------------

    @staticmethod
    def get_attendance_records(student_id: str) -> List[AttendanceRecord]:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return []

        with db() as conn:
            rows = conn.execute(
                """SELECT ar.id, ar.student_user_id, ar.status, ar.checkin_at,
                          sess.expires_at
                   FROM attendance_records ar
                   JOIN attendance_sessions sess ON sess.id = ar.session_id
                   WHERE ar.student_user_id = %s AND ar.course_id = %s
                   ORDER BY ar.checkin_at DESC""",
                (user_id, COURSE_ID)
            ).fetchall()

            return [
                AttendanceRecord(
                    id=row["id"],
                    student_id=student_id,
                    date=str(row.get("checkin_at") or row.get("expires_at") or ""),
                    status=row["status"],
                    note="",
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
        for r in records:
            s = r.status
            if s == "present":
                summary.present_days += 1
            elif s == "absent":
                summary.absent_days += 1
            elif s == "late":
                summary.late_days += 1

        if summary.total_days > 0:
            summary.attendance_rate = round(
                (summary.present_days + summary.late_days) / summary.total_days * 100, 1
            )
        return summary

    @staticmethod
    def save_attendance_records(student_id: str, records: List[AttendanceRecord]) -> bool:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return False

        # attendance_records 依 session_id，只读；写操作需通过 attendance_sessions
        # 这里只返回 True 表示接受，实际写入由考勤系统管理
        return True

    # ------------------------------------------------------------------
    # 考试成绩
    # ------------------------------------------------------------------

    @staticmethod
    def get_exam_scores(student_id: str) -> List[ExamScoreRecord]:
        user_id = ReportService._get_user_id(student_id)
        if not user_id:
            return []

        with db() as conn:
            rows = conn.execute(
                """SELECT ea.exam_id, e.title AS exam_title, ea.total_score AS score,
                          e.exam_type, ea.submitted_at
                   FROM exam_attempts ea
                   JOIN exams e ON e.id = ea.exam_id
                   WHERE ea.student_user_id = %s AND e.course_id = %s
                   ORDER BY ea.submitted_at DESC""",
                (user_id, COURSE_ID)
            ).fetchall()

            return [
                ExamScoreRecord(
                    exam_id=str(row["exam_id"]),
                    exam_title=row["exam_title"],
                    score=float(row["score"]) if row["score"] is not None else 0.0,
                    total=100.0,
                    submitted_at=str(row.get("submitted_at") or ""),
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
        summary.completed_exams = len([e for e in exam_scores if e.score > 0])

        if exam_scores:
            valid = [e for e in exam_scores if e.score > 0]
            if valid:
                total = sum(e.score for e in valid)
                summary.total_score = round(total, 1)
                summary.avg_score = round(total / len(valid), 1)

        return summary

    # ------------------------------------------------------------------
    # 完整报告
    # ------------------------------------------------------------------

    @staticmethod
    async def get_full_report(student_id: str, refresh: bool = False) -> Optional[ReportData]:
        student_info = ReportService.get_student_info(student_id)
        if not student_info:
            return None

        course_settings = ReportService.get_course_settings()
        github_info = ReportService.get_github_info(student_id)

        branches: list = []
        commits: list = []
        code_quality = CodeQualityStats()
        pull_requests: list = []
        pr_analysis = PRAnalysis()
        has_github_data = False
        github_error = None

        if github_info and github_info.github_username and github_info.repo_name:
            token = github_info.github_token or course_settings.github_token or os.environ.get("GITHUB_TOKEN", "")
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
                        last_commit_date=b.get("last_commit_date", ""),
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
                        deletions=c.get("deletions", 0),
                    )
                    for c in github_data.get("commits", [])
                ]

                languages = github_data.get("languages", {})
                total_bytes = sum(languages.values()) if languages else 1
                top_languages = [
                    {"name": lang, "bytes": size,
                     "percentage": round(size / total_bytes * 100, 1)}
                    for lang, size in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                ]

                code_quality = CodeQualityStats(
                    total_lines=github_data.get("total_lines", 0),
                    file_count=0,
                    languages=languages,
                    top_languages=top_languages,
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
                        url=pr.get("url", ""),
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
                    total_deletions=pr_stats.get("total_deletions", 0),
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
            github_error=github_error,
        )

    # ------------------------------------------------------------------
    # AI 审查
    # ------------------------------------------------------------------

    @staticmethod
    async def run_ai_review(student_id: str, refresh: bool = False) -> Optional[Dict[str, object]]:
        student_info = ReportService.get_student_info(student_id)
        if not student_info:
            return {"error": f"学生 {student_id} 不存在"}

        github_info = ReportService.get_github_info(student_id)
        if not github_info or not github_info.github_username or not github_info.repo_name:
            return {"error": "该学生未绑定 GitHub 仓库信息"}

        course_settings = ReportService.get_course_settings()
        token = github_info.github_token or course_settings.github_token or os.environ.get("GITHUB_TOKEN", "")
        github_service = GitHubService(token=token)

        if refresh:
            github_service.clear_cache()

        try:
            github_data = await github_service.get_full_data(
                github_info.github_username,
                github_info.repo_name
            )
        except Exception as e:
            return {"error": f"获取 GitHub 数据失败: {str(e)}"}

        if not github_data.get("commits") and not github_data.get("branches"):
            return {"error": "GitHub 仓库暂无数据"}

        return run_full_ai_review(
            github_data=github_data,
            student_name=student_info.name,
            student_id=student_id,
        )

    # ------------------------------------------------------------------
    # 审计日志
    # ------------------------------------------------------------------

    @staticmethod
    def log_audit(
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        format: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: str = "",
    ) -> bool:
        try:
            with db() as conn:
                detail = {
                    "format": format or "",
                    "ip": ip_address or "",
                    "ua": user_agent or "",
                    "details": details,
                }
                conn.execute(
                    """INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail_json)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        DEFAULT_TEACHER_ID,
                        action,
                        target_type,
                        int(target_id) if target_id and target_id.isdigit() else 0,
                        json.dumps(detail, ensure_ascii=False),
                    )
                )
            return True
        except Exception:
            return False

    @staticmethod
    def get_audit_logs(
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AuditLogResponse:
        conditions = ["1=1"]
        params: list = []

        if student_id:
            conditions.append("target_id = %s")
            params.append(int(student_id) if student_id.isdigit() else 0)

        if action:
            conditions.append("action = %s")
            params.append(action)

        if start_date:
            conditions.append("action_at >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("action_at <= %s")
            params.append(end_date + " 23:59:59")

        where = " AND ".join(conditions)

        with db() as conn:
            count_row = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM audit_logs WHERE {where}",
                params
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"""SELECT id, actor_user_id, action, target_type, target_id,
                           detail_json, action_at
                    FROM audit_logs
                    WHERE {where}
                    ORDER BY action_at DESC LIMIT %s OFFSET %s""",
                params + [page_size, offset]
            ).fetchall()

            logs = []
            for row in rows:
                detail = {}
                try:
                    detail = json.loads(row.get("detail_json") or "{}")
                except Exception:
                    pass

                logs.append(AuditLogEntry(
                    id=row["id"],
                    action=row["action"],
                    operator=str(row.get("actor_user_id", "")),
                    target_type=row["target_type"],
                    target_id=str(row.get("target_id", "")),
                    format=detail.get("format", ""),
                    ip_address=detail.get("ip", ""),
                    user_agent=detail.get("ua", ""),
                    details=detail.get("details", ""),
                    created_at=str(row.get("action_at") or ""),
                ))

        return AuditLogResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=logs,
        )

    # ------------------------------------------------------------------
    # 班级
    # ------------------------------------------------------------------

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
                """SELECT u.full_name, u.student_no, s.class_name
                   FROM students s
                   JOIN users u ON u.id = s.user_id
                   WHERE s.class_name = %s AND u.role = 'student'
                   ORDER BY u.full_name""",
                (class_name,)
            ).fetchall()
            return [ReportService._student_row_to_info(row) for row in rows]

    # ------------------------------------------------------------------
    # GitHub 实名验证
    # ------------------------------------------------------------------

    @staticmethod
    async def verify_github_real_name(student_id: str) -> Dict[str, object]:
        student_info = ReportService.get_student_info(student_id)
        if not student_info:
            return {"ok": False, "reason": "学生不存在"}

        github_info = ReportService.get_github_info(student_id)
        if not github_info or not github_info.github_username:
            return {"ok": False, "reason": "未绑定 GitHub 账号"}

        course_settings = ReportService.get_course_settings()
        token = github_info.github_token or course_settings.github_token or os.environ.get("GITHUB_TOKEN", "")
        github_service = GitHubService(token=token)
        try:
            profile = await github_service.get_user(github_info.github_username)
        except Exception as e:
            return {"ok": False, "reason": f"请求 GitHub 失败: {str(e)}"}

        if profile is None:
            return {"ok": False, "reason": "GitHub 用户不存在"}

        analysis = analyze_name_match(student_info.name, profile)

        return {
            "ok": True,
            "student_id": student_id,
            "expected_name": student_info.name,
            "github_username": github_info.github_username,
            "analysis": analysis,
        }
