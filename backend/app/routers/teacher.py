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
    _require_teacher(authorization)

    raw = await file.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    text = raw.decode(encoding, errors="replace")

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(status_code=422, detail="文件为空")

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
        records.append((name, student_id, class_name))

    if not records:
        raise HTTPException(status_code=422, detail="CSV 中没有有效数据行")

    with db() as conn:
        for name, student_id, class_name in records:
            conn.execute(
                "INSERT INTO users (role, student_no, email, password_hash, full_name, is_active) "
                "VALUES ('student', %s, %s, '', %s, 1) "
                "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)",
                (student_id, f"{student_id}@placeholder.local", name)
            )
            conn.execute(
                "INSERT INTO students (user_id, class_name) "
                "VALUES ((SELECT id FROM users WHERE student_no = %s), %s) "
                "ON DUPLICATE KEY UPDATE class_name = VALUES(class_name)",
                (student_id, class_name)
            )

    return {"count": len(records)}


class AddStudentRequest(BaseModel):
    name: str
    student_id: str
    class_name: str = ""


@router.post("/api/teacher/students/add")
def add_student(req: AddStudentRequest, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    req.name = req.name.strip()
    req.student_id = req.student_id.strip()
    if not req.name or not req.student_id:
        raise HTTPException(status_code=422, detail="姓名和学号不能为空")
    with db() as conn:
        conn.execute(
            "INSERT INTO users (role, student_no, email, password_hash, full_name, is_active) "
            "VALUES ('student', %s, %s, '', %s, 1) "
            "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)",
            (req.student_id, f"{req.student_id}@placeholder.local", req.name)
        )
        conn.execute(
            "INSERT INTO students (user_id, class_name) "
            "VALUES ((SELECT id FROM users WHERE student_no = %s), %s) "
            "ON DUPLICATE KEY UPDATE class_name = VALUES(class_name)",
            (req.student_id, req.class_name.strip())
        )
    return {"ok": True}


@router.delete("/api/teacher/students/{student_id}")
def delete_student(student_id: str, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        student = conn.execute(
            "SELECT u.full_name AS name FROM users u WHERE u.student_no = %s AND u.role = 'student'",
            (student_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")
        conn.execute(
            "DELETE FROM exam_answers WHERE attempt_id IN "
            "(SELECT id FROM exam_attempts WHERE student_user_id = "
            "(SELECT id FROM users WHERE student_no = %s))",
            (student_id,)
        )
        conn.execute(
            "DELETE FROM exam_attempts WHERE student_user_id = "
            "(SELECT id FROM users WHERE student_no = %s)",
            (student_id,)
        )
        conn.execute(
            "DELETE FROM students WHERE user_id = "
            "(SELECT id FROM users WHERE student_no = %s)",
            (student_id,)
        )
        conn.execute("DELETE FROM users WHERE student_no = %s AND role = 'student'", (student_id,))
    return {"ok": True, "deleted": student["name"]}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        students_cnt = conn.execute(
            "SELECT COUNT(*) AS cnt FROM users WHERE role = 'student'"
        ).fetchone()["cnt"]
        conn.execute("DELETE FROM exam_answers")
        conn.execute("DELETE FROM exam_attempts")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM enrollments")
        conn.execute("DELETE FROM users WHERE role = 'student'")
    return {"ok": True, "deleted_count": students_cnt}


@router.post("/api/teacher/reset")
def new_semester_reset(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        students = conn.execute(
            "SELECT COUNT(*) AS cnt FROM users WHERE role = 'student'"
        ).fetchone()["cnt"]
        conn.execute("DELETE FROM exam_answers")
        conn.execute("DELETE FROM exam_attempts")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM enrollments")
        conn.execute("DELETE FROM users WHERE role = 'student'")
    return {"ok": True, "deleted_students": students}


@router.get("/api/teacher/students/list")
def list_students(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT u.full_name AS name, u.student_no AS student_id, s.class_name "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.role = 'student' "
            "ORDER BY s.class_name, u.full_name"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/teacher/exams")
def list_exams(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exams = conn.execute(
            "SELECT id, title, "
            "CASE WHEN end_at IS NULL OR end_at > NOW() THEN 1 ELSE 0 END AS is_active "
            "FROM exams ORDER BY id"
        ).fetchall()

    if not exams:
        print("[list_exams] 考试表为空，触发懒加载同步…")
        sync_exams()
        with db() as conn:
            exams = conn.execute(
                "SELECT id, title, "
                "CASE WHEN end_at IS NULL OR end_at > NOW() THEN 1 ELSE 0 END AS is_active "
                "FROM exams ORDER BY id"
            ).fetchall()

    with db() as conn:
        total_students = conn.execute(
            "SELECT COUNT(*) AS cnt FROM users WHERE role = 'student'"
        ).fetchone()["cnt"]
        result = []
        for e in exams:
            submitted = conn.execute(
                "SELECT COUNT(*) AS cnt FROM exam_attempts "
                "WHERE exam_id = %s AND status IN ('submitted', 'graded')",
                (e["id"],)
            ).fetchone()["cnt"]
            avg = conn.execute(
                "SELECT AVG(total_score) AS avg_score FROM exam_attempts "
                "WHERE exam_id = %s AND status IN ('submitted', 'graded')",
                (e["id"],)
            ).fetchone()["avg_score"]
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
            "INSERT INTO exams (title, exam_type, course_id, start_at, end_at, created_by) "
            "VALUES (%s, 'quiz', 1, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), 1)",
            (req.title,)
        )
    return {"ok": True}


class ExamUpdate(BaseModel):
    is_active: int


@router.put("/api/teacher/exams/{exam_id}")
def update_exam(exam_id: str, req: ExamUpdate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        if req.is_active:
            conn.execute(
                "UPDATE exams SET end_at = DATE_ADD(NOW(), INTERVAL 30 DAY) "
                "WHERE id = CAST(%s AS UNSIGNED)",
                (exam_id,)
            )
        else:
            conn.execute(
                "UPDATE exams SET end_at = NOW() WHERE id = CAST(%s AS UNSIGNED)",
                (exam_id,)
            )
    return {"ok": True}


@router.get("/api/teacher/scores")
def get_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        exam = conn.execute(
            "SELECT title FROM exams WHERE id = CAST(%s AS UNSIGNED)",
            (exam_id,)
        ).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute(
            "SELECT u.full_name AS name, u.student_no AS student_id, s.class_name "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.role = 'student' ORDER BY u.student_no"
        ).fetchall()
        scores_map = {
            r["student_id"]: dict(r)
            for r in conn.execute(
                "SELECT u.student_no AS student_id, ea.total_score AS score, ea.submitted_at, "
                "(SELECT COALESCE(SUM(eq.score),0) FROM exam_questions eq "
                "WHERE eq.exam_id = ea.exam_id) AS total "
                "FROM exam_attempts ea "
                "JOIN users u ON ea.student_user_id = u.id "
                "WHERE ea.exam_id = CAST(%s AS UNSIGNED) "
                "AND ea.status IN ('submitted', 'graded')",
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
            "score": float(sc["score"]) if sc else None,
            "total": float(sc["total"]) if sc else None,
            "submitted_at": str(sc["submitted_at"]) if sc else None,
        })

    return {"exam_title": exam["title"], "rows": result}


@router.get("/api/teacher/scores/export")
def export_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)

    with db() as conn:
        exam = conn.execute(
            "SELECT title FROM exams WHERE id = CAST(%s AS UNSIGNED)",
            (exam_id,)
        ).fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = conn.execute(
            "SELECT u.full_name AS name, u.student_no AS student_id, s.class_name "
            "FROM users u JOIN students s ON u.id = s.user_id "
            "WHERE u.role = 'student' ORDER BY u.student_no"
        ).fetchall()
        scores_map = {
            r["student_id"]: dict(r)
            for r in conn.execute(
                "SELECT u.student_no AS student_id, ea.total_score AS score, ea.submitted_at, "
                "(SELECT COALESCE(SUM(eq.score),0) FROM exam_questions eq "
                "WHERE eq.exam_id = ea.exam_id) AS total "
                "FROM exam_attempts ea "
                "JOIN users u ON ea.student_user_id = u.id "
                "WHERE ea.exam_id = CAST(%s AS UNSIGNED) "
                "AND ea.status IN ('submitted', 'graded')",
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
