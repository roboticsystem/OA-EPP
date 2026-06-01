import os
import io
import json
import asyncio
import hashlib
import chardet
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token, verify_teacher_token
from app.sync_exams import sync_exams
from pypinyin import lazy_pinyin, Style
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

router = APIRouter()

TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _name_to_pinyin(name: str):
    full = "".join(lazy_pinyin(name, style=Style.NORMAL))
    abbr = "".join(lazy_pinyin(name, style=Style.FIRST_LETTER))
    return full.lower(), abbr.lower()


class LoginRequest(BaseModel):
    password: str


@router.post("/api/teacher/login")
def teacher_login(req: LoginRequest):
    if req.password != TEACHER_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_token({"role": "teacher"}, expires_hours=8)
    return {"token": token}


@router.post("/api/teacher/students")
async def upload_students(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """上传学生名单 CSV（UTF-8 或 GBK 均支持）"""
    _require_teacher(authorization)

    raw = await file.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    text = raw.decode(encoding, errors="replace")

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(status_code=422, detail="文件为空")

    # 跳过表头
    data_lines = lines[1:] if lines[0].startswith("姓名") or lines[0].startswith("name") else lines

    records = []
    for line in data_lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        name = parts[0]
        student_no = parts[1]
        class_name = parts[2] if len(parts) > 2 else ""
        if not name or not student_no:
            continue
        records.append((name, student_no, class_name))

    if not records:
        raise HTTPException(status_code=422, detail="CSV 中没有有效数据行")

    with db() as conn:
        for name, student_no, class_name in records:
            user_existing = conn.execute(
                "SELECT id FROM users WHERE student_no=%s", (student_no,)
            ).fetchone()
            if user_existing:
                conn.execute(
                    "UPDATE users SET full_name=%s WHERE id=%s",
                    (name, user_existing["id"])
                )
                conn.execute(
                    "UPDATE students SET class_name=%s WHERE user_id=%s",
                    (class_name, user_existing["id"])
                )
            else:
                user_result = conn.execute(
                    "INSERT INTO users (role, student_no, email, password_hash, full_name) VALUES ('student', %s, %s, 'dummy', %s)",
                    (student_no, f"{student_no}@edu.local", name)
                )
                conn.execute(
                    "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
                    (user_result.lastrowid, class_name)
                )

    return {"count": len(records)}


class AddStudentRequest(BaseModel):
    name: str
    student_no: str
    class_name: str = ""


@router.post("/api/teacher/students/add")
def add_student(req: AddStudentRequest, authorization: Optional[str] = Header(None)):
    """添加单个学生"""
    _require_teacher(authorization)
    req.name = req.name.strip()
    req.student_no = req.student_no.strip()
    if not req.name or not req.student_no:
        raise HTTPException(status_code=422, detail="姓名和学号不能为空")
    with db() as conn:
        user_existing = conn.execute(
            "SELECT id, full_name FROM users WHERE student_no=%s", (req.student_no,)
        ).fetchone()
        if user_existing:
            raise HTTPException(status_code=409, detail=f"学号 {req.student_no} 已存在（{user_existing['full_name']}）")
        user_result = conn.execute(
            "INSERT INTO users (role, student_no, email, password_hash, full_name) VALUES ('student', %s, %s, 'dummy', %s)",
            (req.student_no, f"{req.student_no}@edu.local", req.name)
        )
        conn.execute(
            "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
            (user_result.lastrowid, req.class_name.strip())
        )
    return {"ok": True}


@router.delete("/api/teacher/students/{student_no}")
def delete_student(student_no: str, authorization: Optional[str] = Header(None)):
    """删除单个学生（同时删除其成绩）"""
    _require_teacher(authorization)
    with db() as conn:
        user = conn.execute(
            "SELECT id, full_name FROM users WHERE student_no=%s", (student_no,)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="学号不存在")
        conn.execute("DELETE FROM exam_attempts WHERE student_user_id=%s", (user["id"],))
        conn.execute("DELETE FROM submissions WHERE student_user_id=%s", (user["id"],))
        conn.execute("DELETE FROM students WHERE user_id=%s", (user["id"],))
        conn.execute("DELETE FROM users WHERE id=%s", (user["id"],))
    return {"ok": True, "deleted": user["full_name"]}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    """清空全部学生名单（同时清空所有成绩）"""
    _require_teacher(authorization)
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()['cnt']
        conn.execute("DELETE FROM exam_attempts")
        conn.execute("DELETE FROM submissions")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM users WHERE role='student'")
    return {"ok": True, "deleted_count": count}


@router.post("/api/teacher/reset")
def new_semester_reset(authorization: Optional[str] = Header(None)):
    """新学期重置：清空所有学生名单 + 所有成绩"""
    _require_teacher(authorization)
    with db() as conn:
        students = conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()['cnt']
        exam_attempts_count = conn.execute("SELECT COUNT(*) AS cnt FROM exam_attempts").fetchone()['cnt']
        conn.execute("DELETE FROM exam_attempts")
        conn.execute("DELETE FROM submissions")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM users WHERE role='student'")
    return {"ok": True, "deleted_students": students, "deleted_exam_attempts": exam_attempts_count}


@router.get("/api/teacher/students/list")
def list_students(authorization: Optional[str] = Header(None)):
    """获取全部学生名单"""
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT u.full_name AS name, u.id AS student_id, s.class_name FROM users u JOIN students s ON u.id = s.user_id WHERE u.role = 'student' AND u.is_active = 1 ORDER BY s.class_name, u.full_name"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/teacher/exams")
def list_exams(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exams = conn.execute(
            "SELECT id, title, exam_type, start_at, end_at FROM exams ORDER BY id"
        ).fetchall()
        total_students = conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()['cnt']
        result = []
        for e in exams:
            now = datetime.now()
            is_active = e["start_at"] <= now <= e["end_at"]
            submitted = conn.execute(
                "SELECT COUNT(*) AS cnt FROM exam_attempts WHERE exam_id=%s", (e["id"],)
            ).fetchone()['cnt']
            avg = conn.execute(
                "SELECT AVG(total_score) AS avg_score FROM exam_attempts WHERE exam_id=%s AND total_score IS NOT NULL", (e["id"],)
            ).fetchone()['avg_score']
            result.append({
                "id": e["id"], "title": e["title"],
                "exam_type": e["exam_type"],
                "is_active": is_active,
                "start_at": e["start_at"], "end_at": e["end_at"],
                "submitted": submitted, "total_students": total_students,
                "avg_score": round(avg, 1) if avg else None,
            })
    return result


@router.get("/api/teacher/semesters")
def list_semesters(authorization: Optional[str] = Header(None)):
    """返回所有已配置的学期列表（供下拉筛选器使用）。"""
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT c.term FROM courses c WHERE c.term IS NOT NULL AND c.term != '' ORDER BY c.term DESC"
        ).fetchall()
    semesters = [r["term"] for r in rows]
    if not semesters:
        now = datetime.now()
        if now.month >= 9:
            semesters = [f"{now.year}-{now.year+1}-1"]
        elif now.month <= 2:
            semesters = [f"{now.year-1}-{now.year}-1"]
        else:
            semesters = [f"{now.year-1}-{now.year}-2"]
    return {"semesters": semesters}


