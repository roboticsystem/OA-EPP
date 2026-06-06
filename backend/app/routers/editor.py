"""需求文档编辑器 API — 文档 CRUD / 模板 / 导入 / 校验 / Copilot / GitHub / 审阅。

所有端点前缀: /api/editor
"""

import os
import re
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database_mysql import db
from app.auth_utils import verify_teacher_token, verify_student_token, create_token
from app.markdown_validator import validate as validate_markdown
from app.suggestion_engine import get_suggestions
from app.github_client import extract_features, create_issues_batch

router = APIRouter()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _require_teacher(authorization: Optional[str]) -> dict:
    """验证教师 Token 并返回 payload（含 user_id）。

    Token 不含 user_id 时从 MySQL users 表查询补充。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # 补充 user_id（原有登录接口不返回 user_id）
    if not payload.get("user_id"):
        try:
            with db() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT u.id FROM users u JOIN teachers t ON t.user_id = u.id WHERE u.role = 'teacher' LIMIT 1"
                )
                row = cur.fetchone()
                if row:
                    payload["user_id"] = row["id"]
        except Exception:
            payload["user_id"] = 65  # 默认 fallback
    return payload


def _require_student(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_student_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CreateDocumentRequest(BaseModel):
    course_id: int
    title: str
    content_md: str = ""


class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    content_md: str
    increment_version: bool = True


class StatusTransitionRequest(BaseModel):
    status: str  # 'reviewing', 'sealed', 'archived'


class GenerateIssuesRequest(BaseModel):
    owner: Optional[str] = None
    repo: Optional[str] = None
    selected_features: Optional[List[str]] = None


class AddCommentRequest(BaseModel):
    content: str
    line_reference: Optional[str] = None


class TeacherCommentResponse(BaseModel):
    teacher_response: Optional[str] = None
    status: str  # 'confirmed' | 'dismissed'


class ValidateRequest(BaseModel):
    content_md: str


class SuggestionRequest(BaseModel):
    content_md: str
    cursor_line: int = 0


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

PRESET_TEMPLATES = [
    {
        "id": "functional_requirement",
        "name": "功能需求 (F-xxx)",
        "description": "标准功能需求块，包含功能描述、验收标准、安全属性",
        "content": (
            "### F-xxx 功能名称\n\n"
            "**需求描述**：\n\n"
            "- \n\n"
            "**验收标准**：\n"
            "- [ ] 功能可正常使用\n"
            "- [ ] 异常输入有合理提示\n"
            "- [ ] 操作日志可追溯\n\n"
            "**安全属性**：\n"
            "- 敏感数据加密存储（AES-256-GCM）\n"
            "- 操作需通过权限校验\n"
            "- 输入参数做防注入过滤\n\n"
            "**优先级**：P0 / P1 / P2\n\n"
            "**关联功能**：F-xxx\n"
        ),
    },
    {
        "id": "acceptance_criteria",
        "name": "验收标准",
        "description": "结构化验收标准清单",
        "content": (
            "**验收标准**：\n\n"
            "- [ ] 正常流程：\n"
            "- [ ] 边界条件：\n"
            "- [ ] 异常场景：\n"
            "- [ ] 性能指标：\n"
            "- [ ] 安全合规：\n"
        ),
    },
    {
        "id": "security_attributes",
        "name": "安全属性",
        "description": "功能安全属性声明模板",
        "content": (
            "**安全属性**：\n\n"
            "- **认证**：\n"
            "- **授权**：\n"
            "- **数据保护**：传输 TLS 1.3 / 存储 AES-256\n"
            "- **审计**：操作日志记录到 audit_logs\n"
            "- **输入校验**：参数白名单 + 类型校验\n"
            "- **Session 管理**：JWT 过期策略 + 刷新机制\n"
        ),
    },
    {
        "id": "non_functional_requirement",
        "name": "非功能需求 (NFR)",
        "description": "性能/可用性/兼容性等非功能需求模板",
        "content": (
            "### NFR-xxx 非功能需求\n\n"
            "**性能**：\n"
            "- 响应时间 P95 < 200ms\n"
            "- 并发支持 ≥ 100 用户\n\n"
            "**可用性**：\n"
            "- 系统可用性 ≥ 99.5%\n"
            "- 计划内维护窗口 ≤ 4h/月\n\n"
            "**兼容性**：\n"
            "- 浏览器：Chrome/Firefox/Edge 最新两个主版本\n"
            "- 移动端：响应式适配\n\n"
            "**安全性**：\n"
            "- OWASP Top 10 防护\n"
        ),
    },
    {
        "id": "chapter_section",
        "name": "章节骨架",
        "description": "含前端元数据和章节小结/测验的完整章节结构（遵循 contributing.md）",
        "content": (
            "---\n"
            "number headings: first-level 2, start-at 1\n"
            "---\n\n"
            "## 1 第1章 章节标题\n\n"
            "### 1.1 本章知识导图\n\n"
            "<!-- 可选：PlantUML 思维导图 -->\n\n"
            "### 1.2 第一节\n\n"
            "正文内容。\n\n"
            "### 1.3 本章小结\n\n"
            "### 1.4 本章测验\n\n"
        ),
    },
    {
        "id": "data_model",
        "name": "数据模型定义",
        "description": "数据库表/字段定义模板（ER图 + SQL DDL）",
        "content": (
            "### 数据模型\n\n"
            "**表名**：`table_name`\n\n"
            "| 字段 | 类型 | 约束 | 说明 |\n"
            "|------|------|------|------|\n"
            "| id | BIGINT | PK AUTO_INCREMENT | 主键 |\n"
            "| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 创建时间 |\n\n"
            "```sql\n"
            "CREATE TABLE table_name (\n"
            "    id BIGINT NOT NULL AUTO_INCREMENT,\n"
            "    PRIMARY KEY (id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n"
            "```\n"
        ),
    },
]


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


@router.get("/api/editor/courses")
def list_courses(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    try:
        with db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, code, name, term, status FROM courses ORDER BY id"
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")


# ---------------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------------


@router.get("/api/editor/documents")
def list_documents(
    course_id: Optional[int] = Query(None),
    authorization: Optional[str] = Header(None),
):
    _require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        if course_id:
            cur.execute(
                """SELECT d.id, d.course_id, d.title, d.status, d.version_no,
                          d.created_by, d.updated_at, c.name AS course_name
                   FROM req_documents d
                   JOIN courses c ON c.id = d.course_id
                   WHERE d.course_id = %s
                   ORDER BY d.updated_at DESC""",
                (course_id,),
            )
        else:
            cur.execute(
                """SELECT d.id, d.course_id, d.title, d.status, d.version_no,
                          d.created_by, d.updated_at, c.name AS course_name
                   FROM req_documents d
                   JOIN courses c ON c.id = d.course_id
                   ORDER BY d.updated_at DESC"""
            )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.post("/api/editor/documents")
def create_document(
    req: CreateDocumentRequest,
    authorization: Optional[str] = Header(None),
):
    teacher = _require_teacher(authorization)
    teacher_id = teacher.get("user_id", 0)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO req_documents (course_id, title, content_md, created_by)
               VALUES (%s, %s, %s, %s)""",
            (req.course_id, req.title, req.content_md, teacher_id),
        )
        doc_id = cur.lastrowid
        cur.execute(
            "SELECT id, course_id, title, status, version_no, created_by, updated_at FROM req_documents WHERE id = %s",
            (doc_id,),
        )
        row = cur.fetchone()
    return dict(row)


