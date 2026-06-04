import os
import io
import chardet
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token, verify_teacher_token
from app.sync_exams import sync_exams
from pypinyin import lazy_pinyin, Style
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import json
import re

router = APIRouter()

TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_teacher_token(token)
        return payload
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
        exams = conn.execute("SELECT id, title, is_active FROM exams ORDER BY id").fetchall()

    # 懒加载同步：若数据库中还没有考试记录，尝试立即扫描文档目录
    if not exams:
        print("[list_exams] 考试表为空，触发懒加载同步…")
        sync_exams()
        with db() as conn:
            exams = conn.execute("SELECT id, title, is_active FROM exams ORDER BY id").fetchall()

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
                "submitted": submitted, "total_students": total_students,
                "avg_score": round(avg, 1) if avg else None,
            })
    return result


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
    is_active: int


@router.put("/api/teacher/exams/{exam_id}")
def update_exam(exam_id: str, req: ExamUpdate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        conn.execute("UPDATE exams SET is_active=? WHERE id=?", (req.is_active, exam_id))
    return {"ok": True}


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


class GradeExportRequest(BaseModel):
    class_name: Optional[str] = None
    course_name: Optional[str] = None
    term: Optional[str] = None
    weights: Optional[dict] = None
    rows: Optional[list] = None


DEFAULT_WEIGHTS = {"attendance": 0.15, "exam": 0.30, "code": 0.35, "pr": 0.20}


def _resolve_weights(weights: Optional[dict]) -> dict:
    if not weights:
        return dict(DEFAULT_WEIGHTS)
    result = dict(DEFAULT_WEIGHTS)
    result.update(weights)
    return result


def _compute_total(row: dict, weights: dict) -> float:
    if not weights:
        return None
    total = 0.0
    for k, w in weights.items():
        try:
            v = float(row.get(k, 0) or 0)
        except Exception:
            v = 0
        total += v * float(w)
    return round(total, 2)


def _grade_letter(score: float) -> str:
    if score is None:
        return ""
    try:
        s = float(score)
    except Exception:
        return ""
    if s >= 90:
        return "A"
    if s >= 80:
        return "B"
    if s >= 70:
        return "C"
    if s >= 60:
        return "D"
    return "F"


@router.get("/api/teacher/grades/filters")
def grade_filters(authorization: Optional[str] = Header(None)):
    """返回筛选下拉框的可选值：班级、课程(考试)、学期列表"""
    _require_teacher(authorization)
    with db() as conn:
        classes = [
            r["class_name"] for r in conn.execute(
                "SELECT DISTINCT class_name FROM students WHERE class_name!='' ORDER BY class_name"
            ).fetchall()
        ]
        courses = [
            {"id": r["id"], "title": r["title"]}
            for r in conn.execute("SELECT id, title FROM exams ORDER BY id").fetchall()
        ]
        # extract terms from exam titles (format: "xxx（20xx春/秋）")
        _term_set = set()
        for r in conn.execute("SELECT title FROM exams").fetchall():
            m = re.search(r'（(20\d{2}[春秋])）', r['title'])
            if m:
                _term_set.add(m.group(1))
        terms = sorted(_term_set)
    return {"classes": classes, "courses": courses, "terms": terms}


@router.get("/api/teacher/grades/audit-logs")
def grade_audit_logs(authorization: Optional[str] = Header(None)):
    """返回导出审计日志"""
    _require_teacher(authorization)
    with db() as conn:
        logs = conn.execute(
            "SELECT id, actor, filters, record_count, created_at FROM export_logs ORDER BY id DESC LIMIT 200"
        ).fetchall()
    return {"logs": [dict(r) for r in logs]}


@router.post("/api/teacher/grades/preview")
def preview_grades(req: GradeExportRequest, authorization: Optional[str] = Header(None)):
    """按筛选返回预览数据（可用于前端预览与手动修正）。
    前端可在返回数据上修改个别单元格，然后将最终 rows 发回 /export 接口生成文件。
    """
    _require_teacher(authorization)

    with db() as conn:
        if req.class_name:
            students = conn.execute(
                "SELECT name, student_id, class_name FROM students WHERE class_name=? ORDER BY student_id",
                (req.class_name,)
            ).fetchall()
        else:
            students = conn.execute(
                "SELECT name, student_id, class_name FROM students ORDER BY student_id"
            ).fetchall()

        # try to find an exam matching course_name to fill '考试得分'
        exam_scores = {}
        if req.course_name:
            # match by title (exact) or by id
            exam_row = conn.execute("SELECT id FROM exams WHERE title=?", (req.course_name,)).fetchone()
            if not exam_row:
                exam_row = conn.execute("SELECT id FROM exams WHERE id=?", (req.course_name,)).fetchone()
            if exam_row:
                eid = exam_row["id"]
                for r in conn.execute("SELECT student_id, score FROM scores WHERE exam_id=?", (eid,)).fetchall():
                    exam_scores[r["student_id"]] = r["score"]

    # build rows
    result_rows = []
    provided_rows_map = {}
    if req.rows:
        for r in req.rows:
            if r.get("student_id"):
                provided_rows_map[str(r.get("student_id"))] = r

    for s in students:
        sid = s["student_id"]
        base = {
            "student_id": sid,
            "name": s["name"],
            "class_name": s["class_name"],
            "course_name": req.course_name or "",
            "attendance": None,
            "exam": exam_scores.get(sid),
            "code": None,
            "pr": None,
            "total": None,
            "grade": "",
            "remark": "",
        }
        if sid in provided_rows_map:
            base.update(provided_rows_map[sid])

        # compute total with resolved weights
        resolved = _resolve_weights(req.weights)
        base_total = _compute_total(base, resolved)
        base["total"] = base_total
        base["grade"] = _grade_letter(base_total)

        result_rows.append(base)

    return {"rows": result_rows}


@router.post("/api/teacher/grades/export")
def export_grades(req: GradeExportRequest, authorization: Optional[str] = Header(None)):
    """生成并下载最终的成绩单 Excel，同时写入审计日志。前端应传入最终确认的 `rows`（包含手动修正后的值）。"""
    payload = _require_teacher(authorization)
    actor = payload.get("name") if isinstance(payload, dict) else "teacher"

    rows = req.rows or []
    resolved_weights = _resolve_weights(req.weights)
    for r in rows:
        r["total"] = _compute_total(r, resolved_weights)
        r["grade"] = _grade_letter(r.get("total"))

    # create excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (req.course_name or "成绩")[:31]

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["学号", "姓名", "班级", "课程名称", "出勤得分", "考试得分", "代码提交得分", "PR贡献得分", "总评成绩", "等级", "备注"]
    widths = [14, 12, 20, 20, 10, 10, 10, 10, 10, 8, 20]

    for col, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = w

    for i, r in enumerate(rows, 2):
        ws.cell(row=i, column=1, value=r.get("student_id"))
        ws.cell(row=i, column=2, value=r.get("name"))
        ws.cell(row=i, column=3, value=r.get("class_name"))
        ws.cell(row=i, column=4, value=r.get("course_name"))
        ws.cell(row=i, column=5, value=r.get("attendance"))
        ws.cell(row=i, column=6, value=r.get("exam"))
        ws.cell(row=i, column=7, value=r.get("code"))
        ws.cell(row=i, column=8, value=r.get("pr"))
        ws.cell(row=i, column=9, value=r.get("total"))
        ws.cell(row=i, column=10, value=r.get("grade"))
        ws.cell(row=i, column=11, value=r.get("remark"))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    # write audit log
    filters = {"class_name": req.class_name, "course_name": req.course_name, "term": req.term}
    with db() as conn:
        conn.execute(
            "INSERT INTO export_logs (actor, filters, record_count) VALUES (?,?,?)",
            (actor or "teacher", json.dumps(filters, ensure_ascii=False), len(rows))
        )

    from urllib.parse import quote
    date_str = datetime.now().strftime("%Y%m%d")
    safe_course = (req.course_name or "课程").replace("/", "-")
    safe_class = (req.class_name or "全班").replace("/", "-")
    safe_term = (req.term or "").replace("/", "-")
    filename = f"{safe_course}_{safe_class}_{safe_term}_成绩单_{date_str}.xlsx"
    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