class ExamCreate(BaseModel):
    course_id: int
    title: str
    exam_type: str = "quiz"
    start_at: str
    end_at: str


@router.post("/api/teacher/exams")
def create_exam(req: ExamCreate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        conn.execute(
            "INSERT INTO exams (course_id, title, exam_type, start_at, end_at, created_by) VALUES (%s,%s,%s,%s,%s,0)",
            (req.course_id, req.title, req.exam_type, req.start_at, req.end_at)
        )
    return {"ok": True}


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    exam_type: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None


@router.put("/api/teacher/exams/{exam_id}")
def update_exam(exam_id: int, req: ExamUpdate, authorization: Optional[str] = Header(None)):
    """更新考试属性"""
    _require_teacher(authorization)
    updates = {}
    if req.title is not None:
        updates["title"] = req.title
    if req.exam_type is not None:
        updates["exam_type"] = req.exam_type
    if req.start_at is not None:
        updates["start_at"] = req.start_at
    if req.end_at is not None:
        updates["end_at"] = req.end_at

    if not updates:
        raise HTTPException(status_code=422, detail="没有需要更新的字段")

    set_clause = ", ".join(f"{k}=%s" for k in updates)
    values = list(updates.values())
    with db() as conn:
        existing = conn.execute("SELECT id FROM exams WHERE id=%s", (exam_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")
        conn.execute(f"UPDATE exams SET {set_clause} WHERE id=%s", (*values, exam_id))
    return {"ok": True, "updated": updates}


@router.get("/api/teacher/scores")
def get_scores(exam_id: int = Query(...), authorization: Optional[str] = Header(None)):
    """获取某次考试的所有学生成绩（含未提交）"""
    _require_teacher(authorization)
    with db() as conn:
        exam = conn.execute("SELECT title FROM exams WHERE id=%s", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute("""
            SELECT u.id as student_id, u.full_name as name, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.role = 'student' AND u.is_active = 1
            ORDER BY u.full_name
        """).fetchall()
        scores_map = {
            r["student_user_id"]: dict(r)
            for r in conn.execute(
                "SELECT student_user_id, total_score, submitted_at FROM exam_attempts WHERE exam_id=%s",
                (exam_id,)
            ).fetchall()
        }

    result = []
    for s in students:
        sc = scores_map.get(s["student_id"])
        result.append({
            "name": s["name"],
            "student_id": s["student_id"],
            "class_name": s["class_name"],
            "score": sc["total_score"] if sc else None,
            "submitted_at": sc["submitted_at"] if sc else None,
        })

    return {"exam_title": exam["title"], "rows": result}


@router.get("/api/teacher/scores/export")
def export_scores(exam_id: int = Query(...), authorization: Optional[str] = Header(None)):
    """导出成绩 Excel"""
    _require_teacher(authorization)

    with db() as conn:
        exam = conn.execute("SELECT title FROM exams WHERE id=%s", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute("""
            SELECT u.id as student_id, u.full_name as name, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.role = 'student' AND u.is_active = 1
            ORDER BY u.full_name
        """).fetchall()
        scores_map = {
            r["student_user_id"]: dict(r)
            for r in conn.execute(
                "SELECT student_user_id, total_score, submitted_at FROM exam_attempts WHERE exam_id=%s",
                (exam_id,)
            ).fetchall()
        }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = exam["title"][:31]

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["姓名", "学号", "班级", "得分", "提交时间"]
    col_widths = [12, 14, 20, 8, 20]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = w

    for row_idx, s in enumerate(students, 2):
        sc = scores_map.get(s["student_id"])
        ws.cell(row=row_idx, column=1, value=s["name"])
        ws.cell(row=row_idx, column=2, value=s["student_id"])
        ws.cell(row=row_idx, column=3, value=s["class_name"])
        ws.cell(row=row_idx, column=4, value=sc["total_score"] if sc else "")
        ws.cell(row=row_idx, column=5, value=sc["submitted_at"] if sc else "")
        if not sc:
            for col in range(1, 6):
                ws.cell(row=row_idx, column=col).font = Font(color="999999")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    from urllib.parse import quote
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"成绩单_{exam['title']}_{date_str}.xlsx"
    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


# ══════════════════════════════════════════════════════════════════════════════
#  进度看板 API — 热力图 + 柱状图 + SSE 实时推送
# ══════════════════════════════════════════════════════════════════════════════

def _compute_progress_data(semester: str = "") -> dict:
    """构建全班「学生 × 考试」二维完成状态矩阵 + 各考试完成率。"""
    with db() as cursor:
        students = cursor.execute("""
            SELECT u.id as student_id, u.full_name as name, s.class_name, u.student_no
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.role = 'student' AND u.is_active = 1
            ORDER BY u.full_name
        """).fetchall()

        exams = cursor.execute("""
            SELECT id, title, start_at, end_at, exam_type
            FROM exams
            ORDER BY start_at, id
        """).fetchall()

        exam_attempts = cursor.execute("""
            SELECT ea.student_user_id, ea.exam_id, ea.total_score, ea.submitted_at, ea.status
            FROM exam_attempts ea
        """).fetchall()

    sub_map: dict = {}
    for row in exam_attempts:
        sub_map[(row["student_user_id"], row["exam_id"])] = {
            "total_score": row["total_score"],
            "submitted_at": row["submitted_at"],
            "status": row["status"],
        }

    student_list = []
    student_ids = []
    for s in students:
        student_ids.append(s["student_id"])
        statuses = {}
        submitted_count = 0
        total_exams = 0
        for e in exams:
            total_exams += 1
            key = (s["student_id"], e["id"])
            if key in sub_map:
                sub = sub_map[key]
                statuses[e["id"]] = {
                    "status": "submitted" if sub["status"] == "submitted" else "draft",
                    "score": sub["total_score"],
                    "submitted_at": sub["submitted_at"],
                }
                submitted_count += 1
            else:
                statuses[e["id"]] = {"status": "unsubmitted"}

        completion_rate = round(submitted_count / total_exams, 3) if total_exams > 0 else 0.0
        student_list.append({
            "student_id": s["student_id"],
            "student_no": s["student_no"],
            "name": s["name"],
            "class_name": s["class_name"],
            "completion_rate": completion_rate,
            "statuses": statuses,
        })

    exam_list = []
    for e in exams:
        now = datetime.now()
        is_active = e["start_at"] <= now <= e["end_at"]
        submitted = sum(
            1 for sid in student_ids
            if (sid, e["id"]) in sub_map
        )
        exam_list.append({
            "id": e["id"],
            "title": e["title"],
            "is_active": is_active,
            "start_at": e["start_at"],
            "end_at": e["end_at"],
            "exam_type": e["exam_type"],
            "total_students": len(student_ids),
            "submitted": submitted,
            "completion_rate": round(submitted / len(student_ids), 3) if len(student_ids) > 0 else 0.0,
        })

    return {"students": student_list, "exams": exam_list}


def _progress_data_hash(data: dict) -> str:
    """计算进度数据的哈希，用于 SSE 变更检测。"""
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


@router.get("/api/teacher/progress/matrix")
def progress_matrix(
    authorization: Optional[str] = Header(None),
    bottom_n: int = Query(5, ge=0, le=100),
    sort_order: str = Query("completion_asc", pattern="^(completion_asc|name_asc)$"),
    course: str = Query("", description="按班级筛选（模糊匹配 class_name）"),
    semester: str = Query("", description="按学期筛选"),
):
    """返回全班「学生 × 任务」二维完成状态矩阵。

    参数：
    - bottom_n: 完成率最低前 N 名置顶高亮，默认 5
    - sort_order: completion_asc|name_asc
    - course: 按 class_name 筛选
    - semester: 按学期筛选（如 "2024-2025-2"）
    """
    _require_teacher(authorization)
    data = _compute_progress_data(semester=semester)

    # 按班级/课程筛选
    if course:
        data["students"] = [
            s for s in data["students"]
            if course.lower() in (s.get("class_name") or "").lower()
        ]

    students = data["students"]
    if not students:
        return {"students": [], "exams": data["exams"], "bottom_n": bottom_n}

    # 标记完成率最低前 N 名
    if sort_order == "completion_asc" and bottom_n > 0:
        sorted_by_rate = sorted(students, key=lambda x: x["completion_rate"])
        bottom_ids = {s["student_id"] for s in sorted_by_rate[:bottom_n]}
        for s in students:
            s["highlight"] = s["student_id"] in bottom_ids

        # 低完成率学生置顶
        bottom_students = [s for s in students if s["student_id"] in bottom_ids]
        other_students = [s for s in students if s["student_id"] not in bottom_ids]
        students = bottom_students + other_students
    elif sort_order == "name_asc":
        students = sorted(students, key=lambda x: x["name"])

    return {"students": students, "exams": data["exams"], "bottom_n": bottom_n}


@router.get("/api/teacher/progress/completion")
def progress_completion(
    authorization: Optional[str] = Header(None),
    course: str = Query("", description="按班级筛选"),
    semester: str = Query("", description="按学期筛选"),
):
    """返回各任务在全班的完成率趋势（供柱状图使用）。"""
    _require_teacher(authorization)
    data = _compute_progress_data(semester=semester)

    # 仅返回活跃考试
    exams = [
        e for e in data["exams"]
        if e["is_active"] or e["submitted"] > 0
    ]

    # 按班级筛选完成率
    if course:
        with db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM students WHERE class_name LIKE %s",
                (f"%{course}%",)
            ).fetchone()['cnt']
        for e in exams:
            if total > 0:
                e["total_students"] = total
                e["completion_rate"] = round(e["submitted"] / total, 3)

    return {"exams": exams}


@router.get("/api/teacher/progress/events")
async def progress_events(
    request: Request,
    token: str = Query("", description="教师 JWT token（EventSource 不支持自定义 Header）"),
    semester: str = Query("", description="学期筛选"),
):
    """SSE 端点：进度数据变更时实时推送给前端。

    每 5 秒检查数据是否变化，变化时推送完整矩阵 + 完成率数据。
    前端无需手动刷新页面。

    注：因浏览器 EventSource API 不支持自定义请求头，
    认证 token 通过 URL 查询参数传递。
    """
    # SSE 端点：通过 query param 认证（EventSource 不支持 Authorization header）
    if token:
        try:
            verify_teacher_token(token)
        except ValueError:
            raise HTTPException(status_code=401, detail="token 无效或已过期")
    else:
        raise HTTPException(status_code=401, detail="缺少认证 token")

    async def event_stream() -> AsyncGenerator[str, None]:
        last_hash = ""
        while True:
            # 检查客户端是否断开
            if await request.is_disconnected():
                break
            try:
                data = _compute_progress_data(semester=semester)
                current_hash = _progress_data_hash(data)
                if current_hash != last_hash:
                    last_hash = current_hash
                    payload = json.dumps(data, ensure_ascii=False, default=str)
                    yield f"data: {payload}\n\n"
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(10)  # 出错时延长等待

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
