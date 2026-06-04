import os
import io
import chardet
from datetime import datetime
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token, hash_password, verify_teacher_token, require_teacher
from app.sync_exams import sync_exams
from pypinyin import lazy_pinyin, Style
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

router = APIRouter()

TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
COURSE_ID = int(os.environ.get("COURSE_ID", "2"))


def _list_students_with_class(conn):
    """返回当前课程的全部学生（含 user_id、name、student_id、class_name）"""
    rows = conn.execute("""
        SELECT u.id AS user_id, u.full_name AS name, u.student_no AS student_id,
               COALESCE(s.class_name, '') AS class_name
        FROM enrollments e
        JOIN users u ON u.id = e.student_user_id
        LEFT JOIN students s ON s.user_id = u.id
        WHERE e.course_id = %s AND u.role = 'student'
        ORDER BY u.student_no
    """, (COURSE_ID,)).fetchall()
    return rows


def _get_enrolled_student_count(conn):
    """返回当前课程的选课人数"""
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
        (COURSE_ID,),
    ).fetchone()
    return row["cnt"] if row else 0


def _name_to_pinyin(name: str):
    full = "".join(lazy_pinyin(name, style=Style.NORMAL))
    abbr = "".join(lazy_pinyin(name, style=Style.FIRST_LETTER))
    return full.lower(), abbr.lower()


class LoginRequest(BaseModel):
    password: str

@router.post("/api/teacher/students")
async def upload_students(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """上传学生名单 CSV，同步到远程 users/students/enrollments 表"""
    require_teacher(authorization)

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
        
        count = 0
        for name, student_no, class_name in records:
            email = f"{student_no}@stu.oaepp.dev"
            # 插入或更新 users 表
            conn.execute("""
                INSERT INTO users (role, student_no, email, password_hash, full_name)
                VALUES ('student', %s, %s, '', %s)
                ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)
            """, (student_no, email, name))
            user_id = conn.lastrowid
            if not user_id:
                conn.execute("SELECT id FROM users WHERE student_no = %s", (student_no,))
                user_id = conn.fetchone()["id"]

            # 插入或更新 students 表
            conn.execute("""
                INSERT INTO students (user_id, class_name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE class_name = VALUES(class_name)
            """, (user_id, class_name))

            # 选课
            conn.execute("""
                INSERT IGNORE INTO enrollments (course_id, student_user_id)
                VALUES (%s, %s)
            """, (COURSE_ID, user_id))
            count += 1

    return {"count": count}


class AddStudentRequest(BaseModel):
    name: str
    student_id: str
    class_name: str = ""


@router.post("/api/teacher/students/add")
def add_student(req: AddStudentRequest, authorization: Optional[str] = Header(None)):
    """添加单个学生"""
    require_teacher(authorization)
    req.name = req.name.strip()
    req.student_id = req.student_id.strip()
    if not req.name or not req.student_id:
        raise HTTPException(status_code=422, detail="姓名和学号不能为空")

    with db() as conn:
        
        # 检查是否已存在
        conn.execute(
            "SELECT u.full_name FROM users u WHERE u.student_no = %s",
            (req.student_id,)
        )
        existing = conn.fetchone()
        if existing:
            raise HTTPException(status_code=409,
                                detail=f"学号 {req.student_id} 已存在（{existing['full_name']}）")

        email = f"{req.student_id}@stu.oaepp.dev"
        conn.execute(
            "INSERT INTO users (role, student_no, email, password_hash, full_name) VALUES ('student', %s, %s, '', %s)",
            (req.student_id, email, req.name)
        )
        user_id = conn.lastrowid

        conn.execute(
            "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
            (user_id, req.class_name.strip())
        )
        conn.execute(
            "INSERT IGNORE INTO enrollments (course_id, student_user_id) VALUES (%s, %s)",
            (COURSE_ID, user_id)
        )
        conn.execute(
            "INSERT INTO student_accounts (student_id, password_hash) VALUES (%s, %s)",
            (req.student_id, hash_password(req.student_id)),
        )
    return {"ok": True}


@router.delete("/api/teacher/students/{student_id}")
def delete_student(student_id: str, authorization: Optional[str] = Header(None)):
    """删除单个学生（取消选课，保留用户记录）"""
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute(
            "SELECT u.id, u.full_name FROM users u WHERE u.student_no = %s AND u.role = 'student'",
            (student_id,)
        )
        student = conn.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        # 取消选课
        conn.execute(
            "DELETE FROM enrollments WHERE course_id = %s AND student_user_id = %s",
            (COURSE_ID, student["id"])
        )
    return {"ok": True, "deleted": student["full_name"]}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    """清空当前课程全部选课"""
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
            (COURSE_ID,)
        )
        count = conn.fetchone()["cnt"]
        conn.execute("DELETE FROM enrollments WHERE course_id = %s", (COURSE_ID,))
    return {"ok": True, "deleted_count": count}


