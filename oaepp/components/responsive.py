"""F-S-050 响应式布局组件 — 移动端适配 & 网络韧性

提供响应式布局相关组件，包括：
- connection_banner()       — 网络断开横幅
- network_status_icon()     — 网络状态图标
- responsive_page_layout()  — 响应式页面布局（移动端抽屉 + 底部导航 + 桌面端侧边栏）

用法:
    from oaepp.components.responsive import responsive_page_layout, connection_banner

    def my_page():
        return responsive_page_layout(
            title="我的页面",
            content=rx.vstack(...),
        )
"""
import reflex as rx

from oaepp.states.responsive import ResponsiveState
from oaepp.states.error import ErrorState


# ── 移动端底部导航项 ────────────────────────────────────────────────────
_MOBILE_BOTTOM_ITEMS = [
    ("dashboard", "layout_dashboard"),
    ("courses", "book_open"),
    ("assignments", "file_text"),
    ("grades", "bar_chart_3"),
    ("profile", "user"),
]

# ── 侧边栏导航项 ────────────────────────────────────────────────────────
_NAV_ITEMS = [
    ("课程主页", "/dashboard", "layout_dashboard"),
    ("我的课程", "/courses", "book_open"),
    ("作业提交", "/assignments", "file_text"),
    ("成绩看板", "/grades", "bar_chart_3"),
    ("课堂点名", "/attendance", "user_check"),
    ("在线考试", "/exam", "clipboard_check"),
    ("个人资料", "/profile", "user"),
]


# ═══════════════════════════════════════════════════════════════════════════
# 网络韧性组件
# ═══════════════════════════════════════════════════════════════════════════

def connection_banner() -> rx.Component:
    """网络断开横幅 — 当检测到网络断开时显示红色提示条

    读取 ErrorState.network_online 状态。
    在线时不渲染任何内容，离线时显示粘性顶部横幅。
    """
    return rx.cond(
        ErrorState.network_online == False,
        rx.box(
            rx.hstack(
                rx.icon(tag="wifi_off", size=16, color="white"),
                rx.text("网络已断开，部分功能可能不可用", color="white", size="2"),
                spacing="2",
                align="center",
                justify="center",
                width="100%",
                padding="8px 16px",
            ),
            background_color="#dc2626",
            class_name="oaepp-connection-banner",
        ),
    )


def network_status_icon() -> rx.Component:
    """网络状态图标 — 在线显示绿色 WiFi 图标，离线显示红色断开图标"""
    return rx.cond(
        ErrorState.network_online,
        rx.icon(tag="wifi", size=18, color="green"),
        rx.icon(tag="wifi_off", size=18, color="red"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 侧边栏导航
# ═══════════════════════════════════════════════════════════════════════════

def _nav_item(label: str, route: str, icon_tag: str) -> rx.Component:
    """单个导航项 — 高亮当前路由"""
    return rx.link(
        rx.hstack(
            rx.icon(tag=icon_tag, size=18),
            rx.text(label, size="3"),
            spacing="3",
            align="center",
            width="100%",
            padding="10px 14px",
            border_radius="8px",
            background_color=rx.cond(
                rx.State.router.page.path == route,
                "var(--blue-3)",
                "transparent",
            ),
            color=rx.cond(
                rx.State.router.page.path == route,
                "var(--blue-9)",
                "var(--gray-11)",
            ),
            _hover={
                "background_color": rx.cond(
                    rx.State.router.page.path == route,
                    "var(--blue-3)",
                    "var(--gray-4)",
                ),
            },
        ),
        href=route,
        width="100%",
        text_decoration="none",
    )


def _sidebar() -> rx.Component:
    """桌面端侧边栏导航 — 通过 CSS class_name 控制移动端隐藏"""
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.heading("OA-EPP", size="5", color_scheme="blue"),
                rx.text("工程实践管理平台", size="1", color="gray"),
                align="center",
                padding="20px 16px",
                width="100%",
            ),
            rx.divider(),
            rx.vstack(
                *[_nav_item(label, route, icon) for label, route, icon in _NAV_ITEMS],
                spacing="1",
                width="100%",
                padding="8px 12px",
            ),
            rx.box(flex="1"),
            spacing="0",
            width="100%",
            height="100%",
        ),
        class_name="oaepp-sidebar",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 移动端组件
# ═══════════════════════════════════════════════════════════════════════════

def _hamburger_button() -> rx.Component:
    """移动端汉堡菜单按钮 — 通过 CSS 控制在桌面端隐藏"""
    return rx.button(
        rx.icon(tag="menu", size=20),
        on_click=ResponsiveState.toggle_sidebar,
        variant="ghost",
        color_scheme="gray",
        class_name="oaepp-hamburger-btn",
    )


