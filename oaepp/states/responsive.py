"""F-S-050 响应式布局状态 — ResponsiveState

管理移动端侧边抽屉的打开/关闭状态。

用法:
    from oaepp.states.responsive import ResponsiveState

    # 在组件中使用
    ResponsiveState.sidebar_open      # 读取抽屉是否打开
    ResponsiveState.toggle_sidebar()  # 切换抽屉
    ResponsiveState.close_sidebar()   # 关闭抽屉
"""
import reflex as rx


class ResponsiveState(rx.State):
    """响应式布局状态管理

    管理移动端侧边栏抽屉的显示/隐藏。
    桌面端此状态不生效（侧边栏始终显示，抽屉始终隐藏）。
    """

    sidebar_open: bool = False

    def toggle_sidebar(self):
        """切换侧边栏抽屉的打开/关闭状态"""
        self.sidebar_open = not self.sidebar_open

    def close_sidebar(self):
        """关闭侧边栏抽屉（点击遮罩或导航链接时调用）"""
        self.sidebar_open = False