@router.post("/api/teacher/reset")
def new_semester_reset(authorization: Optional[str] = Header(None)):
    """新学期重置：清空当前课程选课"""
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
            (COURSE_ID,)
        )
        students = conn.fetchone()["cnt"]
        conn.execute("DELETE FROM enrollments WHERE course_id = %s", (COURSE_ID,))
    return {"ok": True, "deleted_students": students, "deleted_scores": 0}


@router.get("/api/teacher/students/list")
def list_students(authorization: Optional[str] = Header(None)):
    """获取全部学生名单"""
    require_teacher(authorization)
    with db() as conn:
        rows = _list_students_with_class(conn)
    return [{"name": r["name"], "student_id": r["student_id"], "class_name": r["class_name"]} for r in rows]


@router.get("/api/teacher/exams")
def list_exams(authorization: Optional[str] = Header(None)):
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute("""
            SELECT id, title, exam_type, start_at, end_at
            FROM exams WHERE course_id = %s ORDER BY id
        """, (COURSE_ID,))
        exams = conn.fetchall()

    # 懒加载同步
    if not exams:
        print("[list_exams] 考试表为空，触发懒加载同步…")
        sync_exams()
        with db() as conn:
            
            conn.execute("""
                SELECT id, title, exam_type, start_at, end_at
                FROM exams WHERE course_id = %s ORDER BY id
            """, (COURSE_ID,))
            exams = conn.fetchall()

    with db() as conn:
        
        total_students = _get_enrolled_student_count(conn)
        result = []
        from datetime import datetime
        for e in exams:
            submitted = conn.execute(
                "SELECT COUNT(*) FROM scores WHERE exam_id=%s", (e["id"],)
            ).fetchone()[0]
            avg = conn.execute(
                "SELECT AVG(score) FROM scores WHERE exam_id=%s", (e["id"],)
            ).fetchone()[0]
            # 尝试根据 classroom_exams 的时间判断状态（开放中 / 已关闭）
            ce = conn.execute("SELECT start_at, end_at FROM classroom_exams WHERE id=%s", (e["id"],)).fetchone()
            status = None
            if ce:
                try:
                    now = datetime.now()
                    start = datetime.strptime(ce["start_at"], "%Y-%m-%d %H:%M:%S")
                    end = datetime.strptime(ce["end_at"], "%Y-%m-%d %H:%M:%S")
                    status = "active" if (now >= start and now <= end) else "ended"
                except Exception:
                    status = "unknown"
            else:
                # 继续使用 is_active 字段作为回退
                status = "active" if e["is_active"] == 1 else "ended"
            result.append({
                "id": str(e["id"]), "title": e["title"], "is_active": 1,
                "exam_type": e["exam_type"],
                "start_at": e["start_at"].strftime("%Y-%m-%d %H:%M:%S") if e["start_at"] else None,
                "end_at": e["end_at"].strftime("%Y-%m-%d %H:%M:%S") if e["end_at"] else None,
                "submitted": submitted, "total_students": total_students,
                "avg_score": round(avg, 1) if avg else None,
                "status": status,
            })
    return result


class ExamCreate(BaseModel):
    title: str
    exam_type: str = "quiz"
    start_at: str
    end_at: str


@router.post("/api/teacher/exams")
def create_exam(req: ExamCreate, authorization: Optional[str] = Header(None)):
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute("""
            INSERT INTO exams (course_id, title, exam_type, start_at, end_at, created_by)
            VALUES (%s, %s, 'quiz', NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), 14)
        """, (COURSE_ID, req.title))
    return {"ok": True}


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    exam_type: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None


class CleanupRequest(BaseModel):
    titles: Optional[list[str]] = None


@router.put("/api/teacher/exams/{exam_id}")
def update_exam(exam_id: str, req: ExamUpdate, authorization: Optional[str] = Header(None)):
    require_teacher(authorization)
    with db() as conn:
        
        if req.is_active == 0:
            conn.execute("UPDATE exams SET end_at = NOW() WHERE id = %s", (exam_id,))
        else:
            conn.execute(
                "UPDATE exams SET end_at = DATE_ADD(NOW(), INTERVAL 7 DAY) WHERE id = %s",
                (exam_id,)
            )
    return {"ok": True}


