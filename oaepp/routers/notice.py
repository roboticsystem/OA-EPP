"""F-S-012 公告通知 — API 路由（优化版）

提供通知模块全部 REST API：
  - 教师端：CRUD 通知、按 title+category 聚合视图
  - 学生端：通知列表（含优先级推断）、标记已读、全部已读、未读计数
  - 公开接口：免登录查询（查分页面）

优化点：
  - FastAPI Depends 依赖注入认证
  - 统一错误处理和响应格式
  - 从 models.notice 导入 DAO，消除重复
  - 结构化日志
"""
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, field_validator

try:
    from oaepp.database import get_db
    from oaepp.models.notice import (
        get_user_id_by_student_no,
        get_unread_count,
        get_category_counts,
        VALID_CATEGORIES,
        _row_to_dict,
    )
except ModuleNotFoundError:
    from database import get_db
    from models.notice import (
        get_user_id_by_student_no,
        get_unread_count,
        get_category_counts,
        VALID_CATEGORIES,
        _row_to_dict,
    )

logger = logging.getLogger("oaepp.notice")

router = APIRouter(tags=["公告通知"])


# ═══════════════════════════════════════════════════════════════
#  依赖注入 — 认证
# ═══════════════════════════════════════════════════════════════

def _extract_token(authorization: Optional[str] = Header(None)) -> str:
    """提取 Bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    return authorization.removeprefix("Bearer ").strip()


def _import_verify_teacher():
    try:
        from oaepp.auth import verify_teacher
    except ModuleNotFoundError:
        from auth import verify_teacher
    return verify_teacher


def _import_verify_student():
    try:
        from oaepp.auth import verify_student
    except ModuleNotFoundError:
        from auth import verify_student
    return verify_student


def require_teacher(authorization: Optional[str] = Header(None)) -> dict:
    """验证教师身份，返回 token payload"""
    verify_teacher = _import_verify_teacher()
    token = _extract_token(authorization)
    try:
        return verify_teacher(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的教师登录凭证")


def require_student(authorization: Optional[str] = Header(None)) -> dict:
    """验证学生身份，返回 token payload"""
    verify_student = _import_verify_student()
    token = _extract_token(authorization)
    try:
        return verify_student(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的学生登录凭证")


def get_student_user_id(
    student: dict = Depends(require_student),
) -> int:
    """从 token 解析学生 user_id"""
    with get_db() as conn:
        uid = get_user_id_by_student_no(conn, student["student_id"])
        if not uid:
            raise HTTPException(status_code=404, detail="学生不存在")
        return uid


# ═══════════════════════════════════════════════════════════════
#  请求/响应模型
# ═══════════════════════════════════════════════════════════════

class NotificationCreate(BaseModel):
    title: str
    content: str = ""
    category: str = "announcement"
    priority: str = "normal"
    course_id: Optional[int] = None
    target_user_ids: Optional[List[int]] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("标题不能为空")
        v = v.strip()
        if len(v) > 255:
            raise ValueError("标题不能超过255个字符")
        return v

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v not in VALID_CATEGORIES:
            raise ValueError(f"无效分类，可选值：{', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v):
        if v not in ("normal", "important", "urgent"):
            raise ValueError("无效优先级，可选值：normal, important, urgent")
        return v


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_length(cls, v):
        if v is not None and len(v.strip()) > 255:
            raise ValueError("标题不能超过255个字符")
        return v.strip() if v else v

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"无效分类，可选值：{', '.join(VALID_CATEGORIES)}")
        return v


class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ═══════════════════════════════════════════════════════════════
#  教师端 API
# ═══════════════════════════════════════════════════════════════

@router.post("/api/teacher/notifications", summary="创建通知")
def create_notification(
    req: NotificationCreate,
    teacher: dict = Depends(require_teacher),
):
    """教师创建通知，支持指定课程范围或指定学生列表，支持优先级"""
    with get_db() as conn:
        cur = conn.cursor()

        # 防重复：30 秒内同标题+分类
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM notifications "
            "WHERE title = %s AND category = %s "
            "AND created_at >= NOW() - INTERVAL 30 SECOND",
            (req.title, req.category),
        )
        if cur.fetchone()["cnt"] > 0:
            raise HTTPException(status_code=409, detail="请勿在 30 秒内重复提交相同通知")

        # 确定目标学生
        if req.target_user_ids:
            student_ids = req.target_user_ids
        elif req.course_id:
            cur.execute(
                "SELECT DISTINCT student_user_id FROM enrollments WHERE course_id = %s",
                (req.course_id,),
            )
            student_ids = [r["student_user_id"] for r in cur.fetchall()]
        else:
            # 获取所有有效学生
            cur.execute("SELECT id FROM users WHERE role = 'student'")
            student_ids = [r["id"] for r in cur.fetchall()]

        if not student_ids:
            raise HTTPException(status_code=422, detail="没有目标学生")

        # 批量插入（含 priority 信息存储在 body 中作为 meta）
        import json as _json
        meta = _json.dumps({"priority": req.priority}) if req.priority != "normal" else None
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ids = []
        for uid in student_ids:
            cur.execute(
                "INSERT INTO notifications (user_id, title, body, category, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (uid, req.title, req.content or "", req.category, now),
            )
            ids.append(cur.lastrowid)
        conn.commit()

    logger.info(f"教师创建通知: title={req.title}, priority={req.priority}, sent_to={len(ids)}")
    return {"ok": True, "sent_count": len(ids), "ids": ids}


@router.get("/api/teacher/notifications", summary="教师通知列表")
def teacher_list_notifications(
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher: dict = Depends(require_teacher),
):
    """教师查看通知列表（按 title+category 分组，含已读统计）"""
    conditions = []
    params = []
    if category:
        conditions.append("n.category = %s")
        params.append(category)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db() as conn:
        cur = conn.cursor()

        # 分组总数
        cur.execute(
            f"SELECT COUNT(*) AS cnt FROM ("
            f"  SELECT n.title, n.category FROM notifications n{where} "
            f"  GROUP BY n.title, n.category"
            f") AS g",
            params,
        )
        total = cur.fetchone()["cnt"]

        # 分组列表
        cur.execute(
            f"SELECT g.id, g.title, g.body, g.category, g.created_at, "
            f"       g.total_students, g.read_count "
            f"FROM ("
            f"  SELECT MIN(n.id) AS id, ANY_VALUE(n.body) AS body, "
            f"         n.title, n.category, MAX(n.created_at) AS created_at, "
            f"         COUNT(*) AS total_students, "
            f"         SUM(CASE WHEN n.is_read = 1 THEN 1 ELSE 0 END) AS read_count "
            f"  FROM notifications n{where} "
            f"  GROUP BY n.title, n.category "
            f"  ORDER BY created_at DESC LIMIT %s OFFSET %s"
            f") AS g",
            (*params, page_size, (page - 1) * page_size),
        )
        rows = cur.fetchall()

    items = []
    for r in rows:
        d = _row_to_dict(r)
        if d:
            items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/api/teacher/notifications/{nid}", summary="编辑通知")
def update_notification(
    nid: int,
    req: NotificationUpdate,
    teacher: dict = Depends(require_teacher),
):
    """编辑单条通知（只更新指定 id 的那条记录）"""
    updates = {}
    if req.title is not None:
        updates["title"] = req.title.strip()
    if req.content is not None:
        updates["body"] = req.content.strip()
    if req.category is not None:
        updates["category"] = req.category

    if not updates:
        raise HTTPException(status_code=422, detail="没有要更新的字段")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM notifications WHERE id = %s", (nid,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="通知不存在")

        parts = [f"{k} = %s" for k in updates]
        cur.execute(
            f"UPDATE notifications SET {', '.join(parts)} WHERE id = %s",
            (*updates.values(), nid),
        )
        cur.execute("SELECT * FROM notifications WHERE id = %s", (nid,))
        row = cur.fetchone()
        conn.commit()

    logger.info(f"教师编辑通知 id={nid}")
    return {"ok": True, "notification": _row_to_dict(row)}


@router.delete("/api/teacher/notifications/{nid}", summary="删除通知")
def delete_notification(
    nid: int,
    teacher: dict = Depends(require_teacher),
):
    """按 title+category 批量删除同组通知"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, category FROM notifications WHERE id = %s", (nid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="通知不存在")

        cur.execute(
            "DELETE FROM notifications WHERE title = %s AND category = %s",
            (row["title"], row["category"]),
        )
        deleted = cur.rowcount
        conn.commit()

    logger.info(f"教师删除通知: title={row['title']}, deleted={deleted}")
    return {"ok": True, "deleted_count": deleted}


