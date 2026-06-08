"""F-S-012 公告通知 — NoticeState

提供公告通知的状态管理：
- notices: 通知列表，按发布时间降序
- unread_count: 未读通知计数
- load_notices(): 从数据库加载通知
- mark_as_read(): 标记通知为已读

依赖：
- oaepp.database: 统一数据库连接
"""
from typing import Any, List, Optional

try:
    from oaepp.database import get_db
except ModuleNotFoundError:
    from database import get_db


class NoticeState:
    """公告通知状态管理"""

    # ── 状态变量 ──
    notices: List[dict] = []
    unread_count: int = 0

    # ── 私有属性 ──
    _user_id: Optional[int] = None
    _db_session: Any = None

    def __init__(self):
        self.notices = []
        self.unread_count = 0

    # ── 事件处理器 ──

    async def load_notices(self, user_id: Optional[int] = None) -> None:
        """从数据库加载通知列表，按发布时间降序排列。

        Args:
            user_id: 可选，指定加载哪个用户的通知
        """
        self._user_id = user_id

        # 尝试从 conftest mem_db fixture 注入的 session 获取数据
        if hasattr(self, "_db_session") and self._db_session is not None:
            self._load_from_session(self._db_session)
        else:
            self._load_from_production()

        if not isinstance(self.notices, list):
            self.notices = []
        self._update_unread_count()

    def mark_as_read(self, notification_id: int) -> None:
        """标记指定通知为已读。

        Args:
            notification_id: 要标记的通知 ID
        """
        for n in self.notices:
            if n.get("id") == notification_id:
                n["is_read"] = True

        # 同步到数据库
        if hasattr(self, "_db_session") and self._db_session is not None:
            from sqlmodel import text
            self._db_session.execute(
                text("UPDATE notifications SET is_read = 1 WHERE id = :nid"),
                {"nid": notification_id},
            )
            self._db_session.commit()
        else:
            self._mark_read_in_production(notification_id)

        self._update_unread_count()

    # ── 内部方法 ──

    def _load_from_session(self, session) -> None:
        """从 sqlmodel Session 加载通知（测试环境）"""
        try:
            from sqlmodel import text
            result = session.execute(
                text("SELECT * FROM notifications ORDER BY created_at DESC")
            )
            rows = result.fetchall()
            self.notices = []
            for row in rows:
                # Row 对象支持 ._mapping 转为 dict
                try:
                    d = dict(row._mapping)
                except AttributeError:
                    # fallback: 按位置索引
                    d = {
                        "id": row[0],
                        "user_id": row[1] if len(row) > 1 else None,
                        "title": row[2] if len(row) > 2 else "",
                        "body": row[3] if len(row) > 3 else "",
                        "category": row[4] if len(row) > 4 else "announcement",
                        "is_read": bool(row[5]) if len(row) > 5 else False,
                        "created_at": str(row[6]) if len(row) > 6 else "",
                    }
                if "is_read" in d:
                    d["is_read"] = bool(d["is_read"])
                if "created_at" in d and d["created_at"]:
                    d["created_at"] = str(d["created_at"])
                self.notices.append(d)
        except Exception:
            self.notices = []

    def _load_from_production(self) -> None:
        """从生产数据库加载通知（通过 oaepp.database 连接池）"""
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    if self._user_id:
                        cur.execute(
                            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC",
                            (self._user_id,),
                        )
                    else:
                        cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
                    rows = cur.fetchall()
            # DictCursor 返回 dict 列表，直接使用
            self.notices = []
            for row in rows:
                n = dict(row)
                if "is_read" in n:
                    n["is_read"] = bool(n["is_read"])
                if "created_at" in n and n["created_at"]:
                    n["created_at"] = str(n["created_at"])
                self.notices.append(n)
        except Exception:
            self.notices = []

    def _mark_read_in_production(self, notification_id: int) -> None:
        """在生产数据库中标记已读（通过 oaepp.database 连接池）"""
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE notifications SET is_read = 1 WHERE id = %s",
                        (notification_id,),
                    )
                conn.commit()
        except Exception:
            pass

    def _update_unread_count(self) -> None:
        """更新未读通知计数"""
        count = 0
        for n in self.notices:
            if not n.get("is_read", False):
                count += 1
        self.unread_count = count
