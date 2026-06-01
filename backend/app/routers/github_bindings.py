"""F-T-001 学生-GitHub账号对应表 API 路由

教师后台管理全班学生与GitHub账号的完整映射表，支持：
- CSV批量导入并自动校验
- 单条手动新增/编辑/删除
- 重复账号冲突检测
- 按班级/课程筛选与导出
- 绑定变更后自动重算历史成绩关联
"""
import os
import io
import csv
import sqlite3
import chardet
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel

from app.database import db
from app.auth_utils import verify_teacher_token

router = APIRouter()


def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _recalculate_student_scores(student_user_id: str, github_username: str):
    """
    当学生的 GitHub 绑定变更时，更新相关的提交记录和评分记录
    
    :param student_user_id: 学生学号
    :param github_username: GitHub 用户名
    :return: 更新的记录数量
    """
    try:
        with db() as conn:
            # 查找该学生的所有提交记录
            cursor = conn.execute("""
                SELECT id FROM submissions 
                WHERE student_user_id = ?
            """, (student_user_id,))
            
            submissions = cursor.fetchall()
            if not submissions:
                return 0
            
            # 更新对应的评分记录（确保关联正确）
            updated_count = 0
            for submission in submissions:
                submission_id = str(submission[0])
                
                conn.execute("""
                    UPDATE grading_records 
                    SET student_user_id = ? 
                    WHERE submission_id = ?
                """, (student_user_id, submission_id))
                
                updated_count += 1
            
            return updated_count
    except sqlite3.OperationalError as e:
        # 如果表不存在，返回 0（表示没有需要更新的记录）
        if "no such table" in str(e):
            return 0
        raise


class GitHubBindingRequest(BaseModel):
    student_user_id: str
    github_username: str
    class_name: str = ""
    course_name: str = ""


