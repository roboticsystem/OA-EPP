import os
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

GITHUB_API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com")
CACHE_TTL = int(os.environ.get("REPORT_CACHE_TTL", "300"))


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OA-EPP-Report-Generator/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self._cache: Dict[str, tuple[Any, datetime]] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
                return value
            del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self._cache[key] = (value, datetime.now())

    async def _request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                elif response.status_code == 403:
                    if "rate limit" in response.text.lower():
                        raise Exception("GitHub API速率限制，请稍后重试")
                    raise Exception(f"GitHub API认证失败: {response.status_code}")
                else:
                    raise Exception(f"GitHub API错误: {response.status_code}")
        except httpx.TimeoutException:
            raise Exception("GitHub API请求超时")
        except httpx.ConnectError:
            raise Exception("无法连接到GitHub API")
        except Exception as e:
            raise Exception(f"GitHub API请求失败: {str(e)}")

    async def get_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        cache_key = f"branches:{owner}:{repo}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"
        data = await self._request("GET", url)
        if data is None:
            return []

        branches = []
        for branch in data:
            branch_info = {
                "name": branch.get("name", ""),
                "protected": branch.get("protected", False),
                "last_commit_sha": branch.get("commit", {}).get("sha", ""),
                "last_commit_date": branch.get("commit", {}).get("commit", {}).get("author", {}).get("date")
            }
            branches.append(branch_info)

        self._set_cache(cache_key, branches)
        return branches

    async def get_commits(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        cache_key = f"commits:{owner}:{repo}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
        params = {"per_page": per_page}
        data = await self._request("GET", url, params=params)
        if data is None:
            return []

        commits = []
        for commit in data:
            commit_info = {
                "sha": commit.get("sha", "")[:7],
                "message": commit.get("commit", {}).get("message", "").split("\n")[0],
                "author_name": commit.get("commit", {}).get("author", {}).get("name", ""),
                "author_email": commit.get("commit", {}).get("author", {}).get("email", ""),
                "date": commit.get("commit", {}).get("author", {}).get("date", ""),
                "additions": 0,
                "deletions": 0,
            }
            commits.append(commit_info)

        self._set_cache(cache_key, commits)
        return commits

    async def get_commit_details(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        cache_key = f"commit:{owner}:{repo}:{sha}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{sha}"
        data = await self._request("GET", url)
        if data is None:
            return {}

        result = {
            "additions": data.get("stats", {}).get("additions", 0),
            "deletions": data.get("stats", {}).get("deletions", 0),
            "files_changed": len(data.get("files", []))
        }

        self._set_cache(cache_key, result)
        return result

    async def get_pull_requests(self, owner: str, repo: str, state: str = "all") -> List[Dict[str, Any]]:
        cache_key = f"prs:{owner}:{repo}:{state}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": 100, "sort": "created", "direction": "desc"}
        data = await self._request("GET", url, params=params)
        if data is None:
            return []

        prs = []
        for pr in data:
            pr_info = {
                "number": pr.get("number", 0),
                "title": pr.get("title", ""),
                "state": pr.get("state", ""),
                "user_login": pr.get("user", {}).get("login", ""),
                "created_at": pr.get("created_at", ""),
                "updated_at": pr.get("updated_at", ""),
                "merged_at": pr.get("merged_at"),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "review_comments": pr.get("review_comments", 0),
                "url": pr.get("html_url", "")
            }
            prs.append(pr_info)

        self._set_cache(cache_key, prs)
        return prs

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """获取单个PR的详细信息"""
        cache_key = f"pr:{owner}:{repo}:{pr_number}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
        data = await self._request("GET", url)
        if data is None:
            return None

        pr_info = {
            "number": data.get("number", 0),
            "title": data.get("title", ""),
            "state": data.get("state", ""),
            "user_login": data.get("user", {}).get("login", ""),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "merged_at": data.get("merged_at"),
            "merged": data.get("merged", False),
            "additions": data.get("additions", 0),
            "deletions": data.get("deletions", 0),
            "review_comments": data.get("review_comments", 0),
            "url": data.get("html_url", ""),
            "base_ref": data.get("base", {}).get("ref", ""),
            "head_ref": data.get("head", {}).get("ref", "")
        }

        self._set_cache(cache_key, pr_info)
        return pr_info

    async def validate_pr_number(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """验证PR编号是否存在，并返回PR状态信息"""
        pr = await self.get_pull_request(owner, repo, pr_number)
        
        if not pr:
            return {
                "valid": False,
                "exists": False,
                "message": f"PR #{pr_number} 不存在"
            }
        
        is_merged = pr.get("merged", False) or (pr.get("merged_at") is not None)
        
        return {
            "valid": True,
            "exists": True,
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "is_merged": is_merged,
            "merged_at": pr["merged_at"],
            "user_login": pr["user_login"],
            "url": pr["url"],
            "message": f"PR #{pr_number} 验证成功"
        }

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """获取单个Issue的详细信息"""
        cache_key = f"issue:{owner}:{repo}:{issue_number}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}"
        data = await self._request("GET", url)
        if data is None:
            return None

        issue_info = {
            "number": data.get("number", 0),
            "title": data.get("title", ""),
            "state": data.get("state", ""),
            "user_login": data.get("user", {}).get("login", ""),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "closed_at": data.get("closed_at"),
            "closed_by": data.get("closed_by", {}).get("login", "") if data.get("closed_by") else None,
            "url": data.get("html_url", ""),
            "body": data.get("body", "")
        }

        self._set_cache(cache_key, issue_info)
        return issue_info

    async def close_issue(self, owner: str, repo: str, issue_number: int, comment: str = "") -> bool:
        """关闭Issue并可选添加评论"""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}"
        
        # 先添加评论（如果有）
        if comment:
            comment_url = f"{url}/comments"
            await self._request("POST", comment_url, json={"body": comment})
        
        # 关闭Issue
        data = await self._request("PATCH", url, json={"state": "closed"})
        return data is not None

    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        cache_key = f"languages:{owner}:{repo}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
        data = await self._request("GET", url)
        if data is None:
            return {}

        self._set_cache(cache_key, data)
        return data

    async def get_repo_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        cache_key = f"stats:{owner}:{repo}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        data = await self._request("GET", url)
        if data is None:
            return {}

        result = {
            "total_lines": sum(data.get("size", 0) for _ in [1]),
            "file_count": 0,
            "open_issues": data.get("open_issues_count", 0),
            "forks": data.get("forks_count", 0),
            "stars": data.get("stargazers_count", 0)
        }

        self._set_cache(cache_key, result)
        return result

    async def get_full_data(self, owner: str, repo: str) -> Dict[str, Any]:
        branches_task = self.get_branches(owner, repo)
        commits_task = self.get_commits(owner, repo)
        prs_task = self.get_pull_requests(owner, repo)
        languages_task = self.get_languages(owner, repo)
        stats_task = self.get_repo_stats(owner, repo)

        branches, commits, prs, languages, stats = await asyncio.gather(
            branches_task, commits_task, prs_task, languages_task, stats_task
        )

        total_lines = sum(languages.values()) if languages else 0

        pr_analysis = {
            "total_prs": len(prs),
            "merged_prs": len([pr for pr in prs if pr.get("merged_at")]),
            "open_prs": len([pr for pr in prs if pr.get("state") == "open"]),
            "closed_prs": len([pr for pr in prs if pr.get("state") == "closed" and not pr.get("merged_at")]),
            "total_additions": sum(pr.get("additions", 0) for pr in prs),
            "total_deletions": sum(pr.get("deletions", 0) for pr in prs),
        }

        if pr_analysis["total_prs"] > 0:
            pr_analysis["merge_rate"] = round(pr_analysis["merged_prs"] / pr_analysis["total_prs"] * 100, 1)
        else:
            pr_analysis["merge_rate"] = 0.0

        total_pr_size = sum(pr.get("additions", 0) + pr.get("deletions", 0) for pr in prs)
        if pr_analysis["total_prs"] > 0:
            pr_analysis["avg_pr_size"] = round(total_pr_size / pr_analysis["total_prs"], 1)
        else:
            pr_analysis["avg_pr_size"] = 0.0

        return {
            "branches": branches,
            "commits": commits,
            "pull_requests": prs,
            "languages": languages,
            "total_lines": total_lines,
            "pr_analysis": pr_analysis,
            "stats": stats
        }

    def clear_cache(self):
        self._cache.clear()


github_service = GitHubService()
