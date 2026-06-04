import asyncio
import io
from collections import Counter
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from urllib.parse import quote

from app.auth_utils import verify_teacher_token
from app.services.report_service import ReportService
from app.services.export_service import ExportService
from app.services.github_service import GitHubService
from app.services.ai_review_service import run_full_ai_review, ai_generate_review_comment
from app.models.report_models import (
    ReportData, GitHubInfo, CourseSettings, AuditLogResponse,
    TeacherComment, AttendanceRecord, BatchExportRequest, StudentInfo,
    AIReviewResult, AIReviewRequest, CommitAnalysisResult, BranchAnalysisResult,
    PRAnalysisResult, ActivityAnalysisResult, CodeScaleResult, AIDimensions
)

router = APIRouter(prefix="/api/teacher/report", tags=["报告管理"])


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _get_client_info(request: Optional[Request]):
    if request is None:
        return None, ""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    return ip_address, user_agent


class SaveGitHubInfoRequest(BaseModel):
    student_id: str
    github_username: str
    repo_name: str
    github_token: str = ""


class SaveCommentRequest(BaseModel):
    student_id: str
    comment: str


class SaveAttendanceRequest(BaseModel):
    student_id: str
    records: List[AttendanceRecord]


class UpdateSettingsRequest(BaseModel):
    course_name: str
    semester: str
    github_token: str = ""


@router.get("/student/{student_id}")
async def get_student_report(
    student_id: str,
    refresh: bool = Query(False, description="是否强制刷新GitHub数据"),
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    _require_teacher(authorization)

    report = await ReportService.get_full_report(student_id, refresh=refresh)
    if not report:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    return report


@router.get("/export")
async def export_report(
    student_id: str = Query(...),
    format: str = Query("pdf", pattern="^(pdf|html|excel)$"),
    refresh: bool = Query(False),
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    report = await ReportService.get_full_report(student_id, refresh=refresh)
    if not report:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    ReportService.log_audit(
        action=f"export_{format}",
        target_type="student",
        target_id=student_id,
        format=format,
        ip_address=ip_address,
        user_agent=user_agent
    )

    filename = ExportService.get_export_filename(report, format)

    if format == "pdf":
        try:
            content = ExportService.generate_pdf(report)
            media_type = "application/pdf"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
    elif format == "html":
        content = ExportService.generate_html(report).encode('utf-8')
        media_type = "text/html"
    else:
        content = ExportService.generate_excel(report)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(len(content))
        }
    )


@router.post("/batch")
async def batch_export(
    req: BatchExportRequest,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    if not req.class_name and not req.student_ids:
        raise HTTPException(status_code=400, detail="请提供班级名称或学生列表")

    if req.class_name:
        students = ReportService.get_students_by_class(req.class_name)
        student_ids = [s.student_id for s in students]
        target_name = req.class_name
    else:
        student_ids = req.student_ids
        target_name = f"{len(student_ids)}名学生"

    ReportService.log_audit(
        action=f"export_batch_{req.format}",
        target_type="class",
        target_id=target_name,
        format=req.format,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"student_count={len(student_ids)}"
    )

    files = []
    for student_id in student_ids:
        try:
            report = await ReportService.get_full_report(student_id, refresh=False)
            if report:
                if req.format == "pdf":
                    content = ExportService.generate_pdf(report)
                    ext = "pdf"
                elif req.format == "html":
                    content = ExportService.generate_html(report).encode('utf-8')
                    ext = "html"
                else:
                    content = ExportService.generate_excel(report)
                    ext = "xlsx"

                filename = ExportService.get_export_filename(report, req.format)
                files.append((filename, report.student_info.name, content))
        except Exception as e:
            continue

    if not files:
        raise HTTPException(status_code=404, detail="没有找到任何学生的报告数据")

    zip_content = ExportService.generate_zip(files)
    date_str = datetime.now().strftime("%Y%m%d")
    zip_filename = f"开发日志报告批量导出_{target_name}_{date_str}.zip"
    encoded_filename = quote(zip_filename, safe="")

    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(len(zip_content))
        }
    )


@router.get("/logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    return ReportService.get_audit_logs(
        page=page,
        page_size=page_size,
        student_id=student_id,
        action=action,
        start_date=start_date,
        end_date=end_date
    )


