"""F-S-050 响应式布局 TDD 测试

测试响应式布局核心功能：
- ResponsiveState 状态管理
- 响应式组件可导入性
- 占位页面注册
"""
import pytest


# ═══════════════════════════════════════════════════════════════════════════
# TC01: ResponsiveState 存在且可实例化
# ═══════════════════════════════════════════════════════════════════════════

def test_F_S_050_TC01_responsive_state_exists():
    """ResponsiveState 必须存在且包含 sidebar_open 属性"""
    try:
        from oaepp.states.responsive import ResponsiveState
    except ImportError as e:
        pytest.fail(f"ResponsiveState 导入失败: {e}")

    assert ResponsiveState is not None, "ResponsiveState 未定义"

    # 验证默认属性
    state = ResponsiveState()
    assert hasattr(state, "sidebar_open"), "ResponsiveState 缺少 sidebar_open 属性"
    assert state.sidebar_open is False, "sidebar_open 默认值应为 False"


# ═══════════════════════════════════════════════════════════════════════════
# TC02: 响应式组件可导入
# ═══════════════════════════════════════════════════════════════════════════

def test_F_S_050_TC02_responsive_components_importable():
    """响应式布局组件必须可导入"""
    try:
        from oaepp.components.responsive import (
            responsive_page_layout,
            connection_banner,
            network_status_icon,
        )
    except ImportError as e:
        pytest.fail(f"响应式组件导入失败: {e}")

    assert responsive_page_layout is not None
    assert connection_banner is not None
    assert network_status_icon is not None


# ═══════════════════════════════════════════════════════════════════════════
# TC03: ResponsiveState 方法逻辑正确
# ═══════════════════════════════════════════════════════════════════════════

def test_F_S_050_TC03_responsive_state_methods():
    """ResponsiveState 的 toggle 和 close 方法逻辑正确"""
    from oaepp.states.responsive import ResponsiveState

    state = ResponsiveState()

    # toggle_sidebar: False → True
    state.toggle_sidebar()
    assert state.sidebar_open is True, "toggle_sidebar 应将 sidebar_open 翻转为 True"

    # toggle_sidebar: True → False
    state.toggle_sidebar()
    assert state.sidebar_open is False, "toggle_sidebar 应将 sidebar_open 翻转为 False"

    # close_sidebar: 强制关闭
    state.sidebar_open = True
    state.close_sidebar()
    assert state.sidebar_open is False, "close_sidebar 应将 sidebar_open 设置为 False"


# ═══════════════════════════════════════════════════════════════════════════
# TC04: 网络状态管理可用
# ═══════════════════════════════════════════════════════════════════════════

def test_F_S_050_TC04_network_state_methods():
    """ErrorState 必须包含 set_online / set_offline 方法"""
    try:
        from oaepp.states.error import ErrorState
    except ImportError as e:
        pytest.fail(f"ErrorState 导入失败: {e}")

    state = ErrorState()
    assert hasattr(state, "network_online"), "ErrorState 缺少 network_online"
    assert state.network_online is True, "network_online 默认值应为 True"

    state.set_offline()
    assert state.network_online is False, "set_offline 应将 network_online 设为 False"

    state.set_online()
    assert state.network_online is True, "set_online 应将 network_online 设为 True"


# ═══════════════════════════════════════════════════════════════════════════
# TC05: 占位页面可导入
# ═══════════════════════════════════════════════════════════════════════════

def test_F_S_050_TC05_placeholder_pages_importable():
    """底部导航栏引用的所有路由页面必须可导入"""
    pages = {
        "dashboard": "oaepp.pages.dashboard",
        "courses": "oaepp.pages.courses",
        "assignments": "oaepp.pages.assignments",
        "grades": "oaepp.pages.grades",
        "attendance": "oaepp.pages.attendance",
        "exam": "oaepp.pages.exam",
    }

    for name, module_path in pages.items():
        try:
            importlib = __import__("importlib")
            mod = importlib.import_module(module_path)
        except ImportError as e:
            pytest.fail(f"页面 {name} ({module_path}) 导入失败: {e}")

        page_func_name = f"{name}_page"
        assert hasattr(mod, page_func_name), (
            f"页面 {name} 缺少 {page_func_name}() 函数"
        )