@router.get("/api/teacher/scores")
def get_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """获取某次考试的所有学生成绩"""
    require_teacher(authorization)
    with db() as conn:
        
        conn.execute("SELECT title FROM exams WHERE id = %s", (exam_id,))
        exam = conn.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = _list_students_with_class(conn)

        # 获取成绩（通过 assignment.title 关联 exam_id）
        conn.execute("""
            SELECT sub.student_user_id, gr.exam_score AS score, gr.total_score AS total, gr.graded_at AS submitted_at
            FROM grading_records gr
            JOIN submissions sub ON gr.submission_id = sub.id
            JOIN assignments a ON sub.assignment_id = a.id
            WHERE a.title LIKE CONCAT('exam_', %s, '%%')
        """, (exam_id,))
        scores_map = {r["student_user_id"]: r for r in conn.fetchall()}

    result = []
    for s in students:
        sc = scores_map.get(s["user_id"])
        result.append({
            "name": s["name"],
            "student_id": s["student_id"],
            "class_name": s["class_name"],
            "score": float(sc["score"]) if sc else None,
            "total": float(sc["total"]) if sc else None,
            "submitted_at": sc["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if sc and sc["submitted_at"] else None,
        })

    return {"exam_title": exam["title"], "rows": result}


@router.get("/api/teacher/scores/export")
def export_scores(exam_id: int = Query(...), authorization: Optional[str] = Header(None)):
    """导出成绩 Excel"""
    require_teacher(authorization)

    with db() as conn:
        
        conn.execute("SELECT title FROM exams WHERE id = %s", (exam_id,))
        exam = conn.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = _list_students_with_class(conn)

        conn.execute("""
            SELECT sub.student_user_id, gr.exam_score AS score, gr.total_score AS total, gr.graded_at AS submitted_at
            FROM grading_records gr
            JOIN submissions sub ON gr.submission_id = sub.id
            JOIN assignments a ON sub.assignment_id = a.id
            WHERE a.title LIKE CONCAT('exam_', %s, '%%')
        """, (exam_id,))
        scores_map = {r["student_user_id"]: r for r in conn.fetchall()}

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
        sc = scores_map.get(s["user_id"])
        ws.cell(row=row_idx, column=1, value=s["name"])
        ws.cell(row=row_idx, column=2, value=s["student_id"])
        ws.cell(row=row_idx, column=3, value=s["class_name"])
        ws.cell(row=row_idx, column=4, value=float(sc["score"]) if sc else "")
        ws.cell(row=row_idx, column=5, value=float(sc["total"]) if sc else "")
        ws.cell(row=row_idx, column=6,
                value=sc["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if sc and sc["submitted_at"] else "")
        if not sc:
            for col in range(1, 7):
                ws.cell(row=row_idx, column=col).font = Font(color="999999")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"成绩单_{exam['title']}_{date_str}.xlsx"
    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


@router.post("/api/teacher/exams/cleanup")
def cleanup_exams(req: CleanupRequest, authorization: Optional[str] = Header(None)):
    """删除指定标题的考试（慎用）。若未提供 titles，则删除已知的三条错误记录。"""
    require_teacher(authorization)
    defaults = [
        "第 12 章 机器人系统开发环境配置 测验",
        "第二章 CubeMX 编程测验",
        "第三章 PicSimlab 仿真开发测验",
    ]
    titles = req.titles or defaults
    affected = 0
    with db() as conn:
        for t in titles:
            # remove from exams
            cur = conn.execute("DELETE FROM exams WHERE title=%s", (t,))
            affected += cur.rowcount
            # remove classroom exams and related records
            rows = conn.execute("SELECT id FROM classroom_exams WHERE title=%s", (t,)).fetchall()
            for r in rows:
                eid = r["id"]
                conn.execute("DELETE FROM classroom_exam_questions WHERE exam_id=%s", (eid,))
                conn.execute("DELETE FROM classroom_exam_attempts WHERE exam_id=%s", (eid,))
                conn.execute("DELETE FROM classroom_exams WHERE id=%s", (eid,))
                affected += 1
    return {"ok": True, "affected": affected}


@router.delete("/api/teacher/exams/{exam_id}")
def delete_exam(exam_id: str, authorization: Optional[str] = Header(None)):
    """删除某次考试及其相关记录（scores、classroom_exams、questions、attempts）。"""
    require_teacher(authorization)
    affected = 0
    with db() as conn:
        # remove scores
        cur = conn.execute("DELETE FROM scores WHERE exam_id=%s", (exam_id,))
        affected += cur.rowcount
        # remove exam entry
        cur2 = conn.execute("DELETE FROM exams WHERE id=%s", (exam_id,))
        affected += cur2.rowcount
        # remove classroom exam related records if any
        rows = conn.execute("SELECT id FROM classroom_exams WHERE id=%s", (exam_id,)).fetchall()
        for r in rows:
            eid = r["id"]
            conn.execute("DELETE FROM classroom_exam_questions WHERE exam_id=%s", (eid,))
            conn.execute("DELETE FROM classroom_exam_attempts WHERE exam_id=%s", (eid,))
            conn.execute("DELETE FROM classroom_exams WHERE id=%s", (eid,))
            affected += 1
    return {"ok": True, "deleted": affected}
