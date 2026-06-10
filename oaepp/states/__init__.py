<<<<<<< HEAD
"""States 子包

Reflex 自动发现机制：states/ 目录下所有继承 rx.State 的类自动注册。
学生创建 states/xxx.py 中的 XxxState(rx.State) 后自动生效，
无需修改此文件。

已有的 State 类（自动发现）：
  - AuthState     → states/auth.py（登录/登出）
  - GlobalState   → states/__init__.py（本文件，全局状态基类）

注意：DeadlineState → states/deadline.py 是普通类（不继承 rx.State），
      不会被 Reflex 自动发现，需显式 import 使用。
"""

import reflex as rx


class GlobalState(rx.State):
    """全局状态基类 — 学生功能可选择继承此类

    提供：current_user、toast 通知等全局状态。

    使用方式：
        from oaepp.states import GlobalState
        user = GlobalState.current_user
    """

    # ── 登录用户信息（只读） ──
    current_user: dict = {}
    """当前登录用户信息：{"student_no": "2024000001", "full_name": "张三", "role": "student"}"""

    # ── 全局加载状态 ──
    is_loading: bool = False

    # ── 全局消息提示 ──
    toast_message: str = ""
    toast_type: str = "info"  # info | success | warning | error

    # ── 全局通知未读数 ──
    unread_notifications: int = 0

    def set_user(self, user: dict):
        """设置当前登录用户（仅由登录页面调用）"""
        self.current_user = user
        self.is_loading = False

    def clear_user(self):
        """清除当前登录用户（仅由退出页面调用）"""
        self.current_user = {}
        self.unread_notifications = 0

    def show_toast(self, message: str, type: str = "info"):
        """显示全局消息提示"""
        self.toast_message = message
        self.toast_type = type

    def clear_toast(self):
        """清除全局消息提示"""
        self.toast_message = ""
        self.toast_type = "info"

    def get_current_user(self) -> dict:
        """获取当前登录用户信息

        返回示例：{"student_no": "2024000001", "full_name": "张三", "role": "student"}
        """
        return self.current_user
=======
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

        # ── 全局消息提示 ──
        toast_message: str = ""
        toast_type: str = "info"  # info | success | warning | error

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

        # ── 方法：显示全局提示 ──
        def show_toast(self, message: str, type: str = "info"):
            """显示全局消息提示"""
            self.toast_message = message
            self.toast_type = type

        # ── 方法：清除提示 ──
        def clear_toast(self):
            """清除全局消息提示"""
            self.toast_message = ""
            self.toast_type = "info"

except Exception:
    GlobalState = None

__all__ = ["AuthState", "DeadlineState"]
>>>>>>> de8cba5 (init: 提交项目初始代码)
