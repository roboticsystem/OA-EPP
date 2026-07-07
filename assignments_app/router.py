"""
作业提交子系统 - API 路由
F-S-020：学生可在截止前提交作业（文本、附件或两者结合），
支持 pdf/docx/zip/py/c/cpp/txt 等常见格式，
展示提交时间、文件大小、版本号。
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from typing import Optional
from pydantic import BaseModel

from .database import db, init_db
from .auth_utils import create_token, verify_student_token, verify_teacher_token

router = APIRouter()

# ----- 配置 -----
UPLOAD_DIR = os.environ.get("ASSIGNMENTS_UPLOAD_DIR", "assignments_uploads")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD")
if not TEACHER_PASSWORD:
    raise RuntimeError("环境变量 TEACHER_PASSWORD 未设置，请设置后启动")

ALLOWED_EXTENSIONS = {"pdf", "docx", "zip", "py", "c", "cpp", "txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# ----- 辅助函数 -----


def _ensure_upload_dir():
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _require_student(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_student_token(token)
        if payload.get("role") != "student":
            raise ValueError("not a student token")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip(".")


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


# ----- Pydantic 模型 -----


class TeacherLoginRequest(BaseModel):
    password: str


class StudentLoginRequest(BaseModel):
    student_id: str


class AssignmentCreate(BaseModel):
    id: str
    title: str
    description: str = ""
    deadline: str
    allowed_formats: str = "pdf,docx,zip,py,c,cpp,txt"
    max_file_size: int = 52428800


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    allowed_formats: Optional[str] = None
    max_file_size: Optional[int] = None
    is_active: Optional[int] = None


# ===================== 教师认证 =====================


@router.post("/api/teacher/login")
def teacher_login(req: TeacherLoginRequest):
    if req.password != TEACHER_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_token({"role": "teacher"}, expires_hours=8)
    return {"token": token}


# ===================== 学生认证 =====================


@router.post("/api/auth/student/login")
def student_login(req: StudentLoginRequest):
    """
    学生学号登录。
    学生身份由平台统一管理，本模块信任平台签发的学号。
    实际部署时，此接口可转发到平台统一认证服务。
    """
    sid = req.student_id.strip()
    if not sid:
        raise HTTPException(status_code=422, detail="学号不能为空")

    token = create_token({
        "role": "student",
        "student_id": sid,
        "name": sid,
    }, expires_hours=8)

    return {
        "token": token,
        "name": sid,
        "student_id": sid,
        "class_name": "",
    }


# ===================== 教师端：作业管理 =====================


@router.post("/api/teacher/assignments")
def create_assignment(req: AssignmentCreate,
                      authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    if not re.match(r"^[\w\-]+$", req.id):
        raise HTTPException(status_code=422,
                          detail="作业ID只能包含字母、数字、下划线和短横线")

    with db() as conn:
        existing = conn.execute(
            "SELECT id FROM assignments WHERE id=?", (req.id,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409,
                              detail=f"作业ID '{req.id}' 已存在")
        conn.execute(
            "INSERT INTO assignments (id, title, description, deadline, "
            "allowed_formats, max_file_size) VALUES (?,?,?,?,?,?)",
            (req.id, req.title, req.description, req.deadline,
             req.allowed_formats, req.max_file_size)
        )
    return {"ok": True}


@router.get("/api/teacher/assignments")
def list_assignments_teacher(
        authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, description, deadline, allowed_formats, "
            "max_file_size, is_active, created_at FROM assignments "
            "ORDER BY created_at DESC"
        ).fetchall()

    result = []
    for r in rows:
        with db() as conn:
            count = conn.execute(
                "SELECT COUNT(DISTINCT student_id) FROM submissions "
                "WHERE assignment_id=?", (r["id"],)
            ).fetchone()[0]
        result.append({**dict(r), "submitted_count": count})
    return result


@router.put("/api/teacher/assignments/{assignment_id}")
def update_assignment(assignment_id: str, req: AssignmentUpdate,
                      authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    fields = []
    values = []
    for field in ("title", "description", "deadline", "allowed_formats",
                  "max_file_size", "is_active"):
        val = getattr(req, field, None)
        if val is not None:
            fields.append(f"{field}=?")
            values.append(val)

    if not fields:
        raise HTTPException(status_code=422, detail="没有需要更新的字段")

    values.append(assignment_id)
    with db() as conn:
        conn.execute(
            f"UPDATE assignments SET {', '.join(fields)} WHERE id=?",
            values
        )
    return {"ok": True}


@router.delete("/api/teacher/assignments/{assignment_id}")
def delete_assignment(assignment_id: str,
                      authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    _ensure_upload_dir()
    with db() as conn:
        conn.execute(
            "DELETE FROM submissions WHERE assignment_id=?",
            (assignment_id,))
        conn.execute(
            "DELETE FROM assignments WHERE id=?", (assignment_id,))

    assign_dir = Path(UPLOAD_DIR) / assignment_id
    if assign_dir.exists():
        shutil.rmtree(str(assign_dir))

    return {"ok": True}


@router.get("/api/teacher/assignments/{assignment_id}/submissions")
def list_submissions_teacher(
        assignment_id: str,
        authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        assignment = conn.execute(
            "SELECT title FROM assignments WHERE id=?",
            (assignment_id,)
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="作业不存在")

        subs = conn.execute(
            "SELECT * FROM submissions "
            "WHERE assignment_id=? ORDER BY student_id, version DESC",
            (assignment_id,)
        ).fetchall()

    sub_map = {}
    for s in subs:
        sid = s["student_id"]
        if sid not in sub_map:
            sub_map[sid] = {
                "student_id": sid,
                "latest_version": s["version"],
                "latest_file_name": s["file_name"],
                "latest_file_size": s["file_size"],
                "latest_submitted_at": s["submitted_at"],
                "version_count": 1,
            }
        else:
            sub_map[sid]["version_count"] += 1

    return {
        "assignment_title": assignment["title"],
        "rows": list(sub_map.values()),
    }


# ===================== 学生端：作业列表与提交 =====================


@router.get("/api/assignments")
def list_active_assignments():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, description, deadline, allowed_formats, "
            "max_file_size, created_at FROM assignments "
            "WHERE is_active=1 ORDER BY deadline ASC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id: str):
    with db() as conn:
        row = conn.execute(
            "SELECT id, title, description, deadline, allowed_formats, "
            "max_file_size, is_active, created_at FROM assignments "
            "WHERE id=?", (assignment_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="作业不存在")
    return dict(row)


@router.post("/api/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    content_text: str = Form(""),
    file: Optional[UploadFile] = File(None),
    authorization: Optional[str] = Header(None),
):
    """★ F-S-020 核心：学生提交作业"""
    payload = _require_student(authorization)
    student_id = payload["student_id"]

    with db() as conn:
        assignment = conn.execute(
            "SELECT id, title, deadline, allowed_formats, "
            "max_file_size, is_active FROM assignments WHERE id=?",
            (assignment_id,)
        ).fetchone()

    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    if not assignment["is_active"]:
        raise HTTPException(status_code=403, detail="该作业已关闭，无法提交")

    # 截止时间校验（兼容两种日期格式）
    now = datetime.now()
    try:
        deadline = datetime.strptime(assignment["deadline"],
                                     "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            deadline = datetime.strptime(assignment["deadline"],
                                         "%Y-%m-%dT%H:%M")
        except ValueError:
            deadline = None

    if deadline and now > deadline:
        raise HTTPException(status_code=403,
                          detail="已超过截止时间，无法提交")

    allowed_list = [f.strip().lower()
                    for f in assignment["allowed_formats"].split(",")]
    max_size = assignment["max_file_size"]

    file_path = file_name = ""
    file_size = 0
    file_type = ""

    if file:
        ext = _get_file_extension(file.filename or "")
        if ext not in allowed_list:
            raise HTTPException(
                status_code=422,
                detail=f"不支持的文件格式 '.{ext}'，"
                       f"允许的格式：{', '.join(allowed_list)}"
            )

        raw = await file.read()
        file_size = len(raw)
        if file_size > max_size:
            raise HTTPException(
                status_code=422,
                detail=f"文件大小 ({_format_file_size(file_size)}) "
                       f"超过限制 ({_format_file_size(max_size)})"
            )

        _ensure_upload_dir()
        assign_dir = Path(UPLOAD_DIR) / assignment_id
        assign_dir.mkdir(parents=True, exist_ok=True)

        file_name = file.filename or "unnamed"
        file_type = ext

    with db() as conn:
        latest = conn.execute(
            "SELECT MAX(version) as max_ver FROM submissions "
            "WHERE assignment_id=? AND student_id=?",
            (assignment_id, student_id)
        ).fetchone()
        new_version = (latest["max_ver"] or 0) + 1

        if file:
            safe_name = f"{student_id}_v{new_version}_{file_name}"
            dest = assign_dir / safe_name
            with open(str(dest), "wb") as f:
                f.write(raw)
            file_path = str(dest)
            file_name = safe_name

        conn.execute(
            "INSERT INTO submissions "
            "(assignment_id, student_id, file_path, file_name, "
            "file_size, file_type, content_text, version) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (assignment_id, student_id, file_path, file_name,
             file_size, file_type, content_text, new_version)
        )

    return {
        "ok": True,
        "version": new_version,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": file_name,
        "file_size": file_size,
        "file_size_display": _format_file_size(file_size)
                              if file_size else "",
    }


@router.get("/api/assignments/{assignment_id}/my-submissions")
def get_my_submissions(
    assignment_id: str,
    authorization: Optional[str] = Header(None),
):
    payload = _require_student(authorization)
    student_id = payload["student_id"]

    with db() as conn:
        rows = conn.execute(
            "SELECT id, version, file_name, file_size, file_type, "
            "content_text, submitted_at FROM submissions "
            "WHERE assignment_id=? AND student_id=? "
            "ORDER BY version DESC",
            (assignment_id, student_id)
        ).fetchall()

    return [{
        "id": r["id"],
        "version": r["version"],
        "file_name": r["file_name"],
        "file_size": r["file_size"],
        "file_size_display": _format_file_size(r["file_size"])
                              if r["file_size"] else "",
        "file_type": r["file_type"],
        "content_text": r["content_text"],
        "submitted_at": r["submitted_at"],
    } for r in rows]


# ===================== 静态页面 =====================


@router.get("/assignments")
def assignments_page():
    static_dir = Path(__file__).parent / "static"
    return FileResponse(str(static_dir / "assignments.html"))


@router.get("/teacher")
def teacher_page():
    static_dir = Path(__file__).parent / "static"
    return FileResponse(str(static_dir / "teacher.html"))
