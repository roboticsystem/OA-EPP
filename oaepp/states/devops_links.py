"""GitHub 快捷链接状态管理（F-D-008 / #41）

提供 7 类标准快捷链接的配置与持久化：
- 仓库主页 / PR 列表 / Issues 列表 / Actions / 分支管理 / Secrets / 分支保护规则
- 链接基于已配置仓库 URL 自动生成，无需手动填写
- 支持自定义标签名称、显示顺序、隐藏/显示
- 持久化到 MySQL gh_quick_links 表，通过 Reflex ORM (rx.session) 读写
"""

from __future__ import annotations

import os
from typing import Optional

import reflex as rx
from sqlmodel import Session, select

# ══════════════════════════════════════════════════════════════════════════════
#  全局仓库 URL
# ══════════════════════════════════════════════════════════════════════════════

GITHUB_REPO_URL = os.environ.get(
    "GITHUB_REPO_URL",
    "https://github.com/uwislab/robotics-systems-course",
).rstrip("/")


# ══════════════════════════════════════════════════════════════════════════════
#  7 类标准快捷链接定义
# ══════════════════════════════════════════════════════════════════════════════

REQUIRED_LINK_TYPES = [
    "repo",
    "pulls",
    "issues",
    "actions",
    "branches",
    "secrets",
    "branch_protection",
]

DEFAULT_LINK_TYPES: list[dict] = [
    {
        "id": "repo",
        "label": "仓库主页",
        "url_suffix": "",
        "icon": "folder-git-2",
        "visible": True,
        "sort_order": 1,
    },
    {
        "id": "pulls",
        "label": "Pull Requests",
        "url_suffix": "/pulls",
        "icon": "git-pull-request",
        "visible": True,
        "sort_order": 2,
    },
    {
        "id": "issues",
        "label": "Issues",
        "url_suffix": "/issues",
        "icon": "alert-circle",
        "visible": True,
        "sort_order": 3,
    },
    {
        "id": "actions",
        "label": "Actions / CI",
        "url_suffix": "/actions",
        "icon": "play",
        "visible": True,
        "sort_order": 4,
    },
    {
        "id": "branches",
        "label": "分支管理",
        "url_suffix": "/branches",
        "icon": "git-branch",
        "visible": True,
        "sort_order": 5,
    },
    {
        "id": "secrets",
        "label": "Settings · Secrets",
        "url_suffix": "/settings/secrets/actions",
        "icon": "key",
        "visible": True,
        "sort_order": 6,
    },
    {
        "id": "branch_protection",
        "label": "Settings · 分支保护",
        "url_suffix": "/settings/branches",
        "icon": "shield-check",
        "visible": True,
        "sort_order": 7,
    },
]


def _build_url(suffix: str) -> str:
    """基于仓库 URL 拼接子路径。"""
    if not suffix:
        return GITHUB_REPO_URL
    return f"{GITHUB_REPO_URL}{suffix}"