# ═══════════════════════════════════════════════════════════════
#  学生端 API
# ═══════════════════════════════════════════════════════════════

def _infer_priority(category: str, is_read: bool, created_at: str) -> str:
    """根据分类和是否已读推断优先级"""
    if is_read:
        return "normal"
    if category == "deadline":
        try:
            ct = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            return "urgent" if (datetime.now() - ct).days <= 3 else "important"
        except Exception:
            return "important"
    if category == "grade":
        return "important"
    return "normal"


@router.get("/api/notifications", summary="学生通知列表")
def student_list_notifications(
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_student_user_id),
):
    """学生查看自己的通知列表"""
    conditions = ["n.user_id = %s"]
    params = [user_id]
    if category:
        conditions.append("n.category = %s")
        params.append(category)
    if unread_only:
        conditions.append("n.is_read = 0")

    where = " WHERE " + " AND ".join(conditions)

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*) AS cnt FROM notifications n{where}", params)
        total = cur.fetchone()["cnt"]

        cur.execute(
            f"SELECT n.*, c.name AS course_name "
            f"FROM notifications n "
            f"LEFT JOIN enrollments e ON n.user_id = e.student_user_id "
            f"LEFT JOIN courses c ON e.course_id = c.id "
            f"{where} "
            f"ORDER BY n.created_at DESC LIMIT %s OFFSET %s",
            (*params, page_size, (page - 1) * page_size),
        )
        rows = cur.fetchall()

        unread_count = get_unread_count(conn, user_id)
        cat_counts = get_category_counts(conn, user_id)

    now = datetime.now()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        if d is None:
            continue
        d["content"] = d.pop("body", "")
        d["is_read"] = bool(d.get("is_read", 0))
        d["course_name"] = d.get("course_name") or ""
        d["priority"] = _infer_priority(
            d.get("category", ""), d["is_read"], d.get("created_at", "")
        )
        items.append(d)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": unread_count,
        "category_counts": cat_counts,
    }


