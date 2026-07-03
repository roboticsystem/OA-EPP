"""F-S-050 响应式布局演示页面

展示响应式布局功能，包括：
- 桌面端：侧边栏 + 顶栏布局
- 移动端：底部导航 + 汉堡菜单抽屉
- 网络状态监控

本页面使用 responsive_page_layout() 替代 page_layout()，
具备完整的移动端适配能力。
"""
try:
    import reflex as rx
except Exception:
    rx = None

responsive_page = None

if rx is not None:
    from oaepp.components.responsive import responsive_page_layout
    from oaepp.components.common import stat_card, empty_state

    def responsive_page():
        """响应式布局演示页面

        展示响应式布局的各种组件和适配效果。
        """
        return responsive_page_layout(
            title="响应式布局演示",
            content=rx.vstack(
                rx.heading("F-S-050 响应式布局", size="6"),
                rx.text(
                    "此页面展示了移动端和桌面端的响应式适配功能。",
                    color="gray",
                    size="3",
                ),
                rx.divider(),
                # 统计卡片（使用响应式 grid CSS）
                rx.grid(
                    stat_card("响应式断点", "768px", icon="smartphone"),
                    stat_card("移动端组件", "3 个", icon="layout_panel_left"),
                    stat_card("网络状态监控", "已启用", icon="wifi"),
                    columns="3",
                    spacing="4",
                    class_name="oaepp-stat-grid",
                ),
                rx.divider(),
                # 功能说明
                rx.box(
                    rx.vstack(
                        rx.heading("功能清单", size="4"),
                        rx.text("✅ 桌面端：固定侧边栏 + 顶栏", size="2"),
                        rx.text("✅ 移动端：汉堡菜单 + 侧滑抽屉", size="2"),
                        rx.text("✅ 移动端：底部固定导航栏", size="2"),
                        rx.text("✅ 网络断连横幅（断开网络测试）", size="2"),
                        rx.text("✅ 网络状态图标（顶栏右侧）", size="2"),
                        rx.text("✅ CSS 媒体查询自适应（768px 断点）", size="2"),
                        rx.text("✅ iPhone 刘海屏安全区适配", size="2"),
                        spacing="2",
                        align="start",
                    ),
                    padding="20px",
                    border_radius="8px",
                    border="1px solid var(--gray-5)",
                    width="100%",
                ),
                spacing="4",
                align="stretch",
                width="100%",
            ),
        )
