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
        student_id = parts[1]
        class_name = parts[2] if len(parts) > 2 else ""
        if not name or not student_id:
            continue
        pinyin, abbr = _name_to_pinyin(name)
        records.append((name, student_id, class_name, pinyin, abbr))

    if not records:
        raise HTTPException(status_code=422, detail="CSV 中没有有效数据行")

    with db() as conn:
        conn.executemany("""
            INSERT INTO students (name, student_id, class_name, pinyin, pinyin_abbr)
            VALUES (?,?,?,?,?)
            ON CONFLICT(student_id) DO UPDATE SET
                name=excluded.name,
                class_name=excluded.class_name,
                pinyin=excluded.pinyin,
                pinyin_abbr=excluded.pinyin_abbr
        """, records)

    return {"count": len(records)}


class AddStudentRequest(BaseModel):
    name: str
    student_id: str
    class_name: str = ""


@router.post("/api/teacher/students/add")
def add_student(req: AddStudentRequest, authorization: Optional[str] = Header(None)):
    """添加单个学生"""
    _require_teacher(authorization)
    req.name = req.name.strip()
    req.student_id = req.student_id.strip()
    if not req.name or not req.student_id:
        raise HTTPException(status_code=422, detail="姓名和学号不能为空")
    pinyin, abbr = _name_to_pinyin(req.name)
    with db() as conn:
        existing = conn.execute(
            "SELECT name FROM students WHERE student_id=?", (req.student_id,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"学号 {req.student_id} 已存在（{existing['name']}）")
        conn.execute(
            "INSERT INTO students (name, student_id, class_name, pinyin, pinyin_abbr) VALUES (?,?,?,?,?)",
            (req.name, req.student_id, req.class_name.strip(), pinyin, abbr)
        )
    return {"ok": True}


@router.delete("/api/teacher/students/{student_id}")
def delete_student(student_id: str, authorization: Optional[str] = Header(None)):
    """删除单个学生（同时删除其成绩）"""
    _require_teacher(authorization)
    with db() as conn:
        student = conn.execute(
            "SELECT name FROM students WHERE student_id=?", (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")
        conn.execute("DELETE FROM scores WHERE student_id=?", (student_id,))
        conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    return {"ok": True, "deleted": student["name"]}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    """清空全部学生名单（同时清空所有成绩）"""
    _require_teacher(authorization)
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        conn.execute("DELETE FROM scores")
        conn.execute("DELETE FROM students")
    return {"ok": True, "deleted_count": count}


@router.post("/api/teacher/reset")
def new_semester_reset(authorization: Optional[str] = Header(None)):
    """新学期重置：清空所有学生名单 + 所有成绩"""
    _require_teacher(authorization)
    with db() as conn:
        students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        scores   = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
        conn.execute("DELETE FROM scores")
        conn.execute("DELETE FROM students")
    return {"ok": True, "deleted_students": students, "deleted_scores": scores}


@router.get("/api/teacher/students/list")
def list_students(authorization: Optional[str] = Header(None)):
    """获取全部学生名单"""
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT name, student_id, class_name FROM students ORDER BY class_name, name"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/teacher/exams")
def list_exams(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exams = conn.execute(
            "SELECT id, title, is_active, deadline, published_at, semester FROM exams ORDER BY id"
        ).fetchall()

    # 懒加载同步：若数据库中还没有考试记录，尝试立即扫描文档目录
    if not exams:
        print("[list_exams] 考试表为空，触发懒加载同步…")
        sync_exams()
        with db() as conn:
            exams = conn.execute(
                "SELECT id, title, is_active, deadline, published_at, semester FROM exams ORDER BY id"
            ).fetchall()

    with db() as conn:
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        result = []
        for e in exams:
            submitted = conn.execute(
                "SELECT COUNT(*) FROM scores WHERE exam_id=?", (e["id"],)
            ).fetchone()[0]
            avg = conn.execute(
                "SELECT AVG(score) FROM scores WHERE exam_id=?", (e["id"],)
            ).fetchone()[0]
            result.append({
                "id": e["id"], "title": e["title"], "is_active": e["is_active"],
                "deadline": e["deadline"], "published_at": e["published_at"],
                "semester": e["semester"] or "",
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
            "SELECT DISTINCT semester FROM exams WHERE semester IS NOT NULL AND semester != '' ORDER BY semester DESC"
        ).fetchall()
    semesters = [r["semester"] for r in rows]
    # 如果数据库中没有学期数据，返回一个默认值
    if not semesters:
        now = datetime.now()
        # 推算当前学期：9月-次年2月为第一学期，3月-8月为第二学期
        if now.month >= 9:
            semesters = [f"{now.year}-{now.year+1}-1"]
        elif now.month <= 2:
            semesters = [f"{now.year-1}-{now.year}-1"]
        else:
            semesters = [f"{now.year-1}-{now.year}-2"]
    return {"semesters": semesters}


class ExamCreate(BaseModel):
    id: str
    title: str


@router.post("/api/teacher/exams")
def create_exam(req: ExamCreate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO exams (id, title) VALUES (?,?)",
            (req.id, req.title)
        )
    return {"ok": True}


class ExamUpdate(BaseModel):
    is_active: Optional[int] = None
    deadline: Optional[str] = None       # ISO datetime, e.g. "2025-06-30T23:59"
    published_at: Optional[str] = None   # ISO datetime
    semester: Optional[str] = None       # e.g. "2024-2025-2"


@router.put("/api/teacher/exams/{exam_id}")
def update_exam(exam_id: str, req: ExamUpdate, authorization: Optional[str] = Header(None)):
    """更新考试属性：开关、截止时间、发布时间、学期。"""
    _require_teacher(authorization)
    updates = {}
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    if req.deadline is not None:
        updates["deadline"] = req.deadline
    if req.published_at is not None:
        updates["published_at"] = req.published_at
    if req.semester is not None:
        updates["semester"] = req.semester

    if not updates:
        raise HTTPException(status_code=422, detail="没有需要更新的字段")

    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values())
    with db() as conn:
        existing = conn.execute("SELECT id FROM exams WHERE id=?", (exam_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")
        conn.execute(f"UPDATE exams SET {set_clause} WHERE id=?", (*values, exam_id))
    return {"ok": True, "updated": updates}


@router.get("/api/teacher/scores")
def get_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """获取某次考试的所有学生成绩（含未提交）"""
    _require_teacher(authorization)
    with db() as conn:
        exam = conn.execute("SELECT title FROM exams WHERE id=?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute(
            "SELECT name, student_id, class_name FROM students ORDER BY student_id"
        ).fetchall()
        scores_map = {
            r["student_id"]: dict(r)
            for r in conn.execute(
                "SELECT student_id, score, total, submitted_at FROM scores WHERE exam_id=?",
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
            "score": sc["score"] if sc else None,
            "total": sc["total"] if sc else None,
            "submitted_at": sc["submitted_at"] if sc else None,
        })

    return {"exam_title": exam["title"], "rows": result}


@router.get("/api/teacher/scores/export")
def export_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """导出成绩 Excel"""
    _require_teacher(authorization)

    with db() as conn:
        exam = conn.execute("SELECT title FROM exams WHERE id=?", (exam_id,)).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute(
            "SELECT name, student_id, class_name FROM students ORDER BY student_id"
        ).fetchall()
        scores_map = {
            r["student_id"]: dict(r)
            for r in conn.execute(
                "SELECT student_id, score, total, submitted_at FROM scores WHERE exam_id=?",
                (exam_id,)
            ).fetchall()
        }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = exam["title"][:31]

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["姓名", "学号", "班级", "得分", "满分", "提交时间"]
    col_widths = [12, 14, 20, 8, 8, 20]

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
        ws.cell(row=row_idx, column=4, value=sc["score"] if sc else "")
        ws.cell(row=row_idx, column=5, value=sc["total"] if sc else "")
        ws.cell(row=row_idx, column=6, value=sc["submitted_at"] if sc else "")
        if not sc:
            for col in range(1, 7):
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
    """构建全班「学生 × 任务」二维完成状态矩阵 + 各任务完成率。

    参数：
    - semester: 可选学期筛选，如 "2024-2025-2"
    """
    where_clause = ""
    params = []
    if semester:
        where_clause = " WHERE semester = ?"
        params.append(semester)

    with db() as conn:
        students = conn.execute(
            "SELECT student_id, name, class_name FROM students ORDER BY name"
        ).fetchall()
        exams = conn.execute(
            f"SELECT id, title, is_active, deadline, published_at, semester FROM exams{where_clause} ORDER BY published_at, id"
            if where_clause else
            f"SELECT id, title, is_active, deadline, published_at, semester FROM exams ORDER BY published_at, id",
            params
        ).fetchall()

        # 一次查询获取所有提交记录
        scores_rows = conn.execute(
            "SELECT student_id, exam_id, score, total, submitted_at FROM scores"
        ).fetchall()

    # 构建快速查找: (student_id, exam_id) → submitted_at
    score_map: dict = {}
    for row in scores_rows:
        score_map[(row["student_id"], row["exam_id"])] = {
            "score": row["score"],
            "total": row["total"],
            "submitted_at": row["submitted_at"],
        }

    student_list = []
    for s in students:
        statuses = {}
        submitted_count = 0
        active_exam_count = 0
        for e in exams:
            key = (s["student_id"], e["id"])
            if not e["is_active"]:
                statuses[e["id"]] = {"status": "not_published"}
                continue
            active_exam_count += 1
            if key in score_map:
                sub_at = score_map[key]["submitted_at"]
                # 判断是否迟交
                if e["deadline"] and sub_at:
                    try:
                        dl = datetime.fromisoformat(e["deadline"])
                        actual = datetime.fromisoformat(sub_at)
                        is_late = actual > dl
                    except (ValueError, TypeError):
                        is_late = False
                else:
                    is_late = False
                statuses[e["id"]] = {
                    "status": "late" if is_late else "submitted",
                    "score": score_map[key]["score"],
                    "total": score_map[key]["total"],
                    "submitted_at": sub_at,
                }
                submitted_count += 1
            else:
                statuses[e["id"]] = {"status": "unsubmitted"}
        completion_rate = round(submitted_count / active_exam_count, 3) if active_exam_count > 0 else 0.0
        student_list.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "class_name": s["class_name"],
            "completion_rate": completion_rate,
            "statuses": statuses,
        })

    exam_list = []
    total_students = len(students)
    for e in exams:
        if not e["is_active"]:
            exam_list.append({
                "id": e["id"], "title": e["title"], "is_active": False,
                "published_at": e["published_at"], "deadline": e["deadline"],
                "semester": e["semester"] or "",
                "total_students": total_students, "submitted": 0,
                "completion_rate": 0.0,
            })
            continue
        submitted = sum(
            1 for s in students
            if (s["student_id"], e["id"]) in score_map
        )
        exam_list.append({
            "id": e["id"], "title": e["title"], "is_active": True,
            "published_at": e["published_at"], "deadline": e["deadline"],
            "semester": e["semester"] or "",
            "total_students": total_students,
            "submitted": submitted,
            "completion_rate": round(submitted / total_students, 3) if total_students > 0 else 0.0,
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
                "SELECT COUNT(*) FROM students WHERE class_name LIKE ?",
                (f"%{course}%",)
            ).fetchone()[0]
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
