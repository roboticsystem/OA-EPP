"""GitHub 快捷链接状态管理（F-D-008 / #41）

提供 7 类标准快捷链接的配置与持久化：
- 仓库主页 / PR 列表 / Issues 列表 / Actions / 分支管理 / Secrets / 分支保护规则
- 链接基于已配置仓库 URL 自动生成，无需手动填写
- 支持自定义标签名称、显示顺序、隐藏/显示
"""

from __future__ import annotations

import os
from typing import Optional

import reflex as rx
from sqlmodel import Field, Session, select


# ══════════════════════════════════════════════════════════════════════════════
#  全局仓库 URL（环境变量注入，运行时不可更改可被所有组件读取）
# ══════════════════════════════════════════════════════════════════════════════

GITHUB_REPO_URL = os.environ.get(
    "GITHUB_REPO_URL",
    "https://github.com/uwislab/robotics-systems-course",
).rstrip("/")


# ══════════════════════════════════════════════════════════════════════════════
#  7 类标准快捷链接定义（字段名与 GitHub 子路径映射）
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_LINKS: list[dict] = [
    {
        "id": "repo",
        "label": "仓库主页",
        "url_suffix": "",
        "icon": "github",
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
        "icon": "shield",
        "visible": True,
        "sort_order": 7,
    },
]


def _build_url(suffix: str) -> str:
    if not suffix:
        return GITHUB_REPO_URL
    return f"{GITHUB_REPO_URL}{suffix}"


def build_default_link_records() -> list[dict]:
    """基于 DEFAULT_LINKS + GITHUB_REPO_URL 生成完整的默认链接记录。"""
    return [
        {
            "id": item["id"],
            "label": item["label"],
            "url": _build_url(item["url_suffix"]),
            "icon": item["icon"],
            "visible": item["visible"],
            "sort_order": item["sort_order"],
        }
        for item in sorted(DEFAULT_LINKS, key=lambda x: x["sort_order"])
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  SQLModel 持久化模型（全局 models/ 中的 GHSLink 已由项目提供）
# ══════════════════════════════════════════════════════════════════════════════
# 说明：项目全局 models/ 已提供 GHSLink 模型，此处为引用示例。
#   from models.gh_quicklink import GHSLink
# 若尚未提供，可回退为本地字典模式运行（不持久化）——系统自动检测。


try:
    from models.gh_quicklink import GHSLink  # type: ignore[import-untyped]
    _HAS_ORM = True
except ImportError:
    _HAS_ORM = False


# ══════════════════════════════════════════════════════════════════════════════
#  Reflex State
# ══════════════════════════════════════════════════════════════════════════════

class GitHubQuickLinksState(rx.State):
    """管理 7 类标准 GitHub 快捷链接的配置与显示。"""

    # ── 核心字段 ───────────────────────────────────────────────────────────
    repo_url: str = GITHUB_REPO_URL
    links: list[dict] = []

    # ── 编辑态字段 ─────────────────────────────────────────────────────────
    edit_mode: bool = False
    editing_link_id: str = ""
    editing_label: str = ""

    # ── 加载提示 ───────────────────────────────────────────────────────────
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

    def reset_to_defaults(self):
        """重置所有链接为默认值（标签、顺序、可见性全部恢复）。"""
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
        self.edit_mode = True
        self.editing_link_id = link_id
        for lnk in self.links:
            if lnk["id"] == link_id:
                self.editing_label = lnk["label"]
                break

    def set_editing_label(self, value: str):
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
        self.edit_mode = False
        self.editing_link_id = ""
        self.editing_label = ""

    # ── 拖拽排序 ───────────────────────────────────────────────────────────

    def move_up(self, link_id: str):
        """将指定链接上移一位。"""
        visible = [lnk for lnk in self.links if lnk.get("visible", True)]
        for i, lnk in enumerate(visible):
            if lnk["id"] == link_id and i > 0:
                # 交换 sort_order
                a = visible[i - 1]
                b = lnk
                a_sort = a["sort_order"]
                b_sort = b["sort_order"]
                # 找到原始条目并交换
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

    # ── 别名重排序 ─────────────────────────────────────────────────────────

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
                        sess.add(GHSLink(**lnk))
                sess.commit()
        except Exception:
            pass
