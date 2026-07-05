"""GitHub 快捷链接 ORM 模型 — 映射到 gh_quick_links 表（F-D-008 / #41）

持久化 7 类标准快捷链接的自定义配置：
- 标签名称、URL、图标、可见性、排序
"""

from __future__ import annotations

from typing import Optional
from sqlmodel import SQLModel, Field


class GHSLink(SQLModel, table=True):
    """GitHub 快捷链接配置 — 映射到 gh_quick_links 表"""

    __tablename__ = "gh_quick_links"

    id: str = Field(primary_key=True, max_length=64)           # repo / pulls / issues / actions / branches / secrets / branch_protection
    label: str = Field(default="")                              # 自定义标签名
    url: str = Field(default="")                                # 完整跳转 URL
    icon: str = Field(default="link-2")                         # Lucide 图标名
    visible: bool = Field(default=True)                         # 是否可见
    sort_order: int = Field(default=99)                         # 显示排序
