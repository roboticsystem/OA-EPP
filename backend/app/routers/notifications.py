from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from app.database import db
from app.auth_utils import verify_teacher_token, verify_student_token

router = APIRouter()


# ──────────────────── 辅助 ────────────────────
def _require_teacher(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_teacher_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _get_student(authorization: Optional[str]):
    """解码学生 token，返回 {student_id, name}，失败返回 None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_student_token(token)
    except ValueError:
        return None


# ──────────────────── 模型 ────────────────────
class NotificationCreate(BaseModel):
    title: str
    content: str = ""
    category: str = "announcement"  # announcement / deadline / grade
    priority: str = "normal"        # normal / important / urgent
    target_role: str = "all"        # all / student / teacher
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


# ──────────────────── 教师端 API ────────────────────

@router.post("/api/teacher/notifications")
def create_notification(req: NotificationCreate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        cursor = conn.execute("""
            INSERT INTO notifications (title, content, category, priority, target_role, target_student_id, course_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (req.title, req.content, req.category, req.priority,
              req.target_role, req.target_student_id, req.course_name))
        nid = cursor.lastrowid
        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
    return dict(row)


@router.put("/api/teacher/notifications/{nid}")
def update_notification(nid: int, req: NotificationUpdate, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
    with db() as conn:
        existing = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="通知不存在")

        updates = {}
        for field in ("title", "content", "category", "priority", "target_role",
                       "target_student_id", "course_name", "is_published"):
            val = getattr(req, field, None)
            if val is not None:
                updates[field] = val

        if updates:
            updates["updated_at"] = "datetime('now','localtime')"
            set_clause = ", ".join(
                f"{k} = {'datetime(\\'now\\',\\'localtime\\')' if k == 'updated_at' else '?'}"
                for k in updates
            )
            values = [updates[k] for k in updates if k != "updated_at"]
            conn.execute(f"UPDATE notifications SET {set_clause} WHERE id = ?", (*values, nid))

        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
    return dict(row)


@router.delete("/api/teacher/notifications/{nid}")
def delete_notification(nid: int, authorization: Optional[str] = Header(None)):
    _require_teacher(authorization)
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
    _require_teacher(authorization)
    where = "WHERE 1=1"
    params = []
    if category:
        where += " AND category = ?"
        params.append(category)

    with db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM notifications {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM notifications {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*params, page_size, (page - 1) * page_size)
        ).fetchall()

        # 统计每个通知的已读人数
        nids = [r["id"] for r in rows]
        read_counts = {}
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if nids:
            placeholders = ",".join("?" for _ in nids)
            read_rows = conn.execute(
                f"SELECT notification_id, COUNT(*) as cnt FROM notification_reads WHERE notification_id IN ({placeholders}) GROUP BY notification_id",
                nids
            ).fetchall()
            read_counts = {r["notification_id"]: r["cnt"] for r in read_rows}

    result = []
    for r in rows:
        d = dict(r)
        d["read_count"] = read_counts.get(d["id"], 0)
        d["total_students"] = total_students
        result.append(d)

    return {"items": result, "total": total, "page": page, "page_size": page_size}


# ──────────────────── 学生端 API ────────────────────

@router.get("/api/notifications")
def student_list_notifications(
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    student = _get_student(authorization)
    sid = student["student_id"] if student else None

    where = "WHERE n.is_published = 1 AND (n.target_role = 'all'"
    params = []
    if sid:
        where += " OR n.target_student_id = ?"
        params.append(sid)
    where += ")"

    if category:
        where += " AND n.category = ?"
        params.append(category)

    if unread_only and sid:
        where += " AND nr.id IS NULL"

    with db() as conn:
        total = conn.execute(f"""
            SELECT COUNT(*) FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            {where}
        """, (sid or "", *params)).fetchone()[0]

        rows = conn.execute(f"""
            SELECT n.*, nr.id AS is_read_flag
            FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            {where}
            ORDER BY
                CASE WHEN nr.id IS NULL THEN 0 ELSE 1 END,
                CASE n.priority
                    WHEN 'urgent' THEN 0
                    WHEN 'important' THEN 1
                    ELSE 2
                END,
                n.created_at DESC
            LIMIT ? OFFSET ?
        """, (sid or "", *params, page_size, (page - 1) * page_size)).fetchall()

        # 统计总未读数
        unread_count = conn.execute(f"""
            SELECT COUNT(*) FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            WHERE n.is_published = 1 AND (n.target_role = 'all' OR n.target_student_id = ?)
              AND nr.id IS NULL
        """, (sid or "", sid or "")).fetchone()[0]

    items = []
    for r in rows:
        d = dict(r)
        d["is_read"] = d.pop("is_read_flag") is not None
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size, "unread_count": unread_count}


@router.post("/api/notifications/{nid}/read")
def mark_notification_read(nid: int, authorization: Optional[str] = Header(None)):
    student = _get_student(authorization)
    if not student:
        raise HTTPException(status_code=401, detail="请先登录")
    sid = student["student_id"]

    with db() as conn:
        n = conn.execute("SELECT id FROM notifications WHERE id = ? AND is_published = 1", (nid,)).fetchone()
        if not n:
            raise HTTPException(status_code=404, detail="通知不存在")

        conn.execute("""
            INSERT OR IGNORE INTO notification_reads (notification_id, student_id)
            VALUES (?, ?)
        """, (nid, sid))

        # 返回最新未读数
        unread_count = conn.execute("""
            SELECT COUNT(*) FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            WHERE n.is_published = 1 AND (n.target_role = 'all' OR n.target_student_id = ?)
              AND nr.id IS NULL
        """, (sid, sid)).fetchone()[0]

    return {"ok": True, "unread_count": unread_count}


@router.post("/api/notifications/read-all")
def mark_all_read(authorization: Optional[str] = Header(None)):
    student = _get_student(authorization)
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

        for u in unread:
            conn.execute("""
                INSERT OR IGNORE INTO notification_reads (notification_id, student_id)
                VALUES (?, ?)
            """, (u["id"], sid))

    return {"ok": True, "marked_count": len(unread), "unread_count": 0}


@router.get("/api/notifications/unread-count")
def get_unread_count(authorization: Optional[str] = Header(None)):
    student = _get_student(authorization)
    if not student:
        return {"unread_count": 0}
    sid = student["student_id"]

    with db() as conn:
        unread_count = conn.execute("""
            SELECT COUNT(*) FROM notifications n
            LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
            WHERE n.is_published = 1 AND (n.target_role = 'all' OR n.target_student_id = ?)
              AND nr.id IS NULL
        """, (sid, sid)).fetchone()[0]

    return {"unread_count": unread_count}
