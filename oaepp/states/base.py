"""F-S-050 响应式布局基础状态 — BaseState

提供所有学生页面的公共基类状态。

用法:
    from oaepp.states.base import BaseState

    class MyPageState(BaseState):
        ...
"""
try:
    import reflex as rx
except Exception:
    rx = None

BaseState = None

if rx is not None:
    class BaseState(rx.State):
        """所有学生 State 的基类

        提供认证状态检查，所有页面 State 应继承此类。
        """

        is_authenticated: bool = False
