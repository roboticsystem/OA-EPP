"""共享 UI 组件 — 统一导出

学生用法：
    from oaepp.components.layout import page_layout
    from oaepp.components.common import (
        stat_card, empty_state, loading_spinner,
        connection_banner, network_status_icon,
    )
"""
from .layout import page_layout
from .common import (
    stat_card, empty_state, loading_spinner, data_table,
    connection_banner, network_status_icon,
)
