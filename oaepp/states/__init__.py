"""Reflex States 子包

导出：
- GlobalState：全局状态基类（所有功能状态继承此类）
- DeadlineState：截止规则状态（F-S-022）

使用方式：
    from states import GlobalState
    from states.deadline import DeadlineState
"""

try:
    from .deadline import DeadlineState
except Exception:
    DeadlineState = None

try:
    from .auth import AuthState
except Exception:
    AuthState = None

# ── 全局状态基类（学生功能继承此类） ──
try:
    import reflex as rx

    class GlobalState(rx.State):
        """全局状态基类 — 所有功能状态继承此类

        需求编号：F-S-001（登录）、F-S-002（个人资料）
        """

        # ── 登录用户信息（只读） ──
        current_user: dict = {}
        """当前登录用户信息：{"student_no": "2021001", "full_name": "张三", "role": "student"}"""

        # ── 全局加载状态 ──
        is_loading: bool = False

        # ── 全局通知未读数 ──
        unread_notifications: int = 0

        # ── 方法：设置登录用户（仅由登录页面调用） ──
        def set_user(self, user: dict):
            """设置当前登录用户"""
            self.current_user = user
            self.is_loading = False

        # ── 方法：清除登录用户（仅由退出页面调用） ──
        def clear_user(self):
            """清除当前登录用户"""
            self.current_user = {}
            self.unread_notifications = 0

except Exception:
    GlobalState = None

__all__ = ["AuthState", "DeadlineState"]
