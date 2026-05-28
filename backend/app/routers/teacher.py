import os
import io
import uuid
import chardet
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from app.database import db
from app.auth_utils import create_token, verify_teacher_token
from app.sync_exams import sync_exams
from pypinyin import lazy_pinyin, Style
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from dotenv import load_dotenv

load_dotenv()

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


@router.get("/api/teacher/exams")
def list_exams(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM exams ORDER BY id")
        exams = cursor.fetchall()
        
        # 转换为原来的格式
        result = []
        for exam in exams:
            result.append({
                "id": str(exam["id"]),
                "title": exam["title"],
                "is_active": 1,  # 默认都激活
                "submitted": 0,
                "total_students": 0,
                "avg_score": None
            })
    
    return result


@router.get("/api/teacher/students/list")
def list_students(authorization: Optional[str] = Header(None)):
    """获取全部学生名单"""
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.full_name as name, u.student_no as student_id, s.class_name 
            FROM users u 
            JOIN students s ON u.id = s.user_id 
            WHERE u.role = 'student'
            ORDER BY s.class_name, u.full_name
        """)
        rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


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
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 查找默认教师
        cursor.execute("SELECT user_id FROM teachers LIMIT 1")
        teacher = cursor.fetchone()
        if not teacher:
            raise HTTPException(status_code=500, detail="没有找到教师用户")
        
        teacher_id = teacher["user_id"]
        
        # 查找默认课程
        cursor.execute("SELECT id FROM courses LIMIT 1")
        course = cursor.fetchone()
        course_id = course["id"] if course else None
        
        # 检查学生是否已存在
        cursor.execute("SELECT id FROM users WHERE student_no = %s", (req.student_id,))
        existing = cursor.fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail=f"学号 {req.student_id} 已存在")
        
        # 创建用户 - 密码就用学号
        cursor.execute("""
            INSERT INTO users (role, student_no, email, password_hash, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ('student', req.student_id, f"{req.student_id}@example.com", req.student_id, req.name))
        user_id = cursor.lastrowid
        
        # 创建学生记录
        cursor.execute("""
            INSERT INTO students (user_id, class_name)
            VALUES (%s, %s)
        """, (user_id, req.class_name or "默认班级"))
        
        # 同时创建一个课程注册记录
        if course_id:
            cursor.execute("""
                INSERT INTO enrollments (course_id, student_user_id)
                VALUES (%s, %s)
            """, (course_id, user_id))
    
    return {"ok": True}


@router.delete("/api/teacher/students/{student_id}")
def delete_student(student_id: str, authorization: Optional[str] = Header(None)):
    """删除单个学生"""
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 查找学生
        cursor.execute("SELECT id FROM users WHERE student_no = %s", (student_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="学号不存在")
        
        user_id = user["id"]
        
        # 删除关联记录 - 先删除注册记录
        cursor.execute("DELETE FROM enrollments WHERE student_user_id = %s", (user_id,))
        # 然后删除学生记录
        cursor.execute("DELETE FROM students WHERE user_id = %s", (user_id,))
        # 最后删除用户
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    
    return {"ok": True}


@router.delete("/api/teacher/students")
def clear_all_students(authorization: Optional[str] = Header(None)):
    """清空全部学生名单"""
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 获取学生数量
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'")
        count = cursor.fetchone()["cnt"]
        
        # 删除关联记录
        cursor.execute("""
            DELETE e FROM enrollments e
            JOIN users u ON e.student_user_id = u.id
            WHERE u.role = 'student'
        """)
        cursor.execute("DELETE FROM students WHERE user_id IN (SELECT id FROM users WHERE role = 'student')")
        cursor.execute("DELETE FROM users WHERE role = 'student'")
    
    return {"ok": True, "deleted_count": count}


@router.post("/api/teacher/students")
async def upload_students(
    file: UploadFile = File(...),
    import_mode: str = Form("incremental"),
    authorization: Optional[str] = Header(None)
):
    """上传学生名单 CSV（支持增量/全量覆盖模式，UTF-8/GBK编码）"""
    _require_teacher(authorization)
    
    batch_id = str(uuid.uuid4())[:8]  # 短批次号
    operator = "teacher"
    
    # 读取文件
    content = await file.read()
    detected = chardet.detect(content)
    encoding = detected.get("encoding", "utf-8") or "utf-8"
    
    # 尝试解码
    try:
        text = content.decode(encoding)
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="replace")
    
    # 解析 CSV
    lines = text.splitlines()
    reader = csv.DictReader(lines)
    
    # 清理表头（去除BOM和空格）
    reader.fieldnames = [f.strip().lstrip("\ufeff") for f in reader.fieldnames] if reader.fieldnames else []
    fields = reader.fieldnames or []
    
    # 校验字段
    if "学号" not in fields or "姓名" not in fields:
        raise HTTPException(status_code=422, detail="CSV 格式错误：缺少必要字段「学号」或「姓名」")
    
    existing_student_ids = set()
    existing_student_users = {}
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 获取现有学生
        cursor.execute("""
            SELECT u.student_no, u.id FROM users u
            WHERE u.role = 'student'
        """)
        for row in cursor.fetchall():
            existing_student_ids.add(row["student_no"])
            existing_student_users[row["student_no"]] = row["id"]
        
        # 查找默认教师
        cursor.execute("SELECT user_id FROM teachers LIMIT 1")
        teacher = cursor.fetchone()
        if not teacher:
            raise HTTPException(status_code=500, detail="没有找到教师用户")
        
        teacher_id = teacher["user_id"]
        
        # 查找默认课程
        cursor.execute("SELECT id FROM courses LIMIT 1")
        course = cursor.fetchone()
        course_id = course["id"] if course else None
        
        # 如果是全量模式，先清空（保留原有主键，清空内容）
        if import_mode == "full":
            cursor.execute("""
                DELETE e FROM enrollments e
                JOIN users u ON e.student_user_id = u.id
                WHERE u.role = 'student'
            """)
            cursor.execute("DELETE FROM students WHERE user_id IN (SELECT id FROM users WHERE role = 'student')")
            cursor.execute("DELETE FROM users WHERE role = 'student'")
            existing_student_ids = set()
            existing_student_users = {}
        
        # 解析和校验每行数据
        rows = []
        errors = []
        student_ids_in_file = set()
        seen_student_ids = set()
        
        for idx, row in enumerate(reader, start=2):
            # 获取字段
            student_id = str(row.get("学号", "")).strip()
            name = str(row.get("姓名", "")).strip()
            class_name = str(row.get("班级", "")).strip()
            course_name = str(row.get("课程", "")).strip()
            
            # 完整性校验
            row_errors = []
            if not student_id:
                row_errors.append("学号不能为空")
            if not name:
                row_errors.append("姓名不能为空")
            
            # 唯一性校验
            if student_id and student_id in seen_student_ids:
                row_errors.append(f"学号 {student_id} 在文件中重复")
            if student_id and student_id in existing_student_ids and import_mode == "incremental":
                row_errors.append(f"学号 {student_id} 已存在于系统中")
            
            # 收集有效行
            if not row_errors:
                seen_student_ids.add(student_id)
                student_ids_in_file.add(student_id)
                rows.append({
                    "student_id": student_id,
                    "name": name,
                    "class_name": class_name,
                    "course_name": course_name,
                    "line": idx
                })
            else:
                errors.append({
                    "line": idx,
                    "raw": row,
                    "errors": row_errors
                })
        
        # 执行导入
        success_count = 0
        created_user_ids = []
        
        for row in rows:
            try:
                # 创建用户
                cursor.execute("""
                    INSERT INTO users (role, student_no, email, password_hash, full_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('student', row["student_id"], f"{row['student_id']}@example.com", row["student_id"], row["name"]))
                user_id = cursor.lastrowid
                created_user_ids.append(user_id)
                
                # 创建学生记录
                cursor.execute("""
                    INSERT INTO students (user_id, class_name)
                    VALUES (%s, %s)
                """, (user_id, row["class_name"] or "默认班级"))
                
                # 同时创建一个课程注册记录
                if course_id:
                    cursor.execute("""
                        INSERT INTO enrollments (course_id, student_user_id)
                        VALUES (%s, %s)
                    """, (course_id, user_id))
                
                success_count += 1
            except Exception as e:
                errors.append({
                    "line": row["line"],
                    "raw": {
                        "学号": row["student_id"],
                        "姓名": row["name"],
                        "班级": row["class_name"],
                        "课程": row["course_name"]
                    },
                    "errors": [str(e)]
                })
        
        # 记录导入日志到 notifications 表（用管理员或教师用户ID）
        # 先获取一个可以用于通知的用户ID，用当前教师用户
        notification_user_id = teacher_id
        
        # 构建导入日志消息
        log_message = f"""
批次号: {batch_id}
操作人: {operator}
导入模式: {import_mode}
总记录数: {len(rows) + len(errors)}
成功: {success_count}
失败: {len(errors)}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # 记录导入通知
        cursor.execute("""
            INSERT INTO notifications (user_id, title, body, category, is_read)
            VALUES (%s, %s, %s, %s, %s)
        """, (notification_user_id, "学生名单导入日志", log_message, "system", 0))
        log_id = cursor.lastrowid
        
        # 给每个新导入的学生发送激活邀请
        for user_id in created_user_ids:
            # 获取学生信息
            cursor.execute("""
                SELECT full_name, student_no FROM users WHERE id = %s
            """, (user_id,))
            student = cursor.fetchone()
            
            if student:
                activation_message = f"""
{student['full_name']} 同学您好：

您的账号已成功创建！
学号：{student['student_no']}
初始密码：{student['student_no']}

请及时登录并修改密码。

此致敬礼！
教师管理系统
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """.strip()
                
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, body, category, is_read)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, "账号激活通知", activation_message, "announcement", 0))
        
        return {
            "batch_id": batch_id,
            "import_mode": import_mode,
            "total": len(rows) + len(errors),
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors,
            "log_id": log_id
        }


