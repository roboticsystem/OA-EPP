"""OA-EPP 通知模块 — 数据模型与 DAO 层

提供 notifications 表的数据访问，依赖 oaepp.database 获取连接。
"""
import logging
from typing import Optional, Dict, Any

try:
    from oaepp.database import get_db, init_table
except ModuleNotFoundError:
    from database import get_db, init_table

logger = logging.getLogger("oaepp.notice")


# ── 常量 ──────────────────────────────────────────────────────

VALID_CATEGORIES = ("announcement", "deadline", "grade", "system", "graded")


# ── 建表 ──────────────────────────────────────────────────────

CREATE_NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    category VARCHAR(32) NOT NULL DEFAULT 'announcement',
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_category (category),
    INDEX idx_is_read (is_read),
    INDEX idx_title_category (title, category),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def init_db():
    """初始化通知表（应用启动时调用）"""
    init_table("notifications", CREATE_NOTIFICATIONS_TABLE)


# ── DAO 层 ───────────────────────────────────────────────────

def get_user_id_by_student_no(conn, student_no: str) -> Optional[int]:
    """通过学号查找学生 user_id"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM users WHERE role = 'student' AND student_no = %s",
            (student_no,),
        )
        row = cur.fetchone()
        return row["id"] if row else None


def get_unread_count(conn, user_id: int) -> int:
    """统计学生未读通知数"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )
        return cur.fetchone()["cnt"]


def get_category_counts(conn, user_id: int) -> Dict[str, int]:
    """统计各分类通知数量（覆盖全部 VALID_CATEGORIES）"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT category, COUNT(*) AS cnt FROM notifications "
            "WHERE user_id = %s GROUP BY category",
            (user_id,),
        )
        counts = {r["category"]: r["cnt"] for r in cur.fetchall()}
        for cat in VALID_CATEGORIES:
            if cat not in counts:
                counts[cat] = 0
        return counts


def _row_to_dict(row: Optional[Dict], datetime_fields=("created_at",)) -> Optional[Dict]:
    """将查询行转为 dict，并序列化 datetime 字段"""
    if row is None:
        return None
    d = dict(row)
    for k in datetime_fields:
        val = d.get(k)
        if val:
            d[k] = val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(val, "strftime") else str(val)
    return d
