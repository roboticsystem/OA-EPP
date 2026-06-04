import asyncio
import io
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from urllib.parse import quote

from app.auth_utils import verify_teacher_token
from app.services.report_service import ReportService
from app.services.export_service import ExportService
from app.models.report_models import (
    ReportData, GitHubInfo, CourseSettings, AuditLogResponse,
    TeacherComment, AttendanceRecord, BatchExportRequest, StudentInfo
)

router = APIRouter(prefix="/api/teacher/report", tags=["报告管理"])


def _require_teacher(authorization: Optional[str], request: Request = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _get_client_info(request: Request):
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