@router.post("/github-info")
def save_github_info(
    req: SaveGitHubInfoRequest,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    info = GitHubInfo(
        student_id=req.student_id,
        github_username=req.github_username,
        repo_name=req.repo_name,
        github_token=req.github_token
    )
    ReportService.save_github_info(info)
    return {"ok": True}


@router.get("/github-info/{student_id}")
def get_github_info(
    student_id: str,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    info = ReportService.get_github_info(student_id)
    if not info:
        return GitHubInfo(student_id=student_id)
    return info


@router.post("/github-verify/{student_id}")
async def github_verify(
    student_id: str,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    result = await ReportService.verify_github_real_name(student_id)

    ReportService.log_audit(
        action="github_verify",
        target_type="student",
        target_id=student_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=str(result)
    )

    return result


@router.post("/comments")
def save_comment(
    req: SaveCommentRequest,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    ReportService.save_teacher_comment(req.student_id, req.comment)
    ReportService.log_audit(
        action="save_comment",
        target_type="student",
        target_id=req.student_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {"ok": True}


@router.get("/comments/{student_id}")
def get_comments(
    student_id: str,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    return ReportService.get_teacher_comments(student_id)


@router.delete("/comments/{student_id}")
def delete_comment(
    student_id: str,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    ReportService.delete_teacher_comment(student_id)
    return {"ok": True}


@router.post("/attendance")
def save_attendance(
    req: SaveAttendanceRequest,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    ReportService.save_attendance_records(req.student_id, req.records)
    return {"ok": True}


@router.get("/attendance/{student_id}")
def get_attendance(
    student_id: str,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    return ReportService.get_attendance_records(student_id)


@router.get("/settings")
def get_settings(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return ReportService.get_course_settings()


@router.put("/settings")
def update_settings(
    req: UpdateSettingsRequest,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)

    settings = CourseSettings(
        course_name=req.course_name,
        semester=req.semester,
        github_token=req.github_token
    )
    ReportService.update_course_settings(settings)
    return {"ok": True}


@router.get("/classes")
def get_classes(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return ReportService.get_classes()


@router.get("/classes/{class_name}/students")
def get_class_students(
    class_name: str,
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    return ReportService.get_students_by_class(class_name)


# ---------------------------------------------------------------------------
# F-T-003-AI: AI 自动审查接口
# ---------------------------------------------------------------------------

@router.get("/ai-review/{student_id}")
async def get_ai_review(
    student_id: str,
    refresh: bool = Query(False, description="是否强制刷新GitHub数据并重新审查"),
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """获取学生的 AI 自动审查结果。从 GitHub 拉取数据后进行多维度自动分析。"""
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    # 获取学生信息
    student_info = ReportService.get_student_info(student_id)
    if not student_info:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    # 获取 GitHub 信息
    github_info = ReportService.get_github_info(student_id)
    if not github_info or not github_info.github_username or not github_info.repo_name:
        raise HTTPException(status_code=400, detail="该学生未绑定 GitHub 仓库信息")

    # 获取 GitHub 数据
    course_settings = ReportService.get_course_settings()
    token = github_info.github_token or course_settings.github_token
    github_service = GitHubService(token=token)

    try:
        github_data = await github_service.get_full_data(
            github_info.github_username,
            github_info.repo_name
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取 GitHub 数据失败: {str(e)}")

    if not github_data.get("commits") and not github_data.get("branches"):
        raise HTTPException(status_code=404, detail="GitHub 仓库无数据")

    # 运行 AI 审查
    result = run_full_ai_review(
        github_data=github_data,
        student_name=student_info.name,
        student_id=student_id,
    )

    # 记录审计日志
    ReportService.log_audit(
        action="ai_review",
        target_type="student",
        target_id=student_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"score={result.get('overall_score')},grade={result.get('grade')}"
    )

    return result


@router.post("/ai-review/{student_id}")
async def trigger_ai_review(
    student_id: str,
    refresh: bool = Query(True, description="是否从GitHub重新获取最新数据"),
    generate_ai_comment: bool = Query(False, description="是否调用AI API生成智能评语"),
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """触发 AI 自动审查（支持 AI API 生成智能评语）。"""
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    student_info = ReportService.get_student_info(student_id)
    if not student_info:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    github_info = ReportService.get_github_info(student_id)
    if not github_info or not github_info.github_username or not github_info.repo_name:
        raise HTTPException(status_code=400, detail="该学生未绑定 GitHub 仓库信息")

    course_settings = ReportService.get_course_settings()
    token = github_info.github_token or course_settings.github_token
    github_service = GitHubService(token=token)

    if refresh:
        github_service.clear_cache()

    try:
        github_data = await github_service.get_full_data(
            github_info.github_username,
            github_info.repo_name
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取 GitHub 数据失败: {str(e)}")

    if not github_data.get("commits") and not github_data.get("branches"):
        raise HTTPException(status_code=404, detail="GitHub 仓库无数据")

    result = run_full_ai_review(
        github_data=github_data,
        student_name=student_info.name,
        student_id=student_id,
    )

    # 可选：调用 AI API 生成智能评语
    ai_comment = None
    if generate_ai_comment:
        ai_comment = await ai_generate_review_comment(result)
        if ai_comment:
            result["ai_comment"] = ai_comment

    ReportService.log_audit(
        action="ai_review",
        target_type="student",
        target_id=student_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"score={result.get('overall_score')},grade={result.get('grade')},ai_comment={'yes' if ai_comment else 'no'}"
    )

    return result


@router.get("/ai-review/{student_id}/summary")
async def get_ai_review_summary(
    student_id: str,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """获取 AI 审查摘要（轻量版，仅返回总分、评级和建议）。"""
    _require_teacher(authorization)

    student_info = ReportService.get_student_info(student_id)
    if not student_info:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    github_info = ReportService.get_github_info(student_id)
    if not github_info or not github_info.github_username or not github_info.repo_name:
        raise HTTPException(status_code=400, detail="该学生未绑定 GitHub 仓库信息")

    course_settings = ReportService.get_course_settings()
    token = github_info.github_token or course_settings.github_token
    github_service = GitHubService(token=token)

    try:
        github_data = await github_service.get_full_data(
            github_info.github_username,
            github_info.repo_name
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取 GitHub 数据失败: {str(e)}")

    if not github_data.get("commits") and not github_data.get("branches"):
        raise HTTPException(status_code=404, detail="GitHub 仓库无数据")

    result = run_full_ai_review(
        github_data=github_data,
        student_name=student_info.name,
        student_id=student_id,
    )

    # 仅返回摘要信息
    return {
        "student_id": student_id,
        "student_name": student_info.name,
        "overall_score": result["overall_score"],
        "grade": result["grade"],
        "grade_desc": result["grade_desc"],
        "summary": result["summary"],
        "highlights": result["highlights"],
        "risks": result["risks"],
        "suggestions": result["suggestions"],
        "reviewed_at": result["reviewed_at"],
    }


@router.post("/ai-review/batch")
async def batch_ai_review(
    req: BatchExportRequest,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """批量 AI 审查——按班级批量执行代码审查并返回汇总。"""
    _require_teacher(authorization)
    ip_address, user_agent = _get_client_info(request)

    if not req.class_name and not req.student_ids:
        raise HTTPException(status_code=400, detail="请提供班级名称或学生列表")

    if req.class_name:
        students = ReportService.get_students_by_class(req.class_name)
        student_ids = [s.student_id for s in students]
        target_name = req.class_name
    else:
        student_ids = req.student_ids
        target_name = f"{len(student_ids)}名学生"

    results = []
    errors = []
    course_settings = ReportService.get_course_settings()

    for student_id in student_ids:
        try:
            student_info = ReportService.get_student_info(student_id)
            if not student_info:
                errors.append({"student_id": student_id, "error": "学生不存在"})
                continue

            github_info = ReportService.get_github_info(student_id)
            if not github_info or not github_info.github_username or not github_info.repo_name:
                errors.append({"student_id": student_id, "error": "未绑定GitHub"})
                continue

            token = github_info.github_token or course_settings.github_token
            github_service = GitHubService(token=token)
            github_data = await github_service.get_full_data(
                github_info.github_username,
                github_info.repo_name
            )

            if not github_data.get("commits") and not github_data.get("branches"):
                errors.append({"student_id": student_id, "error": "GitHub仓库无数据"})
                continue

            review = run_full_ai_review(
                github_data=github_data,
                student_name=student_info.name,
                student_id=student_id,
            )
            results.append({
                "student_id": student_id,
                "student_name": student_info.name,
                "overall_score": review["overall_score"],
                "grade": review["grade"],
                "grade_desc": review["grade_desc"],
                "summary": review["summary"],
                "reviewed_at": review["reviewed_at"],
            })
        except Exception as e:
            errors.append({"student_id": student_id, "error": str(e)})

    # 班级汇总
    if results:
        avg_score = round(sum(r["overall_score"] for r in results) / len(results), 1)
        grade_distribution = Counter(r["grade"] for r in results)
    else:
        avg_score = 0
        grade_distribution = {}

    ReportService.log_audit(
        action="ai_review_batch",
        target_type="class",
        target_id=target_name,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"reviewed={len(results)},errors={len(errors)},avg_score={avg_score}"
    )

    return {
        "target": target_name,
        "total": len(student_ids),
        "reviewed": len(results),
        "errors": errors,
        "average_score": avg_score,
        "grade_distribution": dict(grade_distribution),
        "results": results,
    }