def build_default_link_records() -> list[dict]:
    """基于 DEFAULT_LINK_TYPES + GITHUB_REPO_URL 生成完整默认链接记录。"""
    return [
        {
            "id": item["id"],
            "label": item["label"],
            "url": _build_url(item["url_suffix"]),
            "icon": item["icon"],
            "visible": item["visible"],
            "sort_order": item["sort_order"],
        }
        for item in sorted(DEFAULT_LINK_TYPES, key=lambda x: x["sort_order"])
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  导入 ORM 模型
# ══════════════════════════════════════════════════════════════════════════════

try:
    from oaepp.models.gh_quicklink import GHSLink  # type: ignore[import-untyped]
    _HAS_ORM = True
except ImportError:
    _HAS_ORM = False


# ══════════════════════════════════════════════════════════════════════════════
#  Reflex State
# ══════════════════════════════════════════════════════════════════════════════

class GitHubLinksState(rx.State):
    """管理 7 类标准 GitHub 快捷链接的配置与显示。"""

    # ── 常量（类属性，测试可直接引用） ────────────────────────────────────
    REQUIRED_LINK_TYPES: list[str] = REQUIRED_LINK_TYPES
    DEFAULT_LINK_TYPES: list[dict] = DEFAULT_LINK_TYPES

    # ── 核心字段 ───────────────────────────────────────────────────────────
    repo_url: str = GITHUB_REPO_URL
    links: list[dict] = []

    # ── 编辑态字段 ─────────────────────────────────────────────────────────
    edit_mode: bool = False
    editing_link_id: str = ""
    editing_label: str = ""

    # ── 加载标记 ───────────────────────────────────────────────────────────
    loaded: bool = False

    @rx.var
    def visible_links(self) -> list[dict]:
        """仅返回可见且按 sort_order 排序的链接列表。"""
        return sorted(
            [lnk for lnk in self.links if lnk.get("visible", True)],
            key=lambda x: x.get("sort_order", 99),
        )

    @rx.var
    def hidden_links(self) -> list[dict]:
        """返回被隐藏的链接列表。"""
        return [lnk for lnk in self.links if not lnk.get("visible", True)]

    @rx.var
    def hidden_count(self) -> int:
        """隐藏链接数量。"""
        return len(self.hidden_links)

    # ── 生命周期 ──────────────────────────────────────────────────────────

    def _hydrate_from_orm(self) -> bool:
        """尝试从 ORM 加载持久化配置，失败返回 False。"""
        if not _HAS_ORM:
            return False
        try:
            with rx.session() as sess:
                rows = sess.exec(
                    select(GHSLink).order_by(GHSLink.sort_order)  # type: ignore[union-attr]
                ).all()
            if rows:
                self.links = [
                    {
                        "id": r.id,
                        "label": r.label,
                        "url": r.url,
                        "icon": r.icon,
                        "visible": r.visible,
                        "sort_order": r.sort_order,
                    }
                    for r in rows
                ]
                return True
        except Exception:
            pass
        return False

    def load_links(self):
        """页面挂载时调用：优先 ORM，回退默认配置。"""
        if not self._hydrate_from_orm():
            self.links = build_default_link_records()
        self.loaded = True

    def generate_links(self):
        """别名：同 load_links，用于兼容不同调用方。"""
        self.load_links()

    def reset_to_defaults(self):
        """重置所有链接为默认值。"""
        self.links = build_default_link_records()
        self.edit_mode = False
        self.editing_link_id = ""
        self.editing_label = ""

    # ── 可见性 ─────────────────────────────────────────────────────────────

    def toggle_visibility(self, link_id: str):
        """切换某个链接的显示/隐藏状态。"""
        for lnk in self.links:
            if lnk["id"] == link_id:
                lnk["visible"] = not lnk["visible"]
                break
        self._persist()

    # ── 自定义标签 ─────────────────────────────────────────────────────────

    def start_edit_label(self, link_id: str):
        """进入标签编辑模式。"""
        self.edit_mode = True
        self.editing_link_id = link_id
        for lnk in self.links:
            if lnk["id"] == link_id:
                self.editing_label = lnk["label"]
                break

    def set_editing_label(self, value: str):
        """更新编辑中的标签文本。"""
        self.editing_label = value

    def save_label(self):
        """保存当前编辑的标签名称。"""
        if not self.editing_link_id:
            return
        for lnk in self.links:
            if lnk["id"] == self.editing_link_id:
                lnk["label"] = self.editing_label.strip() or lnk["label"]
                break
        self.edit_mode = False
        self.editing_link_id = ""
        self.editing_label = ""
        self._persist()

    def cancel_edit(self):
        """取消标签编辑。"""
        self.edit_mode = False
        self.editing_link_id = ""
        self.editing_label = ""

    # ── 排序 ───────────────────────────────────────────────────────────────

    def move_up(self, link_id: str):
        """将指定链接上移一位。"""
        visible = [lnk for lnk in self.links if lnk.get("visible", True)]
        for i, lnk in enumerate(visible):
            if lnk["id"] == link_id and i > 0:
                a = visible[i - 1]
                b = lnk
                a_sort = a["sort_order"]
                b_sort = b["sort_order"]
                for orig in self.links:
                    if orig["id"] == a["id"]:
                        orig["sort_order"] = b_sort
                    elif orig["id"] == b["id"]:
                        orig["sort_order"] = a_sort
                break
        self._persist()

    def move_down(self, link_id: str):
        """将指定链接下移一位。"""
        visible = [lnk for lnk in self.links if lnk.get("visible", True)]
        for i, lnk in enumerate(visible):
            if lnk["id"] == link_id and i < len(visible) - 1:
                a = lnk
                b = visible[i + 1]
                a_sort = a["sort_order"]
                b_sort = b["sort_order"]
                for orig in self.links:
                    if orig["id"] == a["id"]:
                        orig["sort_order"] = b_sort
                    elif orig["id"] == b["id"]:
                        orig["sort_order"] = a_sort
                break
        self._persist()

    def set_sort_order(self, link_id: str, new_order: str):
        """手动设置 sort_order 数值。"""
        try:
            val = int(new_order)
        except ValueError:
            return
        for lnk in self.links:
            if lnk["id"] == link_id:
                lnk["sort_order"] = max(1, min(99, val))
                break
        self._persist()

    # ── 持久化 ─────────────────────────────────────────────────────────────

    def _persist(self):
        """将当前 links 写回 ORM（若可用）。"""
        if not _HAS_ORM:
            return
        try:
            with rx.session() as sess:
                for lnk in self.links:
                    row = sess.exec(
                        select(GHSLink).where(GHSLink.id == lnk["id"])  # type: ignore[union-attr]
                    ).first()
                    if row:
                        row.label = lnk["label"]
                        row.url = lnk["url"]
                        row.icon = lnk["icon"]
                        row.visible = lnk["visible"]
                        row.sort_order = lnk["sort_order"]
                    else:
                        sess.add(
                            GHSLink(
                                id=lnk["id"],
                                label=lnk["label"],
                                url=lnk["url"],
                                icon=lnk["icon"],
                                visible=lnk["visible"],
                                sort_order=lnk["sort_order"],
                            )
                        )
                sess.commit()
        except Exception:
            pass
