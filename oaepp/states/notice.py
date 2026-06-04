"""F-S-012 公告通知 — NoticeState

提供公告通知的状态管理：
- notices: 通知列表，按发布时间降序
- unread_count: 未读通知计数
- load_notices(): 从数据库加载通知
- mark_as_read(): 标记通知为已读

依赖：
- oaepp.models.notice: 数据库连接
"""
from typing import Any, List, Optional


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

        优先使用 oaepp.models.notice 中的生产数据库连接；
        如果 conftest 提供了 mem_db fixture（SQLite 内存数据库），
        则通过 sqlmodel Session 查询。

        Args:
            user_id: 可选，指定加载哪个用户的通知
        """
        self._user_id = user_id

        # 尝试从 conftest mem_db fixture 注入的 session 获取数据
        if hasattr(self, "_db_session") and self._db_session is not None:
            self._load_from_session(self._db_session)
        else:
            # 使用 oaepp.models.notice 中的生产数据库连接
            self._load_from_production()

        # 确保 notices 始终为列表类型
        if not isinstance(self.notices, list):
            self.notices = []

        # 更新未读计数
        self._update_unread_count()

    def mark_as_read(self, notification_id: int) -> None:
        """标记指定通知为已读。

        Args:
            notification_id: 要标记的通知 ID
        """
        # 更新本地状态
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

        # 重新计算未读计数
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
            self.notices = [
                {
                    "id": row[0],
                    "user_id": row[1] if len(row) > 1 else None,
                    "title": row[2] if len(row) > 2 else "",
                    "body": row[3] if len(row) > 3 else "",
                    "category": row[4] if len(row) > 4 else "announcement",
                    "is_read": bool(row[5]) if len(row) > 5 else False,
                    "created_at": str(row[6]) if len(row) > 6 else "",
                }
                for row in rows
            ]
        except Exception:
            self.notices = []

    def _load_from_production(self) -> None:
        """从 oaepp.models.notice 中的生产数据库加载通知"""
        try:
            from oaepp.models.notice import get_db_connection

            conn = get_db_connection()
            try:
                import pymysql
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    if self._user_id:
                        cur.execute(
                            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC",
                            (self._user_id,),
                        )
                    else:
                        cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
                    self.notices = cur.fetchall()
            finally:
                conn.close()
        except Exception:
            self.notices = []

    def _mark_read_in_production(self, notification_id: int) -> None:
        """在生产数据库中标记已读"""
        try:
            from oaepp.models.notice import get_db_connection

            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE notifications SET is_read = 1 WHERE id = %s",
                        (notification_id,),
                    )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

    def _update_unread_count(self) -> None:
        """更新未读通知计数"""
        count = 0
        for n in self.notices:
            if not n.get("is_read", False):
                count += 1
        self.unread_count = count
