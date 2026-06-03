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
from app.auth_utils import create_token, require_teacher
        from datetime import datetime
        for e in exams:
            # 优先使用 upstream 的 grading_records/submissions 统计（更通用）；失败时回退到 scores 表（feature 分支）
            submitted = 0
            avg = None
            try:
                cur.execute("""
                    SELECT COUNT(DISTINCT sub.student_user_id) AS cnt
                    FROM grading_records gr
                    JOIN submissions sub ON gr.submission_id = sub.id
                    JOIN assignments a ON sub.assignment_id = a.id
                    WHERE a.course_id = %s AND a.title LIKE CONCAT('exam_', %s, '%%')
                """, (COURSE_ID, str(e["id"])))
                row = cur.fetchone()
                submitted = row["cnt"] or 0

                cur.execute("""
                    SELECT AVG(gr.exam_score) AS avg
                    FROM grading_records gr
                    JOIN submissions sub ON gr.submission_id = sub.id
                    JOIN assignments a ON sub.assignment_id = a.id
                    WHERE a.course_id = %s AND a.title LIKE CONCAT('exam_', %s, '%%')
                """, (COURSE_ID, str(e["id"])))
                avg_row = cur.fetchone()
                avg = avg_row["avg"]
            except Exception:
                # 回退到 legacy 的 scores 表
                try:
                    cur.execute("SELECT COUNT(*) AS cnt FROM scores WHERE exam_id = %s", (e["id"],))
                    submitted = cur.fetchone()["cnt"] or 0
                except Exception:
                    submitted = 0
                try:
                    cur.execute("SELECT AVG(score) AS avg FROM scores WHERE exam_id = %s", (e["id"],))
                    avg_row = cur.fetchone()
                    avg = avg_row["avg"]
                except Exception:
                    avg = None

            # 尝试根据 classroom_exams 的时间判断状态（开放中 / 已关闭），找不到则以 is_active 回退
            status = None
            try:
                cur.execute("SELECT start_at, end_at FROM classroom_exams WHERE id = %s", (e["id"],))
                ce = cur.fetchone()
                if ce and ce.get("start_at") and ce.get("end_at"):
                    try:
                        now = datetime.now()
                        start = datetime.strptime(str(ce["start_at"]), "%Y-%m-%d %H:%M:%S")
                        end = datetime.strptime(str(ce["end_at"]), "%Y-%m-%d %H:%M:%S")
                        status = "active" if (now >= start and now <= end) else "ended"
                    except Exception:
                        status = "unknown"
                else:
                    status = "active" if e.get("is_active", 1) == 1 else "ended"
            except Exception:
                status = "active" if e.get("is_active", 1) == 1 else "ended"

            result.append({
                "id": str(e["id"]),
                "title": e["title"],
                "is_active": 1,
                "exam_type": e["exam_type"],
                "start_at": e["start_at"].strftime("%Y-%m-%d %H:%M:%S") if e["start_at"] else None,
                "end_at": e["end_at"].strftime("%Y-%m-%d %H:%M:%S") if e["end_at"] else None,
                "submitted": submitted,
                "total_students": total_students,
                "avg_score": round(float(avg), 1) if avg else None,
                "status": status,
            })

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
        cur = conn.cursor()
        count = 0
        for name, student_no, class_name in records:
            email = f"{student_no}@stu.oaepp.dev"
            # 插入或更新 users 表
            cur.execute("""
                INSERT INTO users (role, student_no, email, password_hash, full_name)
                VALUES ('student', %s, %s, '', %s)
                ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)
            """, (student_no, email, name))
            user_id = cur.lastrowid
            if not user_id:
                cur.execute("SELECT id FROM users WHERE student_no = %s", (student_no,))
                user_id = cur.fetchone()["id"]

            # 插入或更新 students 表
            cur.execute("""
                INSERT INTO students (user_id, class_name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE class_name = VALUES(class_name)
            """, (user_id, class_name))

            # 选课
            cur.execute("""
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
        cur = conn.cursor()
        # 检查是否已存在
        cur.execute(
            "SELECT u.full_name FROM users u WHERE u.student_no = %s",
            (req.student_id,)
        )
        existing = cur.fetchone()
        if existing:
            raise HTTPException(status_code=409,
                                detail=f"学号 {req.student_id} 已存在（{existing['full_name']}）")

        email = f"{req.student_id}@stu.oaepp.dev"
        cur.execute(
            "INSERT INTO users (role, student_no, email, password_hash, full_name) VALUES ('student', %s, %s, '', %s)",
            (req.student_id, email, req.name)
        )
        user_id = cur.lastrowid

        cur.execute(
            "INSERT INTO students (user_id, class_name) VALUES (%s, %s)",
            (user_id, req.class_name.strip())
        )
        cur.execute(
            "INSERT IGNORE INTO enrollments (course_id, student_user_id) VALUES (%s, %s)",
            (COURSE_ID, user_id)
        )
    return {"ok": True}


@router.delete("/api/teacher/students/{student_id}")
def delete_student(student_id: str, authorization: Optional[str] = Header(None)):
    """删除单个学生（取消选课，保留用户记录）"""
    require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT u.id, u.full_name FROM users u WHERE u.student_no = %s AND u.role = 'student'",
            (student_id,)
        )
        student = cur.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学号不存在")

        # 取消选课
        cur.execute(
            "DELETE FROM enrollments WHERE course_id = %s AND student_user_id = %s",
            (COURSE_ID, student["id"])
        )
    return {"ok": True, "deleted": student["full_name"]}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    """清空当前课程全部选课"""
    require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
            (COURSE_ID,)
        )
        count = cur.fetchone()["cnt"]
        cur.execute("DELETE FROM enrollments WHERE course_id = %s", (COURSE_ID,))
    return {"ok": True, "deleted_count": count}


@router.post("/api/teacher/reset")
def new_semester_reset(authorization: Optional[str] = Header(None)):
    """新学期重置：清空当前课程选课"""
    require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
            (COURSE_ID,)
        )
        students = cur.fetchone()["cnt"]
        cur.execute("DELETE FROM enrollments WHERE course_id = %s", (COURSE_ID,))
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
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, exam_type, start_at, end_at
            FROM exams WHERE course_id = %s ORDER BY id
        """, (COURSE_ID,))
        exams = cur.fetchall()

    # 懒加载同步
    if not exams:
        print("[list_exams] 考试表为空，触发懒加载同步…")
        sync_exams()
        with db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, exam_type, start_at, end_at
                FROM exams WHERE course_id = %s ORDER BY id
            """, (COURSE_ID,))
            exams = cur.fetchall()

    with db() as conn:
        cur = conn.cursor()
        total_students = _get_enrolled_student_count(conn)
        result = []
        from datetime import datetime
        for e in exams:
            # 统计该考试已提交人数
            cur.execute("""
                SELECT COUNT(DISTINCT sub.student_user_id) AS cnt
                FROM grading_records gr
                JOIN submissions sub ON gr.submission_id = sub.id
                JOIN assignments a ON sub.assignment_id = a.id
                WHERE a.course_id = %s AND a.title LIKE CONCAT('exam_', %s, '%%')
            """, (COURSE_ID, str(e["id"])))
            submitted = cur.fetchone()["cnt"] or 0

            # 统计该考试平均分
            cur.execute("""
                SELECT AVG(gr.exam_score) AS avg
                FROM grading_records gr
                JOIN submissions sub ON gr.submission_id = sub.id
                JOIN assignments a ON sub.assignment_id = a.id
                WHERE a.course_id = %s AND a.title LIKE CONCAT('exam_', %s, '%%')
            """, (COURSE_ID, str(e["id"])))
            avg_row = cur.fetchone()
            avg = avg_row["avg"]

            result.append({
                "id": str(e["id"]), "title": e["title"], "is_active": 1,
                "exam_type": e["exam_type"],
                "start_at": e["start_at"].strftime("%Y-%m-%d %H:%M:%S") if e["start_at"] else None,
                "end_at": e["end_at"].strftime("%Y-%m-%d %H:%M:%S") if e["end_at"] else None,
                "submitted": submitted, "total_students": total_students,
                "avg_score": round(float(avg), 1) if avg else None,
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
        cur = conn.cursor()
        cur.execute("""
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
        cur = conn.cursor()
        if req.is_active == 0:
            cur.execute("UPDATE exams SET end_at = NOW() WHERE id = %s", (exam_id,))
        else:
            cur.execute(
                "UPDATE exams SET end_at = DATE_ADD(NOW(), INTERVAL 7 DAY) WHERE id = %s",
                (exam_id,)
            )
    return {"ok": True}