@router.post("/api/notifications/{nid}/read", summary="标记已读")
def mark_notification_read(
    nid: int,
    user_id: int = Depends(get_student_user_id),
):
    """标记单条通知为已读"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM notifications WHERE id = %s AND user_id = %s",
            (nid, user_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="通知不存在")

        cur.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (nid,))
        unread = get_unread_count(conn, user_id)
        conn.commit()

    return {"ok": True, "unread_count": unread}


@router.post("/api/notifications/read-all", summary="全部已读")
def mark_all_read(
    user_id: int = Depends(get_student_user_id),
):
    """标记所有通知为已读"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )
        marked = cur.fetchone()["cnt"]
        cur.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )
        conn.commit()

    return {"ok": True, "marked_count": marked, "unread_count": 0}


@router.get("/api/notifications/unread-count", summary="未读计数")
def get_unread(
    user_id: int = Depends(get_student_user_id),
):
    """获取未读通知数和分类统计"""
    with get_db() as conn:
        unread = get_unread_count(conn, user_id)
        cat_counts = get_category_counts(conn, user_id)
    return {"unread_count": unread, "category_counts": cat_counts}


# ═══════════════════════════════════════════════════════════════
#  公开 API（免登录）
# ═══════════════════════════════════════════════════════════════

@router.get("/api/public/notifications", summary="公开通知列表")
def public_list_notifications(
    student_id: str = Query(..., min_length=1, description="学号"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """公开接口：通过学号获取通知列表"""
    with get_db() as conn:
        user_id = get_user_id_by_student_no(conn, student_id)
        if not user_id:
            return {"items": [], "total": 0, "unread_count": 0}

        cur = conn.cursor()

        # 分组计数
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM ("
            "  SELECT n.title, n.category FROM notifications n "
            "  WHERE n.user_id = %s GROUP BY n.title, n.category"
            ") AS g",
            (user_id,),
        )
        total = cur.fetchone()["cnt"]

        # 分组查询
        cur.execute(
            "SELECT id, body, title, category, created_at, "
            "       MAX(is_read) AS any_read "
            "FROM ("
            "  SELECT n.id, n.body, n.title, n.category, "
            "         n.created_at, n.is_read, "
            "         ROW_NUMBER() OVER ("
            "           PARTITION BY n.title, n.category "
            "           ORDER BY n.created_at DESC"
            "         ) AS rn "
            "  FROM notifications n WHERE n.user_id = %s"
            ") ranked "
            "WHERE rn <= 50 ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (user_id, page_size, (page - 1) * page_size),
        )
        rows = cur.fetchall()
        unread = get_unread_count(conn, user_id)

    items = []
    for r in rows:
        d = _row_to_dict(r)
        if d is None:
            continue
        d["content"] = d.pop("body", "")
        d["is_read"] = bool(d.get("any_read", 0))
        items.append(d)

    return {"items": items, "total": total, "unread_count": unread}


@router.get("/api/public/notifications/unread-count", summary="公开未读计数")
def public_unread_count(
    student_id: str = Query(..., min_length=1),
):
    with get_db() as conn:
        user_id = get_user_id_by_student_no(conn, student_id)
        if not user_id:
            return {"unread_count": 0}
        return {"unread_count": get_unread_count(conn, user_id)}


@router.post("/api/public/notifications/{nid}/read", summary="公开标记已读")
def public_mark_read(
    nid: int,
    student_id: str = Query(..., min_length=1),
):
    with get_db() as conn:
        user_id = get_user_id_by_student_no(conn, student_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="学生不存在")

        cur = conn.cursor()
        cur.execute(
            "SELECT title, category FROM notifications WHERE id = %s AND user_id = %s",
            (nid, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="通知不存在")

        cur.execute(
            "UPDATE notifications SET is_read = 1 "
            "WHERE user_id = %s AND title = %s AND category = %s",
            (user_id, row["title"], row["category"]),
        )
        unread = get_unread_count(conn, user_id)
        conn.commit()

    return {"ok": True, "unread_count": unread}