@router.get("/api/editor/documents/{doc_id}")
def get_document(doc_id: int, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT d.id, d.course_id, d.title, d.content_md, d.status,
                      d.version_no, d.created_by, d.updated_at,
                      c.name AS course_name
               FROM req_documents d
               JOIN courses c ON c.id = d.course_id
               WHERE d.id = %s""",
            (doc_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="文档不存在")
    return dict(row)


@router.put("/api/editor/documents/{doc_id}")
def update_document(
    doc_id: int,
    req: UpdateDocumentRequest,
    authorization: Optional[str] = Header(None),
):
    _require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status, version_no FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] in ("sealed", "archived"):
            raise HTTPException(status_code=403, detail="已封存/归档的文档不可编辑")

        new_title = req.title if req.title is not None else doc.get("title", "")
        new_version = doc["version_no"] + 1 if req.increment_version else doc["version_no"]

        cur.execute(
            """UPDATE req_documents
               SET title = %s, content_md = %s, version_no = %s
               WHERE id = %s""",
            (new_title, req.content_md, new_version, doc_id),
        )

        cur.execute(
            "SELECT id, course_id, title, status, version_no, created_by, updated_at FROM req_documents WHERE id = %s",
            (doc_id,),
        )
        row = cur.fetchone()
    return dict(row)


@router.delete("/api/editor/documents/{doc_id}")
def delete_document(doc_id: int, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] == "sealed":
            raise HTTPException(status_code=403, detail="已封存的文档不可删除，请先归档")

        # 检查是否已有已生成的 Issue
        cur.execute("SELECT COUNT(*) AS cnt FROM generated_issues WHERE req_doc_id = %s AND status = 'created'", (doc_id,))
        has_issues = cur.fetchone()["cnt"] > 0
        if has_issues:
            raise HTTPException(status_code=409, detail="该文档已生成 Issue，请先关闭对应 Issue 后再删除")

        cur.execute("DELETE FROM req_documents WHERE id = %s", (doc_id,))
    return {"ok": True, "deleted_id": doc_id}


@router.put("/api/editor/documents/{doc_id}/status")
def transition_status(
    doc_id: int,
    req: StatusTransitionRequest,
    authorization: Optional[str] = Header(None),
):
    _require_teacher(authorization)

    ALLOWED = {"draft", "reviewing", "sealed", "archived"}
    if req.status not in ALLOWED:
        raise HTTPException(status_code=422, detail=f"状态值无效，允许: {ALLOWED}")

    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status, title FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        current = doc["status"]
        target = req.status

        # 校验状态流转合法性
        VALID_TRANSITIONS = {
            "draft": {"reviewing", "sealed", "archived"},
            "reviewing": {"sealed", "draft"},
            "sealed": {"archived"},
            "archived": set(),
        }
        if target not in VALID_TRANSITIONS.get(current, set()):
            raise HTTPException(
                status_code=422,
                detail=f"不允许从 {current} 转换为 {target}",
            )

        cur.execute(
            "UPDATE req_documents SET status = %s WHERE id = %s",
            (target, doc_id),
        )

        # 进入审阅模式时发送通知
        if target == "reviewing":
            _notify_students_for_review(conn, doc_id, doc["title"])

    return {"ok": True, "status": target}


def _notify_students_for_review(conn, doc_id: int, doc_title: str):
    """向所有学生发送审阅通知。"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role = 'student' AND is_active = 1")
        students = cur.fetchall()
        for s in students:
            cur.execute(
                """INSERT INTO notifications (user_id, title, body, category, source_ref)
                   VALUES (%s, %s, %s, 'system', %s)""",
                (
                    s["id"],
                    f"需求文档待审阅：{doc_title}",
                    f"《{doc_title}》已发布审阅，请登录查看并提出意见。",
                    f"req_doc:{doc_id}",
                ),
            )
    except Exception:
        pass  # 通知失败不阻塞主流程


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@router.get("/api/editor/templates")
def list_templates(authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return PRESET_TEMPLATES


# ---------------------------------------------------------------------------
# Import external .md file
# ---------------------------------------------------------------------------


@router.post("/api/editor/import")
async def import_document(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    title: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    _require_teacher(authorization)

    raw = await file.read()
    try:
        content_md = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content_md = raw.decode("gbk")
        except Exception:
            raise HTTPException(status_code=422, detail="无法识别文件编码，请使用 UTF-8 或 GBK")

    if not content_md.strip():
        raise HTTPException(status_code=422, detail="文件内容为空")

    doc_title = title or os.path.splitext(file.filename)[0] if file.filename else "导入文档"

    teacher_payload = _require_teacher(authorization)
    teacher_id = teacher_payload.get("user_id", 0)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO req_documents (course_id, title, content_md, created_by)
               VALUES (%s, %s, %s, %s)""",
            (course_id, doc_title, content_md, teacher_id),
        )
        doc_id = cur.lastrowid
        cur.execute("SELECT id, course_id, title, status, version_no, updated_at FROM req_documents WHERE id = %s", (doc_id,))
        row = cur.fetchone()

    return {
        "ok": True,
        "document": dict(row),
        "size_bytes": len(raw),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@router.post("/api/editor/validate")
def validate_document(req: ValidateRequest, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return validate_markdown(req.content_md)


# ---------------------------------------------------------------------------
# Copilot suggestions
# ---------------------------------------------------------------------------


@router.post("/api/editor/suggestions")
def copilot_suggestions(req: SuggestionRequest, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    return get_suggestions(req.content_md, req.cursor_line)


# ---------------------------------------------------------------------------
# GitHub Issue generation
# ---------------------------------------------------------------------------


@router.post("/api/editor/documents/{doc_id}/generate-issues")
def generate_issues(
    doc_id: int,
    req: GenerateIssuesRequest,
    authorization: Optional[str] = Header(None),
):
    teacher = _require_teacher(authorization)
    teacher_id = teacher.get("user_id", 0)

    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, content_md, status, version_no FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 提取所有功能需求块
        all_features = extract_features(doc["content_md"])
        if not all_features:
            raise HTTPException(status_code=422, detail="文档中未检测到功能需求块（### F-xxx）")

        # 筛选用户选中的功能
        if req.selected_features:
            selected = [f for f in all_features if f["code"] in req.selected_features]
        else:
            selected = all_features

        if not selected:
            raise HTTPException(status_code=422, detail="没有匹配的功能需求")

        # 批量创建 Issues
        results = create_issues_batch(selected, doc["title"], doc["version_no"])

        # 记录到 generated_issues 表
        created = 0
        failed = 0
        for r in results:
            cur.execute(
                """INSERT INTO generated_issues (req_doc_id, feature_code, feature_title, github_issue_no, status, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                       github_issue_no = VALUES(github_issue_no),
                       status = VALUES(status)""",
                (doc_id, r["code"], r["title"], r.get("issue_number"), r["status"], teacher_id),
            )
            if r["status"] == "created":
                created += 1
            elif r["status"] == "failed":
                failed += 1

    return {
        "ok": True,
        "total": len(results),
        "created": created,
        "skipped": len(results) - created - failed,
        "failed": failed,
        "results": results,
    }


@router.get("/api/editor/documents/{doc_id}/issues")
def list_generated_issues(doc_id: int, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, feature_code, feature_title, github_issue_no, status, created_at
               FROM generated_issues
               WHERE req_doc_id = %s
               ORDER BY id""",
            (doc_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Review / Comments
# ---------------------------------------------------------------------------


@router.get("/api/editor/documents/{doc_id}/review")
def student_review_document(
    doc_id: int,
    authorization: Optional[str] = Header(None),
):
    """学生审阅模式：获取文档内容（仅 reviewing 状态可访问）。"""
    student = _require_student(authorization)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, course_id, title, content_md, status, version_no, updated_at FROM req_documents WHERE id = %s",
            (doc_id,),
        )
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] != "reviewing":
            raise HTTPException(status_code=403, detail="文档未开放审阅")

    return dict(doc)


@router.post("/api/editor/documents/{doc_id}/comments")
def add_comment(
    doc_id: int,
    req: AddCommentRequest,
    authorization: Optional[str] = Header(None),
):
    """学生对文档添加评论（学生审阅模式），教师也可添加。"""
    # 先尝试学生认证
    is_student = False
    user_id = None
    try:
        student = _require_student(authorization)
        is_student = True
        # 学生 JWT 中的 student_id 是学号字符串，需要通过 users.student_no 查找 user_id
        student_no = student.get("student_id", "")
        with db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE student_no = %s AND role = 'student'", (student_no,))
            user_row = cur.fetchone()
            if not user_row:
                raise HTTPException(status_code=404, detail="用户不存在")
            user_id = user_row["id"]
    except HTTPException:
        # 教师认证
        teacher = _require_teacher(authorization)
        user_id = teacher.get("user_id", 0)

    if not user_id:
        raise HTTPException(status_code=401, detail="认证失败")

    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] != "reviewing":
            raise HTTPException(status_code=403, detail="文档未开放评论（需先进入审阅状态）")

        cur.execute(
            """INSERT INTO feedbacks (student_user_id, teacher_user_id, source_type, source_id, content)
               VALUES (%s, %s, 'manual', %s, %s)""",
            (user_id, user_id, doc_id, req.content),
        )
        comment_id = cur.lastrowid

    return {"ok": True, "comment_id": comment_id}


@router.get("/api/editor/documents/{doc_id}/comments")
def list_comments(doc_id: int, authorization: Optional[str] = Header(None)):
    """列出文档的评论（教师看全部，学生看自己的）。"""
    _require_teacher(authorization)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT f.id, f.student_user_id, f.content, f.created_at,
                      u.full_name AS author_name
               FROM feedbacks f
               JOIN users u ON u.id = f.student_user_id
               WHERE f.source_id = %s AND f.source_type = 'manual'
               ORDER BY f.created_at ASC""",
            (doc_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.put("/api/editor/comments/{comment_id}")
def respond_to_comment(
    comment_id: int,
    req: TeacherCommentResponse,
    authorization: Optional[str] = Header(None),
):
    """教师回复/确认评论。"""
    _require_teacher(authorization)

    ALLOWED = {"confirmed", "dismissed"}
    if req.status not in ALLOWED:
        raise HTTPException(status_code=422, detail=f"状态值无效，允许: {ALLOWED}")

    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, content FROM feedbacks WHERE id = %s", (comment_id,))
        comment = cur.fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 教师回复：在 content 后追加回复内容
        if req.teacher_response:
            new_content = comment["content"] + f"\n\n---\n**教师回复**：{req.teacher_response}"
            cur.execute(
                "UPDATE feedbacks SET content = %s WHERE id = %s",
                (new_content, comment_id),
            )

    return {"ok": True, "status": req.status}


# ---------------------------------------------------------------------------
# Student review login — simpler flow for review mode access
# ---------------------------------------------------------------------------

class StudentReviewLoginRequest(BaseModel):
    student_id: str


@router.post("/api/editor/student-login")
def student_review_login(req: StudentReviewLoginRequest):
    """学生审阅模式登录：用学号获取 Token，无需 exam_id。"""
    student_id = req.student_id.strip()
    if not student_id:
        raise HTTPException(status_code=422, detail="学号不能为空")

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT u.id, u.full_name, u.student_no FROM users u WHERE u.student_no = %s AND u.role = 'student' AND u.is_active = 1",
            (student_id,),
        )
        user = cur.fetchone()
        if not user:
            # 也尝试查 students 表（SQLite）
            # 兼容旧数据
            raise HTTPException(status_code=403, detail="学号不在系统中，请联系教师确认")

    token = create_token({
        "role": "student",
        "student_id": student_id,
        "name": user["full_name"],
        "user_id": user["id"],
    }, expires_hours=4)

    return {
        "token": token,
        "name": user["full_name"],
        "student_id": student_id,
    }


@router.get("/api/editor/student/documents")
def list_reviewable_documents(authorization: Optional[str] = Header(None)):
    """学生端：列出可审阅的文档（status='reviewing' 的所有文档）。"""
    student = _require_student(authorization)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT d.id, d.course_id, d.title, d.status, d.version_no, d.updated_at,
                      c.name AS course_name, c.code AS course_code
               FROM req_documents d
               JOIN courses c ON c.id = d.course_id
               WHERE d.status = 'reviewing'
               ORDER BY d.updated_at DESC"""
        )
        rows = cur.fetchall()

    return {
        "student_name": student.get("name", ""),
        "student_id": student.get("student_id", ""),
        "documents": [dict(r) for r in rows],
    }


