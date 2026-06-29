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

# ── 保留你的评语功能 import ──
try:
    from .grade_state import TeacherGradeState, StudentGradeState
except Exception:
    TeacherGradeState = None
    StudentGradeState = None


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