@router.get("/api/teacher/scores")
def get_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """获取某次考试的所有学生成绩"""
    require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT title FROM exams WHERE id = %s", (exam_id,))
        exam = cur.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = _list_students_with_class(conn)

        # 获取成绩（通过 assignment.title 关联 exam_id）
        cur.execute("""
            SELECT sub.student_user_id, gr.exam_score AS score, gr.total_score AS total, gr.graded_at AS submitted_at
            FROM grading_records gr
            JOIN submissions sub ON gr.submission_id = sub.id
            JOIN assignments a ON sub.assignment_id = a.id
            WHERE a.title LIKE CONCAT('exam_', %s, '%%')
        """, (exam_id,))
        scores_map = {r["student_user_id"]: r for r in cur.fetchall()}

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
        cur = conn.cursor()
        cur.execute("SELECT title FROM exams WHERE id = %s", (exam_id,))
        exam = cur.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        students = _list_students_with_class(conn)

        cur.execute("""
            SELECT sub.student_user_id, gr.exam_score AS score, gr.total_score AS total, gr.graded_at AS submitted_at
            FROM grading_records gr
            JOIN submissions sub ON gr.submission_id = sub.id
            JOIN assignments a ON sub.assignment_id = a.id
            WHERE a.title LIKE CONCAT('exam_', %s, '%%')
        """, (exam_id,))
        scores_map = {r["student_user_id"]: r for r in cur.fetchall()}

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
    _require_teacher(authorization)
    defaults = [
        "第 12 章 机器人系统开发环境配置 测验",
        "第二章 CubeMX 编程测验",
        "第三章 PicSimlab 仿真开发测验",
    ]
    titles = req.titles or defaults
    affected = 0
    with db() as conn:
        for t in titles:
            cur = conn.execute("DELETE FROM exams WHERE title=%s", (t,))
            affected += cur.rowcount
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
    _require_teacher(authorization)
    affected = 0
    with db() as conn:
        cur = conn.execute("DELETE FROM scores WHERE exam_id=%s", (exam_id,))
        affected += cur.rowcount
        cur2 = conn.execute("DELETE FROM exams WHERE id=%s", (exam_id,))
        affected += cur2.rowcount
        rows = conn.execute("SELECT id FROM classroom_exams WHERE id=%s", (exam_id,)).fetchall()
        for r in rows:
            eid = r["id"]
            conn.execute("DELETE FROM classroom_exam_questions WHERE exam_id=%s", (eid,))
            conn.execute("DELETE FROM classroom_exam_attempts WHERE exam_id=%s", (eid,))
            conn.execute("DELETE FROM classroom_exams WHERE id=%s", (eid,))
            affected += 1
    return {"ok": True, "deleted": affected}