@router.post("/api/teacher/github/bindings")
async def import_github_bindings(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """批量导入学生-GitHub账号映射 CSV"""
    _require_teacher(authorization)

    raw = await file.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    text = raw.decode(encoding, errors="replace")

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(status_code=422, detail="文件为空")

    # 检查表头（只需要学号、姓名、GitHub用户名三列）
    header = lines[0]
    required_cols = ["学号", "姓名", "GitHub用户名"]
    if not all(col in header for col in required_cols):
        raise HTTPException(status_code=422, detail="CSV 必须包含：学号、姓名、GitHub用户名 三列")

    data_lines = lines[1:]
    records = []
    github_used = set()
    conflicts = []

    for line_num, line in enumerate(data_lines, start=2):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        student_id = parts[0]
        name = parts[1]
        github_username = parts[2]

        if not student_id or not name or not github_username:
            continue

        # 检测重复 GitHub 账号
        if github_username in github_used:
            conflicts.append(f"第{line_num}行：{github_username} 重复")
        else:
            github_used.add(github_username)
            records.append((student_id, github_username))

    # 验证学生并获取班级信息
    with db() as conn:
        # 获取所有学生信息（正确处理 sqlite3.Row 对象）
        students = {}
        for row in conn.execute("SELECT student_id, class_name FROM students").fetchall():
            # sqlite3.Row 对象需要通过索引访问
            student_id = str(row[0])
            class_name = str(row[1]) if len(row) > 1 else ""
            students[student_id] = {"class_name": class_name}
        
        # 验证学号是否存在
        invalid_ids = [r[0] for r in records if r[0] not in students]
        if invalid_ids:
            raise HTTPException(status_code=422, detail=f"以下学号不存在于学生名单：{', '.join(invalid_ids)}")

        # 插入/更新绑定记录（班级从students表获取）
        for student_id, github_username in records:
            class_name = students[student_id]["class_name"]
            conn.execute("""
                INSERT INTO github_bindings (student_user_id, github_username, class_name)
                VALUES (?,?,?)
                ON CONFLICT(student_user_id) DO UPDATE SET
                    github_username=excluded.github_username,
                    class_name=excluded.class_name
            """, (student_id, github_username, class_name))

    # 自动重算历史成绩
    total_recalculated = 0
    for student_id, github_username in records:
        recalculated = _recalculate_student_scores(student_id, github_username)
        total_recalculated += recalculated

    message = f"成功导入 {len(records)} 条绑定记录"
    if conflicts:
        message += f"，发现 {len(conflicts)} 个重复账号"
    if total_recalculated > 0:
        message += f"，已关联 {total_recalculated} 条提交记录"

    return {
        "ok": True,
        "inserted": len(records),
        "conflicts": conflicts,
        "recalculated": total_recalculated,
        "message": message
    }


@router.get("/api/teacher/github/bindings")
def list_github_bindings(
    class_name: Optional[str] = Query(None),
    course_name: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """获取学生-GitHub账号映射列表（支持筛选）"""
    _require_teacher(authorization)

    with db() as conn:
        query = """
            SELECT gb.student_user_id, s.name, gb.github_username, gb.github_name, 
                   gb.verify_status, gb.class_name, gb.course_name
            FROM github_bindings gb
            LEFT JOIN students s ON gb.student_user_id = s.student_id
        """
        params = []
        conditions = []

        if class_name:
            conditions.append("gb.class_name = ?")
            params.append(class_name)
        if course_name:
            conditions.append("gb.course_name = ?")
            params.append(course_name)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY gb.student_user_id"
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


@router.post("/api/teacher/github/bindings/add")
def add_github_binding(req: GitHubBindingRequest, authorization: Optional[str] = Header(None)):
    """手动添加单条 GitHub 绑定记录"""
    _require_teacher(authorization)

    req.student_user_id = req.student_user_id.strip()
    req.github_username = req.github_username.strip()

    if not req.student_user_id or not req.github_username:
        raise HTTPException(status_code=422, detail="学号和 GitHub 用户名不能为空")

    with db() as conn:
        # 验证学生存在并获取班级信息
        student = conn.execute(
            "SELECT name, class_name FROM students WHERE student_id=?", (req.student_user_id,)
        ).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail=f"学号 {req.student_user_id} 不存在")

        # 检查 GitHub 账号是否已被绑定
        existing = conn.execute(
            "SELECT student_user_id FROM github_bindings WHERE github_username=?",
            (req.github_username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"GitHub 账号 {req.github_username} 已被绑定")

        # 使用索引访问 sqlite3.Row 对象
        student_name = str(student[0])
        class_name = str(student[1]) if len(student) > 1 else ""

        conn.execute("""
            INSERT INTO github_bindings (student_user_id, github_username, class_name)
            VALUES (?,?,?)
        """, (req.student_user_id, req.github_username, class_name))

    # 自动重算历史成绩
    recalculated = _recalculate_student_scores(req.student_user_id, req.github_username)
    
    message = f"已绑定 {student_name} ↔ {req.github_username}"
    if recalculated > 0:
        message += f"，已关联 {recalculated} 条提交记录"

    return {"ok": True, "message": message}


@router.put("/api/teacher/github/bindings/{student_id}")
def update_github_binding(
    student_id: str,
    github_username: str = Query(...),
    authorization: Optional[str] = Header(None)
):
    """更新学生的 GitHub 账号绑定"""
    _require_teacher(authorization)

    github_username = github_username.strip()
    if not github_username:
        raise HTTPException(status_code=422, detail="GitHub 用户名不能为空")

    with db() as conn:
        # 检查新账号是否被其他学生使用
        existing = conn.execute(
            "SELECT student_user_id FROM github_bindings WHERE github_username=? AND student_user_id != ?",
            (github_username, student_id)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"GitHub 账号 {github_username} 已被其他学生绑定")

        conn.execute(
            "UPDATE github_bindings SET github_username=? WHERE student_user_id=?",
            (github_username, student_id)
        )

    # 自动重算历史成绩
    recalculated = _recalculate_student_scores(student_id, github_username)
    
    message = "绑定已更新"
    if recalculated > 0:
        message += f"，已关联 {recalculated} 条提交记录"

    return {"ok": True, "message": message}


@router.delete("/api/teacher/github/bindings/{student_id}")
def delete_github_binding(student_id: str, authorization: Optional[str] = Header(None)):
    """删除学生的 GitHub 绑定记录"""
    _require_teacher(authorization)

    with db() as conn:
        binding = conn.execute(
            "SELECT github_username FROM github_bindings WHERE student_user_id=?",
            (student_id,)
        ).fetchone()
        if not binding:
            raise HTTPException(status_code=404, detail="绑定记录不存在")

        conn.execute("DELETE FROM github_bindings WHERE student_user_id=?", (student_id,))

    return {"ok": True, "message": f"已解除绑定 GitHub: {binding['github_username']}"}


@router.get("/api/teacher/github/bindings/export")
def export_github_bindings(
    class_name: Optional[str] = Query(None),
    course_name: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """导出学生-GitHub账号映射 CSV"""
    _require_teacher(authorization)

    with db() as conn:
        query = """
            SELECT gb.student_user_id, s.name, gb.github_username, gb.class_name, gb.course_name
            FROM github_bindings gb
            LEFT JOIN students s ON gb.student_user_id = s.student_id
        """
        params = []
        conditions = []

        if class_name:
            conditions.append("gb.class_name = ?")
            params.append(class_name)
        if course_name:
            conditions.append("gb.course_name = ?")
            params.append(course_name)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY gb.student_user_id"
        rows = conn.execute(query, params).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["学号", "姓名", "GitHub用户名", "班级", "课程"])
    for r in rows:
        writer.writerow([r["student_user_id"], r["name"] or "", r["github_username"], r["class_name"] or "", r["course_name"] or ""])

    output.seek(0)
    filename = f"github_bindings_{datetime.now().strftime('%Y%m%d')}.csv"
    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


@router.get("/api/teacher/github/classes")
def get_classes(authorization: Optional[str] = Header(None)):
    """获取所有班级列表（用于筛选）"""
    _require_teacher(authorization)

    with db() as conn:
        rows = conn.execute("SELECT DISTINCT class_name FROM github_bindings WHERE class_name != '' ORDER BY class_name").fetchall()

    return [r["class_name"] for r in rows]


@router.get("/api/teacher/github/courses")
def get_courses(authorization: Optional[str] = Header(None)):
    """获取所有课程列表（用于筛选）"""
    _require_teacher(authorization)

    with db() as conn:
        rows = conn.execute("SELECT DISTINCT course_name FROM github_bindings WHERE course_name != '' ORDER BY course_name").fetchall()

    return [r["course_name"] for r in rows]
