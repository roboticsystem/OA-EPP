"""F-S-012 公告通知 — API 路由

提供通知模块的全部 REST API 端点：
- 教师端：创建/更新/删除/列表通知
- 学生端：获取通知列表/标记已读/全部已读/未读计数/分类统计
- 公开接口：无需登录的通知查询（查分页面使用）

数据库依赖：oaepp.models.notice 中的数据库连接和表模型
认证依赖：oaepp.auth 中的 token 验证
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel

router = APIRouter()

# ──────────────── 通知分类常量 ────────────────
VALID_CATEGORIES = ("announcement", "deadline", "grade", "system", "graded")


# ──────────────── 数据库连接 ────────────────

def _get_db():
    """获取数据库连接（延迟导入，避免循环依赖）"""
    from oaepp.models.notice import get_db_connection
    return get_db_connection()


def _get_user_id_by_student_no(conn, student_no: str) -> Optional[int]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE role = 'student' AND student_no = %s",
        (student_no,)
    )
    row = cur.fetchone()
    return row["id"] if row else None


def _get_unread_count(conn, user_id: int) -> int:
    """统计学生未读通知数"""
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0",
        (user_id,)
    )
    return cur.fetchone()["cnt"]


def _datetime_to_str(d: dict, *keys):
    """将 dict 中的 datetime 字段转为字符串"""
    for k in keys:
        if d.get(k):
            d[k] = d[k].strftime("%Y-%m-%d %H:%M:%S")


def _require_teacher(authorization: Optional[str]):
    """提取并验证教师 Bearer token"""
    from oaepp.auth import verify_teacher
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        verify_teacher(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")


def _get_student_from_token(authorization: Optional[str]) -> Optional[dict]:
    """解码学生 token，返回 {student_id, name}，失败返回 None"""
    from oaepp.auth import verify_student
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_student(token)
    except ValueError:
        return None


# ──────────────── 模型 ────────────────

class NotificationCreate(BaseModel):
    title: str
    content: str = ""
    category: str = "announcement"
    course_id: Optional[int] = None
    target_user_ids: Optional[list] = None  # 指定发给哪些学生


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


# ──────────────── 教师端 API ────────────────

@router.post("/api/teacher/notifications")
def create_notification(req: NotificationCreate, authorization: Optional[str] = Header(None)):
    """创建通知（广播：可指定课程范围或指定学生）"""
    _require_teacher(authorization)
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422,
                            detail=f"无效分类，可选值：{', '.join(VALID_CATEGORIES)}")

    conn = _get_db()
    try:
        cur = conn.cursor()

        # 防重复提交：检查最近 30 秒内是否已存在相同 title + category 的通知
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM notifications "
            "WHERE title = %s AND category = %s "
            "AND created_at >= NOW() - INTERVAL 30 SECOND",
            (req.title, req.category)
        )
        if cur.fetchone()["cnt"] > 0:
            raise HTTPException(
                status_code=409,
                detail="相同标题和分类的通知在 30 秒内已发送过，请勿重复提交"
            )

        # 确定目标学生列表
        if req.target_user_ids:
            student_ids = req.target_user_ids
        elif req.course_id:
            cur.execute(
                "SELECT DISTINCT e.student_user_id FROM enrollments e WHERE e.course_id = %s",
                (req.course_id,)
            )
            students = cur.fetchall()
            student_ids = [s["student_user_id"] for s in students]
        else:
            cur.execute("""
                SELECT DISTINCT e.student_user_id FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                WHERE c.status = 'open'
            """)
            students = cur.fetchall()
            student_ids = [s["student_user_id"] for s in students]

        if not student_ids:
            raise HTTPException(status_code=422, detail="没有目标学生，无法发送通知")

        # 批量插入通知（同批次使用统一 created_at）
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        notification_ids = []
        for uid in student_ids:
            cur.execute(
                "INSERT INTO notifications (user_id, title, body, category, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (uid, req.title, req.content, req.category, now_str)
            )
            notification_ids.append(cur.lastrowid)

        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "sent_count": len(notification_ids), "ids": notification_ids}


@router.put("/api/teacher/notifications/{nid}")
def update_notification(nid: int, req: NotificationUpdate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)

    updates = {}
    if req.title is not None:
        updates["title"] = req.title
    if req.content is not None:
        updates["body"] = req.content
    if req.category is not None:
        if req.category not in VALID_CATEGORIES:
            raise HTTPException(status_code=422, detail="无效分类")
        updates["category"] = req.category

    if not updates:
        raise HTTPException(status_code=422, detail="没有要更新的字段")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM notifications WHERE id = %s", (nid,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="通知不存在")

        parts = [f"{k} = %s" for k in updates]
        values = list(updates.values())
        cur.execute(
            f"UPDATE notifications SET {', '.join(parts)} WHERE id = %s",
            (*values, nid)
        )

        cur.execute("SELECT * FROM notifications WHERE id = %s", (nid,))
        row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    _datetime_to_str(row, "created_at")
    return row


@router.delete("/api/teacher/notifications/{nid}")
def delete_notification(nid: int, authorization: Optional[str] = Header(None)):
    """删除通知（按 title+category 批量删除所有学生的同一条通知）"""
    _require_teacher(authorization)
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, category FROM notifications WHERE id = %s",
            (nid,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="通知不存在")

        # 按 title+category 批量删除整组
        cur.execute(
            "DELETE FROM notifications WHERE title = %s AND category = %s",
            (row["title"], row["category"])
        )
        deleted_count = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "deleted_count": deleted_count}


@router.get("/api/teacher/notifications")
def teacher_list_notifications(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    _require_teacher(authorization)
    conditions = []
    params = []
    if category:
        conditions.append("n.category = %s")
        params.append(category)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = _get_db()
    try:
        cur = conn.cursor()
        # 按标题+分类分组计数
        cur.execute(
            f"SELECT COUNT(*) AS cnt FROM ("
            f"SELECT n.title, n.category "
            f"FROM notifications n{where} "
            f"GROUP BY n.title, n.category) AS g",
            params
        )
        total = cur.fetchone()["cnt"]

        # 按 title+category 分组，用子查询取代表行
        cur.execute(
            f"SELECT g.id, g.title, g.body, g.category, g.created_at, "
            f"g.total_students, g.read_count FROM ("
            f"SELECT MIN(n.id) AS id, ANY_VALUE(n.body) AS body, n.title, n.category, "
            f"MAX(n.created_at) AS created_at, COUNT(*) AS total_students, "
            f"SUM(CASE WHEN n.is_read=1 THEN 1 ELSE 0 END) AS read_count "
            f"FROM notifications n {where} "
            f"GROUP BY n.title, n.category "
            f"ORDER BY created_at DESC LIMIT %s OFFSET %s) AS g",
            (*params, page_size, (page - 1) * page_size)
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    result = []
    for r in rows:
        d = dict(r)
        _datetime_to_str(d, "created_at")
        result.append(d)

    return {"items": result, "total": total, "page": page, "page_size": page_size}


# ──────────────── 学生端 API ────────────────

@router.get("/api/notifications")
def student_list_notifications(
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    student = _get_student_from_token(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")

    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student["student_id"])
        if not user_id:
            raise HTTPException(status_code=404, detail="学生不存在")

        conditions = ["n.user_id = %s"]
        params = [user_id]
        if category:
            conditions.append("n.category = %s")
            params.append(category)
        if unread_only:
            conditions.append("n.is_read = 0")

        where = " WHERE " + " AND ".join(conditions)

        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) AS cnt FROM notifications n{where}", params)
        total = cur.fetchone()["cnt"]

        # 查询通知，关联 courses 获取课程名称
        cur.execute(
            f"SELECT n.*, c.name AS course_name "
            f"FROM notifications n "
            f"LEFT JOIN enrollments e ON n.user_id = e.student_user_id "
            f"LEFT JOIN courses c ON e.course_id = c.id "
            f"{where} "
            f"ORDER BY n.created_at DESC LIMIT %s OFFSET %s",
            (*params, page_size, (page - 1) * page_size)
        )
        rows = cur.fetchall()

        unread_count = _get_unread_count(conn, user_id)

        # 按分类统计
        cur.execute(
            "SELECT category, COUNT(*) AS cnt FROM notifications "
            "WHERE user_id = %s GROUP BY category",
            (user_id,)
        )
        category_counts = {r["category"]: r["cnt"] for r in cur.fetchall()}
        for cat in ("announcement", "deadline", "grade"):
            if cat not in category_counts:
                category_counts[cat] = 0
    finally:
        conn.close()

    now = datetime.now()
    items = []
    for r in rows:
        d = dict(r)
        d["content"] = d.pop("body", "")
        d["is_read"] = bool(d.get("is_read", 0))
        _datetime_to_str(d, "created_at")
        d["course_name"] = d.get("course_name") or ""

        # 优先级推断
        cat = d.get("category", "")
        if cat == "deadline":
            created = d.get("created_at")
            if created and not d["is_read"]:
                try:
                    ct = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                    if (now - ct).days <= 3:
                        d["priority"] = "urgent"
                    else:
                        d["priority"] = "important"
                except Exception:
                    d["priority"] = "important"
            else:
                d["priority"] = "important"
        elif cat == "grade":
            d["priority"] = "important"
        elif cat == "announcement" and not d["is_read"]:
            d["priority"] = "normal"
        else:
            d["priority"] = "normal"
        items.append(d)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": unread_count,
        "category_counts": category_counts
    }


@router.post("/api/notifications/{nid}/read")
def mark_notification_read(nid: int, authorization: Optional[str] = Header(None)):
    student = _get_student_from_token(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")

    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student["student_id"])
        if not user_id:
            raise HTTPException(status_code=404, detail="学生不存在")

        cur = conn.cursor()
        cur.execute("SELECT id FROM notifications WHERE id = %s AND user_id = %s", (nid, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="通知不存在")

        cur.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (nid,))
        unread_count = _get_unread_count(conn, user_id)
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "unread_count": unread_count}


@router.post("/api/notifications/read-all")
def mark_all_read(authorization: Optional[str] = Header(None)):
    student = _get_student_from_token(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")

    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student["student_id"])
        if not user_id:
            raise HTTPException(status_code=404, detail="学生不存在")

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0", (user_id,))
        unread_cnt = cur.fetchone()["cnt"]

        cur.execute("UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0", (user_id,))
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "marked_count": unread_cnt, "unread_count": 0}


@router.get("/api/notifications/unread-count")
def get_unread_count(authorization: Optional[str] = Header(None)):
    student = _get_student_from_token(authorization)
    if not student:
        return {"unread_count": 0, "category_counts": {}}

    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student["student_id"])
        if not user_id:
            return {"unread_count": 0, "category_counts": {}}
        unread_count = _get_unread_count(conn, user_id)

        cur = conn.cursor()
        cur.execute(
            "SELECT category, COUNT(*) AS cnt FROM notifications "
            "WHERE user_id = %s GROUP BY category",
            (user_id,)
        )
        category_counts = {r["category"]: r["cnt"] for r in cur.fetchall()}
        for cat in ("announcement", "deadline", "grade"):
            if cat not in category_counts:
                category_counts[cat] = 0
    finally:
        conn.close()

    return {"unread_count": unread_count, "category_counts": category_counts}


@router.get("/api/notifications/category-stats")
def get_category_stats(authorization: Optional[str] = Header(None)):
    """获取各分类通知数量（供标签页显示）"""
    student = _get_student_from_token(authorization)
    if not student:
        return {"category_counts": {}}

    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student["student_id"])
        if not user_id:
            return {"category_counts": {}}

        cur = conn.cursor()
        cur.execute(
            "SELECT category, COUNT(*) AS cnt FROM notifications "
            "WHERE user_id = %s GROUP BY category",
            (user_id,)
        )
        category_counts = {r["category"]: r["cnt"] for r in cur.fetchall()}
        result = {}
        for cat in ("announcement", "deadline", "grade"):
            result[cat] = category_counts.get(cat, 0)
        result["all"] = sum(result.values())
    finally:
        conn.close()

    return {"category_counts": result}


# ──────────────── 公开 API（学生查分页面使用，无需 token）───────────────

@router.get("/api/public/notifications")
def public_list_notifications(
    student_id: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """公开接口：通过学号获取通知列表（按 title+category 分组去重）"""
    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student_id)
        if not user_id:
            return {"items": [], "total": 0, "unread_count": 0}

        cur = conn.cursor()
        # 按标题+分类分组计数
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM ("
            "SELECT n.title, n.category "
            "FROM notifications n WHERE n.user_id = %s "
            "GROUP BY n.title, n.category) AS g",
            (user_id,)
        )
        total = cur.fetchone()["cnt"]

        # 按 title+category 分组查询，取每组最新的一条代表
        cur.execute(
            "SELECT id, body, title, category, created_at, "
            "(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) > 0 AS any_read "
            "FROM ("
            "  SELECT n.id, n.body, n.title, n.category, "
            "         n.created_at, n.is_read, "
            "         ROW_NUMBER() OVER ("
            "             PARTITION BY n.title, n.category "
            "             ORDER BY n.created_at DESC"
            "         ) AS rn "
            "  FROM notifications n WHERE n.user_id = %s"
            ") ranked "
            "WHERE rn <= %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (user_id, 50, page_size, (page - 1) * page_size)
        )
        rows = cur.fetchall()

        unread_count = _get_unread_count(conn, user_id)
    finally:
        conn.close()

    items = []
    for r in rows:
        d = dict(r)
        d["content"] = d.pop("body", "")
        d["is_read"] = bool(d.get("any_read", 0))
        _datetime_to_str(d, "created_at")
        items.append(d)

    return {"items": items, "total": total, "unread_count": unread_count}


@router.get("/api/public/notifications/unread-count")
def public_unread_count(student_id: str = Query(..., min_length=1)):
    """公开接口：通过学号获取未读通知数"""
    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student_id)
        if not user_id:
            return {"unread_count": 0}
        unread_count = _get_unread_count(conn, user_id)
    finally:
        conn.close()
    return {"unread_count": unread_count}


@router.post("/api/public/notifications/{nid}/read")
def public_mark_read(nid: int, student_id: str = Query(..., min_length=1)):
    """公开接口：标记通知为已读（按 title+category 批量标记该组所有记录）"""
    conn = _get_db()
    try:
        user_id = _get_user_id_by_student_no(conn, student_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="学生不存在")

        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, category FROM notifications WHERE id = %s AND user_id = %s",
            (nid, user_id)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="通知不存在")

        # 按 title+category 批量标记该组全部为已读
        cur.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND title = %s AND category = %s",
            (user_id, row["title"], row["category"])
        )
        unread_count = _get_unread_count(conn, user_id)
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "unread_count": unread_count}
