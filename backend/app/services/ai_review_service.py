import re
from typing import Dict, Optional


def _normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.lower()
    # keep alnum and CJK unified by removing punctuation
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)
    return s


def analyze_name_match(expected_name: str, github_user: Dict[str, str]) -> Dict[str, object]:
    """Basic heuristic to compare student expected name with GitHub profile name.
    Returns dict: {match: bool, score: float, github_name: str, reason: str}
    """
    github_name = (github_user.get("name") or "").strip()
    github_bio = (github_user.get("bio") or "").strip()

    norm_expected = _normalize(expected_name)
    norm_github = _normalize(github_name)
    norm_bio = _normalize(github_bio)

    # exact match
    if norm_expected and norm_expected == norm_github:
        return {"match": True, "score": 1.0, "github_name": github_name, "reason": "完全匹配"}

    # substring match
    if norm_expected and norm_expected in norm_github:
        return {"match": True, "score": 0.85, "github_name": github_name, "reason": "姓名为 GitHub 名称的子串"}

    if norm_github and norm_github in norm_expected:
        return {"match": True, "score": 0.8, "github_name": github_name, "reason": "GitHub 名称为姓名的子串"}

    # bio contains name tokens
    if norm_expected and norm_expected in norm_bio:
        return {"match": True, "score": 0.7, "github_name": github_name, "reason": "姓名出现在 GitHub bio 中"}

    # token overlap heuristic
    def tokens(s: str):
        if not s:
            return set()
        # split CJK into characters, latin by camel/cut
        if re.search(r"[\u4e00-\u9fff]", s):
            return set(list(s))
        return set(re.findall(r"[a-z0-9]+", s))

    t_expected = tokens(norm_expected)
    t_github = tokens(norm_github) | tokens(norm_bio)
    if t_expected and t_github:
        overlap = t_expected & t_github
        ratio = len(overlap) / max(len(t_expected), 1)
        if ratio >= 0.5:
            return {"match": True, "score": round(0.6 + 0.4 * ratio, 2), "github_name": github_name, "reason": f"部分匹配，重合率 {ratio:.2f}"}

    return {"match": False, "score": 0.0, "github_name": github_name, "reason": "未能在 GitHub 资料中找到明显匹配"}
