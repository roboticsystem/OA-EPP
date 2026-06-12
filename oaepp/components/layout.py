"""oaepp.components.layout — 共享页面壳。

所有页面通过 page_layout() 包裹，自动获得：
- 顶部 Toast 错误提示条
- 未来可扩展：导航栏、侧边栏插槽
"""

import reflex as rx
from oaepp.components.toast_bar import toast_bar


def page_layout(*children) -> rx.Component:
    """页面通用布局。

    自动挂载全局 Toast 条，子元素填充内容区。

    用法:
        @rx.page("/", title="首页")
        def index():
            return page_layout(
                rx.heading("欢迎"),
                ...
            )
    """
    return rx.box(
        # 全局 Toast（最顶层，始终在内容上方）
        toast_bar(),
        # 页面内容
        rx.box(
            *children,
            width="100%",
        ),
        width="100%",
        position="relative",
    )