@router.get("/api/editor/student/documents/{doc_id}")
def student_view_document(doc_id: int, authorization: Optional[str] = Header(None)):
    """学生端：查看单个文档详情（含渲染所需内容）。"""
    student = _require_student(authorization)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT d.id, d.course_id, d.title, d.content_md, d.status, d.version_no,
                      d.updated_at, c.name AS course_name, c.code AS course_code
               FROM req_documents d
               JOIN courses c ON c.id = d.course_id
               WHERE d.id = %s""",
            (doc_id,),
        )
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] != "reviewing":
            raise HTTPException(status_code=403, detail="该文档当前未开放审阅")

    return dict(doc)


@router.post("/api/editor/student/documents/{doc_id}/comments")
def student_add_comment(
    doc_id: int,
    req: AddCommentRequest,
    authorization: Optional[str] = Header(None),
):
    """学生端：对文档添加评论。"""
    student = _require_student(authorization)
    student_no = student.get("student_id", "")

    with db() as conn:
        cur = conn.cursor()
        # 通过 student_no 查找 user_id
        cur.execute(
            "SELECT id, full_name FROM users WHERE student_no = %s AND role = 'student'",
            (student_no,),
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        user_id = user["id"]

        cur.execute("SELECT id, status FROM req_documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        if doc["status"] != "reviewing":
            raise HTTPException(status_code=403, detail="文档未开放审阅")

        cur.execute(
            """INSERT INTO feedbacks (student_user_id, teacher_user_id, source_type, source_id, content)
               VALUES (%s, %s, 'manual', %s, %s)""",
            (user_id, user_id, doc_id, req.content),
        )
        comment_id = cur.lastrowid

    return {
        "ok": True,
        "comment_id": comment_id,
        "author_name": user["full_name"],
    }