@router.get("/api/teacher/import-logs")
def list_import_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """获取导入日志列表"""
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 查询导入相关的系统通知
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT id, title, body, created_at 
            FROM notifications 
            WHERE category = 'system' 
            AND title LIKE '学生名单导入日志'
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        rows = cursor.fetchall()
        
        # 解析日志内容
        result = []
        for row in rows:
            body = row["body"]
            # 从日志内容中提取信息
            log_info = {"id": row["id"], "created_at": row["created_at"]}
            
            # 简单解析
            lines = body.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("批次号:"):
                    log_info["batch_id"] = line.split(":", 1)[1].strip()
                elif line.startswith("操作人:"):
                    log_info["operator"] = line.split(":", 1)[1].strip()
                elif line.startswith("导入模式:"):
                    log_info["import_mode"] = line.split(":", 1)[1].strip()
                elif line.startswith("总记录数:"):
                    log_info["total_records"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("成功:"):
                    log_info["success_count"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("失败:"):
                    log_info["error_count"] = int(line.split(":", 1)[1].strip())
            
            result.append(log_info)
        
        # 总数
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM notifications 
            WHERE category = 'system' 
            AND title LIKE '学生名单导入日志'
        """)
        total = cursor.fetchone()["total"]
    
    return {
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/api/teacher/import-logs/{log_id}/errors")
def get_import_errors(
    log_id: int,
    authorization: Optional[str] = Header(None)
):
    """获取某次导入的错误详情"""
    _require_teacher(authorization)
    
    # 由于我们不存储错误详情，这里返回一个友好的提示
    # 在实际系统中，错误详情会临时存储在内存中
    with db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, body, created_at 
            FROM notifications 
            WHERE id = %s
        """, (log_id,))
        log = cursor.fetchone()
        
        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")
    
    return {
        "log_id": log_id,
        "message": "完整错误详情在导入完成后已在响应中返回，详细信息请查看导入时的反馈。",
        "log_content": log["body"]
    }


@router.get("/api/teacher/scores")
def get_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """获取某次考试的所有学生成绩"""
    _require_teacher(authorization)
    
    with db() as conn:
        cursor = conn.cursor()
        
        # 检查考试是否存在
        cursor.execute("SELECT title FROM exams WHERE id = %s", (int(exam_id),))
        exam = cursor.fetchone()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        # 获取所有学生
        cursor.execute("""
            SELECT u.full_name as name, u.student_no as student_id, s.class_name, u.id as user_id
            FROM users u 
            JOIN students s ON u.id = s.user_id 
            WHERE u.role = 'student'
            ORDER BY u.student_no
        """)
        students = cursor.fetchall()
        
        # 获取成绩 - 使用 exam_attempts 和 exam_answers 或者 score_items
        # 这里我们用一个简化的方式
        result = []
        for student in students:
            result.append({
                "name": student["name"],
                "student_id": student["student_id"],
                "class_name": student["class_name"],
                "score": None,
                "total": None,
                "submitted_at": None
            })

    return {"exam_title": exam["title"], "rows": result}


@router.get("/api/teacher/scores/export")
def export_scores(exam_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """导出成绩 Excel"""
    _require_teacher(authorization)

    with db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT title FROM exams WHERE id = %s", (int(exam_id),))
        exam = cursor.fetchone()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")

        cursor.execute("""
            SELECT u.full_name as name, u.student_no as student_id, s.class_name
            FROM users u 
            JOIN students s ON u.id = s.user_id 
            WHERE u.role = 'student'
            ORDER BY u.student_no
        """)
        students = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = exam["title"][:31] if len(exam["title"]) > 31 else exam["title"]

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["姓名", "学号", "班级"]
    col_widths = [12, 14, 20]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = w

    for row_idx, student in enumerate(students, 2):
        ws.cell(row=row_idx, column=1, value=student["name"])
        ws.cell(row=row_idx, column=2, value=student["student_id"])
        ws.cell(row=row_idx, column=3, value=student["class_name"])

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
