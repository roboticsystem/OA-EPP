"""F-S-012 公告通知 — NoticeState

提供公告通知的状态管理：
- notices: 通知列表，按发布时间降序
- unread_count: 未读通知计数
- load_notices(): 从数据库加载通知
- mark_as_read(): 标记通知为已读

依赖：
- oaepp.database: 统一数据库连接（pymysql 同步接口）
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

    def __init__(self):
        self.notices = []
        self.unread_count = 0

    # ── 事件处理器 ──

    def load_notices(self, user_id: Optional[int] = None) -> None:
        """从数据库加载通知列表，按发布时间降序排列。

        Args:
            user_id: 可选，指定加载哪个用户的通知
        """
        self._user_id = user_id
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
        self._mark_read_in_production(notification_id)
        self._update_unread_count()

    # ── 内部方法 ──

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