# ───── GitHub 账号绑定状态看板 (F-T-004) ─────


@router.get("/api/teacher/github-bindings/summary")
def get_binding_summary(authorization: Optional[str] = Header(None)):
    """获取全班绑定状态汇总统计"""
    require_teacher(authorization)
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='student'"
        ).fetchone()[0]
        bound = conn.execute(
            "SELECT COUNT(*) FROM github_bindings WHERE verify_status='approved'"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM github_bindings WHERE verify_status='pending'"
        ).fetchone()[0]
        unbound = total - bound - pending
    return {"total": total, "bound": bound, "pending": pending, "unbound": max(unbound, 0)}


@router.get("/api/teacher/github-bindings/list")
def get_binding_list(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by_status: bool = Query(False),
    authorization: Optional[str] = Header(None)
):
    """获取全班学生 GitHub 绑定状态列表，支持筛选、搜索、排序"""
    require_teacher(authorization)

    with db() as conn:
        query = """
            SELECT u.full_name AS name, u.student_no AS student_id,
                   COALESCE(s.class_name, '') AS class_name,
                   COALESCE(g.github_username, '') AS github_username,
                   COALESCE(g.verify_status, 'unbound') AS binding_status,
                   COALESCE(g.github_name, '') AS github_name,
                   g.verified_at
            FROM users u
            LEFT JOIN students s ON s.user_id = u.id
            LEFT JOIN github_bindings g ON u.id = g.student_user_id
            WHERE u.role = 'student'
        """
        conditions = []
        params: list = []

        if status and status != "all":
            if status == "unbound":
                conditions.append("(g.verify_status IS NULL OR g.verify_status NOT IN ('approved','pending'))")
            else:
                conditions.append("g.verify_status = %s")
                params.append(status)

        if search:
            conditions.append(
                "(u.full_name LIKE %s OR u.student_no LIKE %s OR g.github_username LIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like])

        if conditions:
            query += " AND " + " AND ".join(conditions)

        if sort_by_status:
            query += """
                ORDER BY
                    CASE
                        WHEN g.verify_status IS NULL OR g.verify_status NOT IN ('approved','pending') THEN 0
                        WHEN g.verify_status = 'pending' THEN 1
                        WHEN g.verify_status = 'approved' THEN 2
                    END,
                    u.student_no
            """
        else:
            query += " ORDER BY u.student_no"

    with db() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


class BatchStudentIds(BaseModel):
    student_ids: list[str]


@router.post("/api/teacher/github-bindings/batch-approve")
def batch_approve_bindings(req: BatchStudentIds, authorization: Optional[str] = Header(None)):
    """一键批量通过待审核的绑定请求"""
    require_teacher(authorization)
    if not req.student_ids:
        raise HTTPException(status_code=422, detail="请选择至少一名学生")
    placeholders = ",".join(["%s"] * len(req.student_ids))
    with db() as conn:
        conn.execute(
            f"UPDATE github_bindings g JOIN users u ON g.student_user_id=u.id "
            f"SET g.verify_status='approved', g.verified_at=NOW() "
            f"WHERE u.student_no IN ({placeholders}) AND g.verify_status='pending'",
            req.student_ids
        )
    return {"ok": True, "approved": conn.rowcount}


@router.post("/api/teacher/github-bindings/reject")
def reject_binding(req: BatchStudentIds, authorization: Optional[str] = Header(None)):
    """拒绝绑定申请"""
    require_teacher(authorization)
    if not req.student_ids:
        raise HTTPException(status_code=422, detail="请选择至少一名学生")
    placeholders = ",".join(["%s"] * len(req.student_ids))
    with db() as conn:
        conn.execute(
            f"UPDATE github_bindings g JOIN users u ON g.student_user_id=u.id "
            f"SET g.verify_status='rejected', g.github_username='', g.github_name='', g.verified_at=NULL "
            f"WHERE u.student_no IN ({placeholders})",
            req.student_ids
        )
    return {"ok": True}


@router.post("/api/teacher/github-bindings/send-reminder")
def send_binding_reminder(req: BatchStudentIds, authorization: Optional[str] = Header(None)):
    """向未绑定学生批量发送提醒"""
    require_teacher(authorization)
    if not req.student_ids:
        raise HTTPException(status_code=422, detail="请选择至少一名学生")
    placeholders = ",".join(["%s"] * len(req.student_ids))
    with db() as conn:
        rows = conn.execute(
            f"SELECT u.full_name AS name FROM users u "
            f"LEFT JOIN github_bindings g ON g.student_user_id=u.id "
            f"WHERE u.student_no IN ({placeholders}) "
            f"AND u.role='student' "
            f"AND (g.verify_status IS NULL OR g.verify_status NOT IN ('approved','pending'))",
            req.student_ids
        ).fetchall()
    names = [r["name"] for r in rows]
    return {"ok": True, "reminded": len(names), "students": names}


# ───── 进度看板 API (F-T-013) ─────

# 热力图状态常量
HEATMAP_STATUS = {
    "submitted": "绿",      # 已提交
    "late": "黄",          # 迟交
    "missing": "红",        # 未提交
    "not_published": "灰"  # 任务未发布
}


class ProgressFilter(BaseModel):
    """进度看板筛选参数"""
    course_id: Optional[int] = None
    semester: Optional[str] = None
    top_n_lowest: Optional[int] = 5  # 完成率最低的前N名置顶高亮


@router.get("/api/teacher/progress/heatmap")
def get_progress_heatmap(
    course_id: Optional[int] = Query(None),
    semester: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    获取热力图数据：学生（行）× 任务（列）二维完成状态矩阵
    
    返回格式：
    {
        "students": [{"id": 1, "name": "张三", "student_id": "2021001", "class_name": "计算机1班"}, ...],
        "assignments": [{"id": 1, "title": "第一章作业", "deadline": "2026-06-10"}, ...],
        "matrix": [
            [{"assignment_id": 1, "student_id": 1, "status": "submitted"}, ...],
            ...
        ]
    }
    """
    require_teacher(authorization)
    
    with db() as conn:
        # 查询学生列表
        student_query = """
            SELECT s.user_id AS student_id, u.full_name AS name, 
                   u.student_no, COALESCE(s.class_name, '') AS class_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE u.role = 'student'
        """
        students = conn.execute(student_query).fetchall()
        
        # 查询作业列表
        assignment_query = """
            SELECT a.id, a.title, a.deadline, a.created_at, a.course_id,
                   c.name AS course_name
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
        """
        params = []
        if course_id:
            assignment_query += " WHERE a.course_id = %s"
            params.append(course_id)
        if semester:
            assignment_query += " AND c.term = %s" if course_id else " WHERE c.term = %s"
            params.append(semester)
        assignment_query += " ORDER BY a.deadline"
        
        assignments = conn.execute(assignment_query, params).fetchall()
        
        if not assignments:
            return {"students": [], "assignments": [], "matrix": []}
        
        # 查询提交状态
        assignment_ids = [a["id"] for a in assignments]
        student_ids = [s["student_id"] for s in students]
        
        if not assignment_ids or not student_ids:
            return {"students": [], "assignments": [], "matrix": []}
        
        # 构建查询条件
        placeholders_a = ",".join(["%s"] * len(assignment_ids))
        placeholders_s = ",".join(["%s"] * len(student_ids))
        
        submissions = conn.execute(f"""
            SELECT sub.assignment_id, sub.student_user_id, sub.is_late, 
                   sub.submitted_at, sub.version_no, sub.grading_status
            FROM submissions sub
            WHERE sub.assignment_id IN ({placeholders_a})
            AND sub.student_user_id IN ({placeholders_s})
            AND sub.version_no = (
                SELECT MAX(s2.version_no) 
                FROM submissions s2 
                WHERE s2.assignment_id = sub.assignment_id 
                AND s2.student_user_id = sub.student_user_id
            )
        """, assignment_ids + student_ids).fetchall()
        
        # 构建提交映射：(assignment_id, student_id) -> submission
        submission_map = {
            (str(s["assignment_id"]), str(s["student_user_id"])): dict(s)
            for s in submissions
        }
        
        # 构建矩阵数据
        now = datetime.now()
        matrix = []
        for student in students:
            row = []
            for assignment in assignments:
                key = (str(assignment["id"]), str(student["student_id"]))
                sub = submission_map.get(key)
                
                if sub:
                    # 有提交记录
                    if sub["is_late"]:
                        status = "late"
                    else:
                        status = "submitted"
                    cell = {
                        "assignment_id": assignment["id"],
                        "student_id": student["student_id"],
                        "status": status,
                        "submitted_at": sub["submitted_at"].isoformat() if sub["submitted_at"] else None,
                        "version_no": sub["version_no"],
                        "grading_status": sub["grading_status"]
                    }
                elif assignment["deadline"] < now:
                    # 截止时间已过且未提交
                    cell = {
                        "assignment_id": assignment["id"],
                        "student_id": student["student_id"],
                        "status": "missing",
                        "submitted_at": None,
                        "version_no": None,
                        "grading_status": None
                    }
                else:
                    # 任务未发布（截止时间未到）
                    cell = {
                        "assignment_id": assignment["id"],
                        "student_id": student["student_id"],
                        "status": "not_published",
                        "submitted_at": None,
                        "version_no": None,
                        "grading_status": None
                    }
                row.append(cell)
            matrix.append({
                "student_id": student["student_id"],
                "name": student["name"],
                "student_no": student["student_no"],
                "class_name": student["class_name"],
                "cells": row
            })
        
        return {
            "students": [dict(s) for s in students],
            "assignments": [dict(a) for a in assignments],
            "matrix": matrix
        }


@router.get("/api/teacher/progress/chart")
def get_progress_chart(
    course_id: Optional[int] = Query(None),
    semester: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    获取柱状图数据：各任务在全班的完成率趋势
    
    返回格式：
    {
        "tasks": [{"id": 1, "title": "第一章作业", "deadline": "2026-06-10", "completion_rate": 0.75}, ...]
    }
    """
    require_teacher(authorization)
    
    with db() as conn:
        # 获取总学生数
        total_students = conn.execute(
            "SELECT COUNT(*) AS cnt FROM users WHERE role='student'"
        ).fetchone()["cnt"]
        
        if total_students == 0:
            return {"tasks": []}
        
        # 查询作业列表
        assignment_query = """
            SELECT a.id, a.title, a.deadline, a.created_at, a.course_id,
                   c.name AS course_name
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
        """
        params = []
        if course_id:
            assignment_query += " WHERE a.course_id = %s"
            params.append(course_id)
        if semester:
            assignment_query += " AND c.term = %s" if course_id else " WHERE c.term = %s"
            params.append(semester)
        assignment_query += " ORDER BY a.deadline"
        
        assignments = conn.execute(assignment_query, params).fetchall()
        
        if not assignments:
            return {"tasks": []}
        
        # 查询每个作业的提交数量
        now = datetime.now()
        tasks = []
        for a in assignments:
            assignment_id = a["id"]
            
            # 获取该作业的最新提交（每个学生只算一次）
            submitted_count = conn.execute("""
                SELECT COUNT(DISTINCT student_user_id) AS cnt
                FROM submissions
                WHERE assignment_id = %s
            """, (assignment_id,)).fetchone()["cnt"]
            
            # 判断是否已截止
            is_past_deadline = a["deadline"] < now
            
            if is_past_deadline:
                completion_rate = submitted_count / total_students if total_students > 0 else 0
            else:
                completion_rate = None  # 未截止的任务不计算完成率
            
            tasks.append({
                "id": assignment_id,
                "title": a["title"],
                "deadline": a["deadline"].isoformat() if a["deadline"] else None,
                "created_at": a["created_at"].isoformat() if a["created_at"] else None,
                "course_name": a["course_name"],
                "total_students": total_students,
                "submitted_count": submitted_count,
                "completion_rate": round(completion_rate, 2) if completion_rate is not None else None,
                "is_past_deadline": is_past_deadline
            })
        
        return {"tasks": tasks}


@router.get("/api/teacher/progress/matrix")
def get_progress_matrix(
    course_id: Optional[int] = Query(None),
    semester: Optional[str] = Query(None),
    bottom_n: int = Query(5, description="完成率最低的前N名学生置顶"),
    sort_order: str = Query("completion_asc", description="排序方式"),
    authorization: Optional[str] = Header(None)
):
    """
    获取完整的进度矩阵数据，包含排序（完成率最低的前N名置顶高亮）
    
    返回格式（兼容前端期望的exams字段）：
    {
        "students": [...],
        "exams": [...],
        "matrix": [...]
    }
    """
    require_teacher(authorization)
    
    # 获取热力图数据
    heatmap_data = get_progress_heatmap(course_id=course_id, semester=semester, authorization=authorization)
    
    # 转换assignments为exams格式（前端期望的字段名）
    exams = []
    for assn in heatmap_data["assignments"]:
        deadline = assn.get("deadline", "")
        # deadline可能是datetime对象或字符串
        if isinstance(deadline, datetime):
            deadline_str = deadline.strftime("%Y-%m-%d %H:%M:%S")
            is_active = datetime.now() >= deadline
        elif isinstance(deadline, str) and deadline:
            deadline_str = deadline
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
                is_active = datetime.now() >= deadline_dt
            except:
                is_active = False
        else:
            deadline_str = ""
            is_active = False
            
        exams.append({
            "id": f"hw{assn['id']}",
            "title": assn["title"],
            "deadline": deadline_str,
            "published_at": assn.get("created_at", ""),
            "semester": semester or "2024-2025-2",
            "is_active": is_active,
            "total_students": len(heatmap_data["students"]),
            "submitted": 0,
            "completion_rate": 0.0
        })
    
    # 构建学生数据（包含statuses字段，前端需要）
    now = datetime.now()
    students = []
    for row in heatmap_data["matrix"]:
        student_id = row["student_id"]
        cells = row["cells"]
        
        # 构建statuses字典
        statuses = {}
        for idx, cell in enumerate(cells):
            exam_id = f"hw{heatmap_data['assignments'][idx]['id']}"
            status_map = {
                "submitted": "submitted",
                "late": "late",
                "missing": "unsubmitted",
                "not_published": "not_published"
            }
            status = status_map.get(cell["status"], "not_published")
            
            status_info = {"status": status}
            if cell.get("submitted_at"):
                status_info["submitted_at"] = cell["submitted_at"]
            if cell.get("score") is not None:
                status_info["score"] = cell["score"]
                status_info["total"] = 100
            
            statuses[exam_id] = status_info
        
        # 计算完成率
        completed = sum(1 for c in cells if c["status"] in ["submitted", "late"])
        past_deadline = sum(1 for c in cells if c["status"] in ["submitted", "late", "missing"])
        
        if past_deadline > 0:
            completion_rate = completed / past_deadline
        else:
            completion_rate = 1.0
        
        students.append({
            "student_id": student_id,
            "name": row["name"],
            "student_no": row["student_no"],
            "class_name": row["class_name"],
            "completion_rate": round(completion_rate, 3),
            "highlight": False,
            "statuses": statuses
        })
    
    # 排序
    if sort_order == "completion_asc":
        students.sort(key=lambda x: x["completion_rate"])
    else:
        students.sort(key=lambda x: x["name"])
    
    # 高亮前N名
    for i, student in enumerate(students):
        student["highlight"] = i < bottom_n and student["completion_rate"] < 1.0
    
    # 更新exams的完成率统计
    for exam in exams:
        submitted = 0
        for student in students:
            st = student["statuses"].get(exam["id"])
            if st and (st["status"] == "submitted" or st["status"] == "late"):
                submitted += 1
        exam["submitted"] = submitted
        exam["completion_rate"] = round(submitted / len(students), 3) if students else 0.0
    
    return {
        "students": students,
        "exams": exams,
        "matrix": heatmap_data["matrix"]
    }


@router.get("/api/teacher/progress/submission/{student_user_id}/{assignment_id}")
def get_submission_detail(
    student_user_id: int,
    assignment_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    获取学生某任务的提交详情
    
    返回格式：
    {
        "student": {"id": 1, "name": "张三", "student_no": "2021001", "class_name": "计算机1班"},
        "assignment": {"id": 1, "title": "第一章作业", "deadline": "2026-06-10"},
        "submission": {
            "id": 1,
            "version_no": 2,
            "is_late": false,
            "submitted_at": "2026-06-09T10:30:00",
            "grading_status": "graded",
            "file_url": "...",
            "text_content": "..."
        } or None
    }
    """
    require_teacher(authorization)
    
    with db() as conn:
        # 获取学生信息
        student = conn.execute("""
            SELECT s.user_id AS student_id, u.full_name AS name, 
                   u.student_no, COALESCE(s.class_name, '') AS class_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE u.role = 'student' AND s.user_id = %s
        """, (student_user_id,)).fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 获取作业信息
        assignment = conn.execute("""
            SELECT a.id, a.title, a.deadline, a.description_md, a.late_policy,
                   c.name AS course_name
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            WHERE a.id = %s
        """, (assignment_id,)).fetchone()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="作业不存在")
        
        # 获取最新的提交记录
        submission = conn.execute("""
            SELECT id, version_no, is_late, submitted_at, grading_status,
                   file_url, text_content
            FROM submissions
            WHERE assignment_id = %s AND student_user_id = %s
            ORDER BY version_no DESC
            LIMIT 1
        """, (assignment_id, student_user_id)).fetchone()
        
        return {
            "student": dict(student),
            "assignment": {
                "id": assignment["id"],
                "title": assignment["title"],
                "deadline": assignment["deadline"].isoformat() if assignment["deadline"] else None,
                "description": assignment["description_md"],
                "late_policy": assignment["late_policy"],
                "course_name": assignment["course_name"]
            },
            "submission": dict(submission) if submission else None
        }


@router.get("/api/teacher/progress/courses")
def get_progress_courses(
    authorization: Optional[str] = Header(None)
):
    """
    获取可用于进度看板筛选的课程列表
    
    返回格式：
    {
        "courses": [{"id": 1, "code": "CS2026-PYTHON", "name": "Python程序设计", "term": "2026-春"}, ...]
    }
    """
    require_teacher(authorization)
    
    with db() as conn:
        courses = conn.execute("""
            SELECT id, code, name, term
            FROM courses
            ORDER BY term DESC, code
        """).fetchall()
    
    return {"courses": [dict(c) for c in courses]}
