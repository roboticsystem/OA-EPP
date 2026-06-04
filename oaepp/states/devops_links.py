from typing import List, Dict, Optional


class GitHubLinksState:
    """提供与 GitHub 仓库相关的快捷链接列表。用于测试与 UI 快捷面板。

    要求：声明 `repo_url`、`links`；提供 `generate_links()` 或 `load_links()`；
    提供 `REQUIRED_LINK_TYPES` 或 `DEFAULT_LINK_TYPES`。
    """

    # 必需的链接类型（测试会检查此常量是否存在）
    REQUIRED_LINK_TYPES = ("repo", "PRs", "Issues", "Actions")

    # 实例属性
    repo_url: str = ""
    links: List[Dict] = []

    def __init__(self, repo_url: Optional[str] = None, custom_labels: Optional[Dict[str, str]] = None):
        self.repo_url = repo_url or ""
        # 每个实例保持自己的 links 列表
        self.links = []
        self._custom_labels = custom_labels or {}

    def generate_links(self) -> List[Dict]:
        """生成一组默认的快捷链接（可被 UI 用于展示）。

        每个链接为 dict，包含至少 `type`、`label`、`url` 字段。
        支持通过构造器传入 `custom_labels` 覆盖默认标签。
        """
        base = self.repo_url.rstrip("/")
        defaults = {
            "repo": f"{base}" if base else "",
            "PRs": f"{base}/pulls" if base else "",
            "Issues": f"{base}/issues" if base else "",
            "Actions": f"{base}/actions" if base else "",
        }

        order = ["repo", "PRs", "Issues", "Actions"]

        links = []
        for t in order:
            label = self._custom_labels.get(t, t)
            links.append({"type": t, "label": label, "url": defaults.get(t, "")})

        self.links = links
        return self.links

    def load_links(self, source: Optional[List[Dict]] = None) -> List[Dict]:
        """如果提供了自定义链接数据则加载，否则生成默认链接。"""
        if source is None:
            return self.generate_links()
        # 进行基本验证和排序：保留必须的字段
        cleaned = []
        for item in source:
            if not isinstance(item, dict):
                continue
            t = item.get("type")
            if not t:
                continue
            label = item.get("label", t)
            url = item.get("url", "")
            cleaned.append({"type": t, "label": label, "url": url})

        self.links = cleaned
        return self.links
