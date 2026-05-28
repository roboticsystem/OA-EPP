from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import require_teacher, get_student_from_token

router = APIRouter()

# ──────────────── 通知分类 & 优先级常量 ────────────────
VALID_CATEGORIES = ("announcement", "deadline", "grade")
VALID_PRIORITIES = ("normal", "important", "urgent")

# ──────────────── 辅助 ────────────────

def _get_unread_count(conn, student_id: str) -> int:
    """统计学生未读通知数"""
    return conn.execute("""
        SELECT COUNT(*) FROM notifications n
        LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
        WHERE n.is_published = 1
          AND (n.target_role = 'all' OR n.target_student_id = ?)
          AND nr.id IS NULL
    """, (student_id, student_id)).fetchone()[0]


def _row_to_dict(row) -> dict:
    return dict(row)


# ──────────────── 模型 ────────────────

class NotificationCreate(BaseModel):
    title: str
    content: str = ""
    category: str = "announcement"
    priority: str = "normal"
    target_role: str = "all"
    target_student_id: Optional[str] = None
    course_name: str = ""


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    target_role: Optional[str] = None
    target_student_id: Optional[str] = None
    course_name: Optional[str] = None
    is_published: Optional[int] = None


# ──────────────── 教师端 API ────────────────

@router.post("/api/teacher/notifications")
def create_notification(req: NotificationCreate, authorization: Optional[str] = Header(None)):
    require_teacher(authorization)
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"无效分类，可选值：{', '.join(VALID_CATEGORIES)}")
    if req.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"无效优先级，可选值：{', '.join(VALID_PRIORITIES)}")

    with db() as conn:
        cursor = conn.execute("""
            INSERT INTO notifications (title, content, category, priority, target_role, target_student_id, course_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (req.title, req.content, req.category, req.priority,
              req.target_role, req.target_student_id, req.course_name))
        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_dict(row)


@router.put("/api/teacher/notifications/{nid}")
def update_notification(nid: int, req: NotificationUpdate, authorization: Optional[str] = Header(None)):
    require_teacher(authorization)

    allowed_fields = ("title", "content", "category", "priority", "target_role",
                      "target_student_id", "course_name", "is_published")
    updates = {f: getattr(req, f) for f in allowed_fields if getattr(req, f, None) is not None}

    if "category" in updates and updates["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"无效分类")
    if "priority" in updates and updates["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"无效优先级")

    with db() as conn:
        existing = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="通知不存在")

        if updates:
            parts = [f"{k} = ?" for k in updates]
            values = list(updates.values())
            parts.append("updated_at = datetime('now','localtime')")
            conn.execute(
                f"UPDATE notifications SET {', '.join(parts)} WHERE id = ?",
                (*values, nid)
            )

        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
    return _row_to_dict(row)


@router.delete("/api/teacher/notifications/{nid}")
def delete_notification(nid: int, authorization: Optional[str] = Header(None)):
    require_teacher(authorization)
    with db() as conn:
        existing = conn.execute("SELECT id FROM notifications WHERE id = ?", (nid,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="通知不存在")
        conn.execute("DELETE FROM notification_reads WHERE notification_id = ?", (nid,))
        conn.execute("DELETE FROM notifications WHERE id = ?", (nid,))
    return {"ok": True}


@router.get("/api/teacher/notifications")
def teacher_list_notifications(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    require_teacher(authorization)
    conditions = []
    params = []
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    with db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM notifications{where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM notifications{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*params, page_size, (page - 1) * page_size)
        ).fetchall()

        # 统计每个通知的已读人数
        nids = [r["id"] for r in rows]
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        read_counts = {}
        if nids:
            placeholders = ",".join("?" for _ in nids)
            read_rows = conn.execute(
                f"SELECT notification_id, COUNT(*) as cnt FROM notification_reads WHERE notification_id IN ({placeholders}) GROUP BY notification_id",
                nids
            ).fetchall()
            read_counts = {r["notification_id"]: r["cnt"] for r in read_rows}

    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["read_count"] = read_counts.get(d["id"], 0)
        d["total_students"] = total_students
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
    student = get_student_from_token(authorization)
    sid = student["student_id"] if student else None

    # 构建 WHERE 条件（参数化）
    conditions = ["n.is_published = 1"]
    params = []
    if sid:
        conditions.append("(n.target_role = 'all' OR n.target_student_id = ?)")
        params.append(sid)
    else:
        conditions.append("n.target_role = 'all'")

    if category:
        conditions.append("n.category = ?")
        params.append(category)

    if unread_only and sid:
        conditions.append("nr.id IS NULL")

    where = " WHERE " + " AND ".join(conditions)

    with db() as conn:
        base_params = [sid or "", *params]
        total = conn.execute(
            f"SELECT COUNT(*) FROM notifications n LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?{where}",
            base_params
        ).fetchone()[0]

        rows = conn.execute(
            f"""SELECT n.*, nr.id AS is_read_flag
               FROM notifications n
               LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
               {where}
               ORDER BY
                   CASE WHEN nr.id IS NULL THEN 0 ELSE 1 END,
                   CASE n.priority WHEN 'urgent' THEN 0 WHEN 'important' THEN 1 ELSE 2 END,
                   n.created_at DESC
               LIMIT ? OFFSET ?""",
            (*base_params, page_size, (page - 1) * page_size)
        ).fetchall()

        unread_count = _get_unread_count(conn, sid) if sid else 0

    items = []
    for r in rows:
        d = _row_to_dict(r)
        d["is_read"] = d.pop("is_read_flag") is not None
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size, "unread_count": unread_count}


@router.post("/api/notifications/{nid}/read")
def mark_notification_read(nid: int, authorization: Optional[str] = Header(None)):
    student = get_student_from_token(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")
    sid = student["student_id"]

    with db() as conn:
        n = conn.execute("SELECT id FROM notifications WHERE id = ? AND is_published = 1", (nid,)).fetchone()
        if not n:
            raise HTTPException(status_code=404, detail="通知不存在")

        conn.execute(
            "INSERT OR IGNORE INTO notification_reads (notification_id, student_id) VALUES (?, ?)",
            (nid, sid)
        )
        unread_count = _get_unread_count(conn, sid)

    return {"ok": True, "unread_count": unread_count}


@router.post("/api/notifications/read-all")
def mark_all_read(authorization: Optional[str] = Header(None)):
    student = get_student_from_token(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")
    sid = student["student_id"]

    with db() as conn:
        unread = conn.execute("""
            SELECT n.id FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            WHERE n.is_published = 1 AND (n.target_role = 'all' OR n.target_student_id = ?)
              AND nr.id IS NULL
        """, (sid, sid)).fetchall()

        conn.executemany(
            "INSERT OR IGNORE INTO notification_reads (notification_id, student_id) VALUES (?, ?)",
            [(u["id"], sid) for u in unread]
        )

    return {"ok": True, "marked_count": len(unread), "unread_count": 0}


@router.get("/api/notifications/unread-count")
def get_unread_count(authorization: Optional[str] = Header(None)):
    student = get_student_from_token(authorization)
    if not student:
        return {"unread_count": 0}
    sid = student["student_id"]

    with db() as conn:
        unread_count = _get_unread_count(conn, sid)

    return {"unread_count": unread_count}
