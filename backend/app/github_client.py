"""
github_client.py — GitHub API 客户端

通过 GitHub REST API 创建/更新仓库中的文件。
需要环境变量 GITHUB_TOKEN 和可选的 GITHUB_REPO（默认使用项目配置）。
"""

import os
import base64
import json
import urllib.request
import urllib.error
from typing import Optional

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = os.environ.get("GITHUB_REPO", "uwislab/robotics-systems-course")
GIT_BRANCH   = os.environ.get("GIT_BRANCH", "F-D-009]-Commit-消息格式自动校验")

_API_BASE = "https://api.github.com"


def _headers() -> dict:
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN 未配置，请在 .env 文件中设置")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OA-EPP-commitlint/1.0",
    }


def _api_url(path: str) -> str:
    return f"{_API_BASE}/repos/{GITHUB_REPO}{path}"


def _github_request(
    method: str,
    url: str,
    data: Optional[dict] = None,
) -> dict:
    """发送 GitHub API 请求，返回 JSON 响应。"""
    headers = _headers()
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(
            f"GitHub API {method} {url} 失败 (HTTP {e.code}): {detail}"
        )


def _encode_content(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def file_exists(path: str, branch: Optional[str] = None) -> bool:
    """检查仓库中是否存在指定路径的文件。"""
    ref = branch or GIT_BRANCH
    try:
        _github_request("GET", _api_url(f"/contents/{path}?ref={ref}"))
        return True
    except RuntimeError:
        return False


def get_file_sha(path: str, branch: Optional[str] = None) -> Optional[str]:
    """获取仓库中已有文件的 SHA（用于更新文件）。返回 None 表示文件不存在。"""
    ref = branch or GIT_BRANCH
    try:
        resp = _github_request(
            "GET", _api_url(f"/contents/{path}?ref={ref}")
        )
        return resp.get("sha")
    except RuntimeError:
        return None


def push_file(
    path: str,
    content: str,
    commit_message: str,
    branch: Optional[str] = None,
) -> dict:
    """
    向仓库推送单个文件。
    - 文件不存在则创建；存在则更新。
    - 返回 GitHub API 响应（含 commit SHA）。
    """
    branch = branch or GIT_BRANCH
    sha = get_file_sha(path)

    data = {
        "message": commit_message,
        "content": _encode_content(content),
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    return _github_request("PUT", _api_url(f"/contents/{path}"), data)


def push_files(
    files: list[dict[str, str]],
    commit_message: str,
    branch: Optional[str] = None,
) -> dict:
    """
    通过 Content API 推送文件（逐文件 PUT /contents/{path}）。
    返回 {"commit_sha": "...", "commit_url": "..."}
    """
    branch = branch or GIT_BRANCH

    last_sha = None
    for f in files:
        data = {
            "message": commit_message,
            "content": _encode_content(f["content"]),
            "branch": branch,
        }
        sha = get_file_sha(f["path"], branch)
        if sha:
            data["sha"] = sha

        resp = _github_request("PUT", _api_url(f"/contents/{f['path']}"), data)
        last_sha = resp["commit"]["sha"]

    commit_url = f"https://github.com/{GITHUB_REPO}/commit/{last_sha}"
    return {
        "commit_sha": last_sha,
        "commit_url": commit_url,
        "html_url": commit_url,
    }


def check_token() -> dict:
    """验证 GITHUB_TOKEN 是否有效，返回仓库信息。"""
    try:
        repo = _github_request("GET", _api_url(""))
        return {
            "ok": True,
            "default_branch": repo.get("default_branch", "main"),
            "full_name": repo.get("full_name", GITHUB_REPO),
            "html_url": repo.get("html_url", ""),
        }
    except (ValueError, RuntimeError) as e:
        return {"ok": False, "error": str(e)}


def get_repo_file_content(path: str, branch: Optional[str] = None) -> Optional[str]:
    """读取仓库中文件的内容（用于比对版本）。"""
    ref = branch or GIT_BRANCH
    try:
        resp = _github_request(
            "GET", _api_url(f"/contents/{path}?ref={ref}")
        )
        if resp.get("encoding") == "base64":
            return base64.b64decode(resp["content"]).decode("utf-8")
        return resp.get("content")
    except RuntimeError:
        return None


def list_branches() -> list[dict]:
    """获取仓库所有分支列表。返回 [{"name": "...", "default": bool}, ...]"""
    try:
        # 获取默认分支
        repo = _github_request("GET", _api_url(""))
        default_branch = repo.get("default_branch", "main")
        # 获取所有分支
        resp = _github_request("GET", _api_url("/branches") + "?per_page=100")
        branches = []
        for b in resp:
            branches.append({
                "name": b["name"],
                "default": b["name"] == default_branch,
            })
        return branches
    except RuntimeError as e:
        return []