def _mobile_drawer() -> rx.Component:
    """移动端侧滑抽屉 — 仅在 sidebar_open=True 时渲染"""
    return rx.cond(
        ResponsiveState.sidebar_open,
        rx.box(
            # 遮罩层 — 点击关闭抽屉
            rx.box(
                on_click=ResponsiveState.close_sidebar,
                class_name="oaepp-drawer-backdrop",
            ),
            # 抽屉面板
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("OA-EPP", size="5", color_scheme="blue"),
                        rx.button(
                            rx.icon(tag="x", size=18),
                            on_click=ResponsiveState.close_sidebar,
                            variant="ghost",
                            color_scheme="gray",
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                        padding="16px",
                    ),
                    rx.divider(),
                    rx.vstack(
                        *[
                            rx.link(
                                rx.hstack(
                                    rx.icon(tag=icon, size=18),
                                    rx.text(label, size="3"),
                                    spacing="3",
                                    align="center",
                                    padding="10px 14px",
                                    width="100%",
                                ),
                                href=f"/{label}" if label != "课程主页" else "/dashboard",
                                width="100%",
                                text_decoration="none",
                                on_click=ResponsiveState.close_sidebar,
                            )
                            for label, route, icon in _NAV_ITEMS
                        ],
                        spacing="1",
                        width="100%",
                        padding="8px 12px",
                    ),
                    spacing="0",
                    width="100%",
                ),
                class_name="oaepp-drawer-panel",
            ),
            class_name="oaepp-drawer",
        ),
    )


def _mobile_bottom_nav() -> rx.Component:
    """移动端底部固定导航栏 — 通过 CSS 控制在桌面端隐藏"""
    return rx.box(
        rx.hstack(
            *[
                rx.link(
                    rx.vstack(
                        rx.icon(tag=icon, size=20),
                        rx.text(label, size="1"),
                        spacing="0",
                        align="center",
                    ),
                    href=f"/{label}" if label != "dashboard" else "/dashboard",
                    class_name="oaepp-bottom-nav-item",
                )
                for label, icon in _MOBILE_BOTTOM_ITEMS
            ],
            justify="around",
            align="center",
            width="100%",
            padding="8px 4px",
            background_color="white",
            border_top="1px solid var(--gray-5)",
        ),
        class_name="oaepp-mobile-bottom-nav",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 网络监控脚本 — 监听浏览器 online/offline 事件并更新 ErrorState
# ═══════════════════════════════════════════════════════════════════════════

_NETWORK_MONITOR_SCRIPT = rx.script("""\
(function() {
    // 网络状态监控：监听浏览器 online/offline 事件
    // 通过 Reflex 内部事件机制更新 ErrorState.network_online

    function notifyNetworkChange(online) {
        console.log('[OA-EPP] Network ' + (online ? 'restored' : 'lost'));
        // 发送自定义事件，由 Reflex 前端桥接层转发到后端 State
        var event = new CustomEvent('_reflex_network_change', {
            detail: { online: online }
        });
        document.dispatchEvent(event);

        // 通过 Reflex WebSocket 发送状态更新事件
        try {
            var ws = document.querySelector('[data-reflex-ws]');
            if (!ws && window.__reflex && window.__reflex.ws) {
                ws = window.__reflex.ws;
            }
            // 备选：通过 fetch 发送到 /_event 端点
            if (!ws) {
                fetch('/_event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        state: 'error_state',
                        handler: online ? 'set_online' : 'set_offline',
                        args: []
                    })
                }).catch(function(e) {
                    console.warn('[OA-EPP] Network status update failed:', e);
                });
                return;
            }
        } catch(e) {
            console.warn('[OA-EPP] Network status sync error:', e);
        }
    }

    window.addEventListener('online', function() {
        notifyNetworkChange(true);
    });
    window.addEventListener('offline', function() {
        notifyNetworkChange(false);
    });

    // 初始化：检查当前网络状态
    if (!navigator.onLine) {
        console.log('[OA-EPP] Initial state: offline');
    }
})();
""")


# ═══════════════════════════════════════════════════════════════════════════
# 顶栏
# ═══════════════════════════════════════════════════════════════════════════

def _topbar(title: str) -> rx.Component:
    """顶栏：页面标题 + 汉堡菜单按钮 + 网络状态图标"""
    return rx.box(
        rx.hstack(
            _hamburger_button(),
            rx.heading(title, size="5"),
            rx.spacer(),
            network_status_icon(),
            align="center",
            width="100%",
            padding="16px 24px",
            border_bottom="1px solid var(--gray-5)",
            background_color="white",
        ),
        width="100%",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 响应式页面布局（对外公开接口）
# ═══════════════════════════════════════════════════════════════════════════

def responsive_page_layout(title: str, content: rx.Component) -> rx.Component:
    """响应式页面布局：桌面端侧边栏 + 移动端抽屉/底部导航

    与 page_layout() 的区别：
    - 添加了移动端适配（汉堡菜单、侧滑抽屉、底部导航栏）
    - 通过 CSS 类名控制移动端/桌面端显示
    - 包含网络状态监控和断连横幅

    Args:
        title: 页面标题（显示在顶栏）
        content: 页面主体内容

    Returns:
        完整的响应式页面布局组件

    用法示例:
        def dashboard_page():
            return responsive_page_layout(
                title="仪表盘",
                content=rx.vstack(
                    stat_card("已提交作业", 3),
                    stat_card("待批改", 1),
                ),
            )
    """
    return rx.box(
        # 桌面端侧边栏（CSS 控制移动端隐藏）
        _sidebar(),
        # 移动端抽屉（条件渲染）
        _mobile_drawer(),
        # 主内容区
        rx.box(
            # 网络断连横幅（粘性顶部）
            connection_banner(),
            _topbar(title),
            rx.box(
                content,
                padding="24px",
                width="100%",
                class_name="oaepp-content-area",
            ),
            class_name="oaepp-main-content",
        ),
        # 移动端底部导航栏（CSS 控制桌面端隐藏）
        _mobile_bottom_nav(),
        # 网络状态监控脚本
        _NETWORK_MONITOR_SCRIPT,
        width="100%",
    )
